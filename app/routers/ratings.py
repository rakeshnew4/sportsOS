from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.db import Client, FieldFilter, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.booking import BookingResponse

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
    rating_distribution: dict[int, int]  # {1: count, 2: count, ...}


@router.post("/", status_code=201)
def create_rating(
    req: RatingCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> RatingResponse:
    """Rate another player after a match. Only players in the same booking can rate each other."""
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be 1-5")

    # Extract tenant_id from booking_id (format: venue_id/booking_id or just booking_id)
    # For now, search across all tenants for the booking
    booking_found = None
    booking_ref = None
    tenant_id = None

    for tenant_doc in db.collection("tenants").stream():
        tenant_id = tenant_doc.id
        candidate_ref = db.collection("tenants").document(tenant_id).collection("bookings").document(req.booking_id)
        booking_doc = candidate_ref.get()
        if booking_doc.exists:
            booking_ref = candidate_ref
            booking_found = booking_doc.to_dict()
            break

    if not booking_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Check that rating user and rated user were both in the booking. Participants
    # live in a subcollection (doc id = uid); the captain is only on created_by.
    participants = {booking_found.get("created_by")}
    participants.update(p.id for p in booking_ref.collection("participants").stream())
    if user.uid not in participants or req.rated_uid not in participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only participants of a match can rate each other",
        )

    if user.uid == req.rated_uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate yourself")

    # Check no duplicate rating from this user to that user for this booking
    existing = (
        db.collection("ratings")
        .where(filter=FieldFilter("from_uid", "==", user.uid))
        .where(filter=FieldFilter("to_uid", "==", req.rated_uid))
        .where(filter=FieldFilter("booking_id", "==", req.booking_id))
        .stream()
    )
    if list(existing):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already rated this player for this booking",
        )

    # Create rating
    rating_id = db.collection("ratings").document().id
    rating_doc = {
        "from_uid": user.uid,
        "to_uid": req.rated_uid,
        "booking_id": req.booking_id,
        "tenant_id": tenant_id,
        "rating": req.rating,
        "comment": req.comment,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    db.collection("ratings").document(rating_id).set(rating_doc)

    return RatingResponse(
        rating_id=rating_id,
        from_uid=user.uid,
        to_uid=req.rated_uid,
        booking_id=req.booking_id,
        rating=req.rating,
        comment=req.comment,
        created_at=rating_doc["created_at"],
    )


@router.get("/players/{uid}/stats")
def get_player_ratings_stats(
    uid: str,
    db: Client = Depends(get_db),
) -> PlayerRatingsStats:
    """Get aggregated ratings for a player (avg, count, distribution)."""
    ratings = db.collection("ratings").where(filter=FieldFilter("to_uid", "==", uid)).stream()

    ratings_list = [doc.to_dict() for doc in ratings]

    if not ratings_list:
        return PlayerRatingsStats(uid=uid, avg_rating=0.0, total_ratings=0, rating_distribution={})

    rating_values = [r["rating"] for r in ratings_list]
    avg_rating = sum(rating_values) / len(rating_values)

    # Build distribution
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating in rating_values:
        distribution[rating] += 1

    return PlayerRatingsStats(
        uid=uid,
        avg_rating=round(avg_rating, 2),
        total_ratings=len(ratings_list),
        rating_distribution=distribution,
    )


@router.get("/players/{uid}/reviews")
def list_player_reviews(
    uid: str,
    limit: int = 10,
    db: Client = Depends(get_db),
) -> list[RatingResponse]:
    """Get recent reviews for a player."""
    ratings = (
        db.collection("ratings")
        .where(filter=FieldFilter("to_uid", "==", uid))
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .stream()
    )

    results = []
    for doc in ratings:
        data = doc.to_dict()
        results.append(
            RatingResponse(
                rating_id=doc.id,
                from_uid=data["from_uid"],
                to_uid=data["to_uid"],
                booking_id=data["booking_id"],
                rating=data["rating"],
                comment=data.get("comment", ""),
                created_at=data["created_at"],
            )
        )

    return results
