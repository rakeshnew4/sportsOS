from fastapi import FastAPI

from app.routers import auth, bookings, courts, matches, matchmaking, venues, wallet

app = FastAPI(title="SportsOS API")

app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(courts.router)
app.include_router(bookings.router)
app.include_router(matches.router)
app.include_router(matchmaking.router)
app.include_router(wallet.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
