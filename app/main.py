from fastapi import FastAPI

from app.routers import analytics, auth, bookings, courts, kpis, matches, matchmaking, notifications, players, ratings, teams, rewards, venues, wallet, venue_staff, waitlist

app = FastAPI(title="SportsOS API")

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
