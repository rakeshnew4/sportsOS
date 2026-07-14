"""Seed sample data into Postgres and confirm it mirrors through to Firestore.

Exercises the real service layer (venue -> court -> booking -> confirm ->
open to community -> join match), which is what triggers
app.services.realtime_service to write the "matches"/"slots" mirror docs.
Then reads those docs straight back from Firestore to validate the pipeline
end to end.

Run inside the backend container, where DATABASE_URL and the Firebase
service account are configured:

    docker compose exec backend python scripts/seed_firestore.py
"""

from datetime import date, timedelta

from app.core.database import SessionLocal
from app.core.firebase import get_firestore_client
from app.db.orm import Court, Tenant, User
from app.models.booking import BookingCreateRequest
from app.models.court import CourtCreateRequest
from app.models.match import OpenToCommunityRequest
from app.models.user import OwnerRegisterRequest, PlayerRegisterRequest
from app.models.venue import GeoPoint, VenueCreateRequest
from app.services import booking_service, court_service, match_service, user_service, venue_service, wallet_service

OWNER_UID = "seed_owner_raj"
CAPTAIN_UID = "seed_player_kabir"
JOINER_UID = "seed_player_meera"
VENUE_NAME = "Seed Sports Arena"
WALLET_TOPUP = 2000.0


def get_or_create_user(db, uid: str, name: str, phone: str, is_player: bool) -> None:
    if db.query(User).filter(User.uid == uid).first():
        return
    if is_player:
        user_service.register_player(db, PlayerRegisterRequest(display_name=name, phone=phone), uid=uid)
    else:
        user_service.register_owner(db, OwnerRegisterRequest(display_name=name, phone=phone), uid=uid)


def get_or_create_venue(db, uid: str) -> str:
    tenant = db.query(Tenant).filter(Tenant.name == VENUE_NAME).first()
    if tenant:
        return tenant.tenant_id
    venue = venue_service.create_venue(
        db,
        uid,
        VenueCreateRequest(
            name=VENUE_NAME,
            city="Hyderabad",
            geo=GeoPoint(lat=17.385, lng=78.4867),
            sports=["badminton"],
            description="Seed data for Firestore mirror validation",
        ),
    )
    return venue.tenant_id


def get_or_create_court(db, tenant_id: str) -> str:
    court = db.query(Court).filter(Court.tenant_id == tenant_id).first()
    if court:
        return court.court_id
    court_resp = court_service.create_court(
        db,
        tenant_id,
        CourtCreateRequest(name="Court 1", sport="badminton", hourly_price=500.0, open_time="06:00", close_time="23:00"),
    )
    return court_resp.court_id


def main() -> None:
    db = SessionLocal()
    try:
        print("Seeding Postgres...")
        get_or_create_user(db, OWNER_UID, "Raj Seed", "+91-9000000001", is_player=False)
        get_or_create_user(db, CAPTAIN_UID, "Kabir Seed", "+91-9000000002", is_player=True)
        get_or_create_user(db, JOINER_UID, "Meera Seed", "+91-9000000003", is_player=True)

        for uid in (CAPTAIN_UID, JOINER_UID):
            wallet_service.credit_wallet(db, uid, WALLET_TOPUP, "Seed wallet top-up")
        db.commit()

        tenant_id = get_or_create_venue(db, OWNER_UID)
        court_id = get_or_create_court(db, tenant_id)

        seed_date = (date.today() + timedelta(days=1)).isoformat()
        existing = (
            db.query(booking_service.Booking)
            .filter(
                booking_service.Booking.tenant_id == tenant_id,
                booking_service.Booking.court_id == court_id,
                booking_service.Booking.date == seed_date,
                booking_service.Booking.start_time == "18:00",
            )
            .first()
        )
        if existing:
            booking = booking_service.booking_to_response(existing)
            print(f"Reusing existing booking {booking.booking_id}")
        else:
            booking = booking_service.create_booking(
                db,
                tenant_id,
                CAPTAIN_UID,
                BookingCreateRequest(court_id=court_id, date=seed_date, start_time="18:00", end_time="19:00", team_name="Seed Team"),
            )
            booking_service.confirm_booking(db, tenant_id, booking.booking_id)
            booking = match_service.open_to_community(db, tenant_id, booking.booking_id, CAPTAIN_UID, OpenToCommunityRequest(slots_open=3))
            if booking.slots_open > 0:
                booking = match_service.join_match(db, tenant_id, booking.booking_id, JOINER_UID)
            print(f"Created booking {booking.booking_id}")

        print(f"tenant_id={tenant_id} court_id={court_id} date={seed_date}")

        client = get_firestore_client()
        if client is None:
            print("\nFirestore client unavailable (no credentials configured) — cannot validate.")
            return

        match_doc = client.collection("matches").document(booking.booking_id).get()
        slots_doc_id = f"{tenant_id}_{court_id}_{seed_date}"
        slots_doc = client.collection("slots").document(slots_doc_id).get()

        print("\nValidation against Firestore:")
        print(f"  matches/{booking.booking_id} exists={match_doc.exists}")
        if match_doc.exists:
            print(f"    {match_doc.to_dict()}")
        print(f"  slots/{slots_doc_id} exists={slots_doc.exists}")
        if slots_doc.exists:
            print(f"    {slots_doc.to_dict()}")

        assert match_doc.exists, "match document did not mirror to Firestore"
        assert slots_doc.exists, "slots document did not mirror to Firestore"
        print("\nSeed + Firestore validation succeeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
