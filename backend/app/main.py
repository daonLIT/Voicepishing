from fastapi import FastAPI
from backend.app.routers import agents, simulate, education, metrics

app = FastAPI(title="Voice Phishing Simulation")
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(simulate.router, prefix="/simulate", tags=["simulate"])
app.include_router(education.router, prefix="/education", tags=["education"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
