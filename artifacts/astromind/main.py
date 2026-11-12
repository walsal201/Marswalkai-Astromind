"""AstroMind backend: FastAPI + CrewAI. Works instantly in demo mode; set an LLM key (server-side) for live agents."""
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

load_dotenv()
import crew_agents  # noqa: E402
import demo_data    # noqa: E402

app = FastAPI(title="AstroMind API", version="2.0")
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

RATE = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
_hits: dict = defaultdict(deque)


def rate_limit(request: Request):
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "x")).split(",")[0].strip()
    now = time.time(); q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE:
        raise HTTPException(429, "Too many requests, please wait a minute.")
    q.append(now)


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class AstroReq(BaseModel):
    destination: str = Field("Mars", max_length=60)
    mission_type: str = Field("Crewed Mission", max_length=60)
    launch_year: int = Field(2028, ge=2026, le=2060)
    crew_size: int = Field(4, ge=0, le=12)
    duration_days: int = Field(900, ge=1, le=5000)
    message: Optional[str] = Field(None, max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=20)


class MarsReq(BaseModel):
    site: str = Field("Jezero Crater", max_length=80)
    lat: float = 18.4
    lon: float = 77.7
    elevation_m: float = -2900
    temp_c: float = -63
    wind_ms: float = Field(12, ge=0, le=100)
    dust_tau: float = Field(0.5, ge=0, le=10)
    duration_hours: float = Field(6, ge=1, le=12)
    crew: str = Field("2-person EVA team", max_length=60)
    objective: str = Field("Geological Survey", max_length=80)
    route_km: float = Field(3.2, ge=0, le=30)
    waypoints: int = Field(0, ge=0, le=60)
    hazards: int = Field(0, ge=0, le=60)
    science_targets: int = Field(0, ge=0, le=60)
    message: Optional[str] = Field(None, max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=20)


ASTRO_ACTIONS = set(demo_data.ASTRO)
MARS_ACTIONS = set(demo_data.MARS)
API_PREFIX = "/astro-api"


def respond(domain: str, action: str, req: BaseModel):
    p = req.model_dump()
    if action == "chat" and not (p.get("message") or "").strip():
        raise HTTPException(422, "message is required for chat")
    if crew_agents.live_available():
        try:
            return dict(action=action, mode="live", engine="CrewAI", text=crew_agents.generate(domain, action, p))
        except Exception as e:  # fall back so the UI never breaks
            return dict(action=action, mode="demo", engine="fallback",
                        text=demo_data.generate(domain, action, p),
                        note=f"Live agents unavailable ({type(e).__name__}); showing built-in demo output.")
    return dict(action=action, mode="demo", engine="built-in", text=demo_data.generate(domain, action, p))


@app.get(f"{API_PREFIX}/health")
def health():
    live = crew_agents.live_available()
    return dict(status="ok", mode="live" if live else "demo", engine="CrewAI" if live else "built-in", **crew_agents.engine_info())


@app.post(f"{API_PREFIX}/astromind/metrics")
def astro_metrics(req: AstroReq):
    return demo_data.metrics(req.destination)


@app.post(f"{API_PREFIX}/astromind/{{action}}")
def astro_action(action: str, req: AstroReq, request: Request):
    if action not in ASTRO_ACTIONS:
        raise HTTPException(404, "Unknown action")
    rate_limit(request)
    return respond("astromind", action, req)


@app.post(f"{API_PREFIX}/marswalk/{{action}}")
def mars_action(action: str, req: MarsReq, request: Request):
    if action not in MARS_ACTIONS:
        raise HTTPException(404, "Unknown action")
    rate_limit(request)
    return respond("marswalk", action, req)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
