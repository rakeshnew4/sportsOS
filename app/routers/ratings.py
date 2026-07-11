import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.db.orm import Booking, BookingParticipant, Rating

router = APIRouter(prefix="/ratings", tags=["ratings"])


class RatingCreate(BaseModel):
    rated_uid: str
    booking_id: str
    rating: int  # 1-5 stars
    comment: str = ""


class RatingResponse(BaseModel):
    rating_id: str
    from_uid: str
    to_uid: str
    booking_id: str
    rating: int
    comment: str
    created_at: str


class PlayerRatingsStats(BaseModel):
    uid: str
    avg_rating: float
    total_ratings: int
    rating_distribution: dict[int, int]


class VenueRatingsStats(BaseModel):
    tenant_id: str
    avg_rating: float
    total_ratings: int


@router.post("/", status_code=201)
def create_rating(
    req: RatingCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RatingResponse:
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be 1-5")
    if user.uid == req.rated_uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate yourself")

    booking = db.query(Booking).filter(Booking.booking_id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    participants = {booking.created_by}
    for p in db.query(BookingParticipant).filter(BookingParticipant.booking_id == req.booking_id).all():
        participants.add(p.uid)
    if user.uid not in participants or req.rated_uid not in participants:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only participants of a match can rate each other")

    existing = db.query(Rating).filter(
        Rating.from_uid == user.uid, Rating.to_uid == req.rated_uid, Rating.booking_id == req.booking_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already rated this player for this booking")

    now = datetime.now(timezone.utc)
    r = Rating(
        rating_id=uuid.uuid4().hex,
        from_uid=user.uid,
        to_uid=req.rated_uid,
        booking_id=req.booking_id,
        tenant_id=booking.tenant_id,
        rating=req.rating,
        comment=req.comment,
        created_at=now,
    )
    db.add(r)
    db.commit()
    return RatingResponse(
        rating_id=r.rating_id, from_uid=user.uid, to_uid=req.rated_uid,
        booking_id=req.booking_id, rating=req.rating, comment=req.comment,
        created_at=now.isoformat(),
    )


@router.get("/players/{uid}/stats")
def get_player_ratings_stats(uid: str, db: Session = Depends(get_db)) -> PlayerRatingsStats:
    ratings = db.query(Rating).filter(Rating.to_uid == uid).all()
    if not ratings:
        return PlayerRatingsStats(uid=uid, avg_rating=0.0, total_ratings=0, rating_distribution={})
    values = [r.rating for r in ratings]
    avg = sum(values) / len(values)
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for v in values:
        dist[v] = dist.get(v, 0) + 1
    return PlayerRatingsStats(uid=uid, avg_rating=round(avg, 2), total_ratings=len(values), rating_distribution=dist)


@router.get("/venues/{tenant_id}/stats")
def get_venue_ratings_stats(tenant_id: str, db: Session = Depends(get_db)) -> VenueRatingsStats:
    ratings = db.query(Rating).filter(Rating.tenant_id == tenant_id).all()
    if not ratings:
        return VenueRatingsStats(tenant_id=tenant_id, avg_rating=0.0, total_ratings=0)
    avg = sum(r.rating for r in ratings) / len(ratings)
    return VenueRatingsStats(tenant_id=tenant_id, avg_rating=round(avg, 2), total_ratings=len(ratings))


@router.get("/players/{uid}/reviews")
def list_player_reviews(uid: str, limit: int = 10, db: Session = Depends(get_db)) -> list[RatingResponse]:
    ratings = (
        db.query(Rating)
        .filter(Rating.to_uid == uid)
        .order_by(Rating.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        RatingResponse(
            rating_id=r.rating_id, from_uid=r.from_uid, to_uid=r.to_uid,
            booking_id=r.booking_id, rating=r.rating, comment=r.comment or "",
            created_at=r.created_at.isoformat(),
        )
        for r in ratings
    ]



