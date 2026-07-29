from fastapi import FastAPI
from masteries.api.router import router

app = FastAPI(
    title="PACE Backend",
    version="1.0.0",
    description="Backend API for the PACE Project",
)

app.include_router(router)
