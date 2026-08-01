from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from masteries.api.router import router

app = FastAPI(
    title="PACE Backend",
    version="1.0.0",
    description="Backend API for the PACE Project",
)

# Allow the Vite dev-server and any localhost origin to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
