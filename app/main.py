from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import create_all_tables
from app.routers import analytics, auth, bookings, courts, invites, kpis, matches, matchmaking, notifications, players, ratings, realtime, teams, rewards, venues, wallet, venue_staff, waitlist


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_all_tables()
    yield


app = FastAPI(title="SportsOS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(venue_staff.router)
app.include_router(courts.router)
app.include_router(bookings.router)
app.include_router(matches.router)
app.include_router(matchmaking.router)
app.include_router(notifications.router)
app.include_router(waitlist.router)
app.include_router(players.router)
app.include_router(ratings.router)
app.include_router(analytics.router)
app.include_router(wallet.router)
app.include_router(kpis.router)
app.include_router(teams.router)
app.include_router(rewards.router)
app.include_router(invites.router)
app.include_router(realtime.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
