from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends

from app.cache.sqlite_cache import SqliteCache
from app.cache.memory_cache import MemoryCache
from app.config import settings
from app.dependencies import get_riot_api, get_memory_cache
from app.routers import summoner, matches, analysis
from app.services.riot_api import RiotAPIClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.riot_api = RiotAPIClient()
    app.state.sqlite_cache = SqliteCache()
    await app.state.sqlite_cache.init()
    yield
    await app.state.riot_api.close()
    await app.state.sqlite_cache.close()


app = FastAPI(title="LoL Match Analyzer", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summoner.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/ddragon-version")
async def ddragon_version(
    riot_api: RiotAPIClient = Depends(get_riot_api),
    cache: MemoryCache = Depends(get_memory_cache),
):
    cached = cache.get("ddragon_version")
    if cached:
        return cached

    version = await riot_api.get_ddragon_version()
    result = {"version": version}
    cache.set("ddragon_version", result, ttl_seconds=3600)
    return result
