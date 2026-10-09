"""PACE API entrypoint: one worker on free hosting; no privileged executor."""
from __future__ import annotations
import logging
import time
from collections import deque,defaultdict
from contextlib import asynccontextmanager
from threading import Lock
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import get_settings
from masteries.api.router import router
from masteries.services.database import init_db
from backend.request_limits import RequestBodyLimit

settings=get_settings()
logging.basicConfig(level=settings.log_level, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger('pace.api')

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app=FastAPI(title='PACE API',version='2.0.0',lifespan=lifespan)
app.add_middleware(RequestBodyLimit)
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=False,allow_methods=['GET','POST','DELETE','OPTIONS'],allow_headers=['Content-Type','X-PACE-Session','X-PACE-Desktop-Key'])
_hits:dict[str,deque[float]]=defaultdict(deque)
_lock=Lock()

@app.middleware('http')
async def security_middleware(request:Request,call_next):
    if request.method!='OPTIONS' and request.url.path not in {'/health','/'}:
        peer=request.client.host if request.client else 'unknown'
        now=time.monotonic()
        with _lock:
            if len(_hits) > 4096:
                stale = [key for key, values in _hits.items() if not values or values[-1] < now - 60]
                for key in stale:
                    del _hits[key]
            q=_hits[peer]
            while q and q[0] < now-60:
                q.popleft()
            if len(q)>=settings.rate_limit_per_minute:
                response=JSONResponse({'detail':'Rate limit exceeded'},status_code=429,headers={'Retry-After':'60'})
            else:
                q.append(now)
                response=None
        if response is None:
            response=await call_next(request)
    else:
        response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Cache-Control']='no-store'
    return response

@app.exception_handler(Exception)
async def unknown_error(request:Request,exc:Exception):
    logger.error('Unhandled API failure on %s',request.url.path,exc_info=True)
    return JSONResponse({'detail':'Internal server error'},status_code=500)

app.include_router(router)
