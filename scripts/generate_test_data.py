#!/usr/bin/env python3
"""
Generate dummy test data for SportsOS.
Run: python scripts/generate_test_data.py
"""

import sys
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.db import get_db
from app.models.user import PlayerRegisterRequest, OwnerRegisterRequest
from app.models.venue import VenueCreateRequest, GeoPoint
from app.models.court import CourtCreateRequest
from app.models.booking import BookingCreateRequest
from app.services import user_service, venue_service, court_service, booking_service, team_service


def generate_dummy_players(db):
    """Create dummy player accounts with wallets."""
    print("📝 Creating dummy players with wallets...")

    players = [
        {"uid": "player_rakesh", "name": "Rakesh Kumar", "phone": "+91-9876543210"},
        {"uid": "player_priya", "name": "Priya Singh", "phone": "+91-9876543211"},
        {"uid": "player_amit", "name": "Amit Patel", "phone": "+91-9876543212"},
        {"uid": "player_neha", "name": "Neha Sharma", "phone": "+91-9876543213"},
        {"uid": "player_vikram", "name": "Vikram Reddy", "phone": "+91-9876543214"},
        {"uid": "player_isha", "name": "Isha Gupta", "phone": "+91-9876543215"},
        {"uid": "player_arun", "name": "Arun Kumar", "phone": "+91-9876543216"},
        {"uid": "player_deepak", "name": "Deepak Verma", "phone": "+91-9876543217"},
    ]

    INITIAL_WALLET = 5000.0
    CURRENCY = "INR"

    for player in players:
        try:
            user_service.register_player(
                db,
                PlayerRegisterRequest(display_name=player["name"], phone=player["phone"]),
                uid=player["uid"],
            )
            # Create wallet with initial balance
            wallet_ref = db.collection("players").document(player["uid"]).collection("wallet").document("wallet")
            wallet_ref.set({
                "balance": INITIAL_WALLET,
                "currency": CURRENCY,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            print(f"  ✅ {player['name']}")
            print(f"     💰 Wallet: {INITIAL_WALLET} {CURRENCY} (1 credit = 1 rupee)")
        except Exception as e:
            print(f"  ⚠️  {player['name']}: {str(e)[:50]}")


def generate_dummy_owners(db):
    """Create dummy venue owner accounts."""
    print("\n🏢 Creating dummy venue owners...")

    owners = [
        {"uid": "owner_raj", "name": "Raj Menon", "phone": "+91-8765432100"},
        {"uid": "owner_preet", "name": "Preet Kaur", "phone": "+91-8765432101"},
    ]

    for owner in owners:
        try:
            user_service.register_owner(
                db,
                OwnerRegisterRequest(display_name=owner["name"], phone=owner["phone"]),
                uid=owner["uid"],
            )
            print(f"  ✅ {owner['name']}")
        except Exception as e:
            print(f"  ⚠️  {owner['name']}: {str(e)[:50]}")


def generate_dummy_venues(db):
    """Create dummy venues with courts."""
    print("\n🏟️  Creating dummy venues and courts...")

    venues_data = [
        {
            "owner": "owner_raj",
            "name": "Champions Sports Arena",
            "city": "Hyderabad",
            "lat": 17.3850,
            "lng": 78.4867,
            "sports": ["badminton", "tennis", "table_tennis"],
            "courts": [
                {"name": "Court A", "sport": "badminton", "price": 600.0},
                {"name": "Court B", "sport": "badminton", "price": 600.0},
                {"name": "Court C", "sport": "tennis", "price": 800.0},
                {"name": "Table Tennis Arena", "sport": "table_tennis", "price": 400.0},
            ],
        },
        {
            "owner": "owner_preet",
            "name": "Victory Sports Complex",
            "city": "Bangalore",
            "lat": 12.9716,
            "lng": 77.5946,
            "sports": ["badminton", "cricket", "volleyball"],
            "courts": [
                {"name": "Badminton Court 1", "sport": "badminton", "price": 650.0},
                {"name": "Badminton Court 2", "sport": "badminton", "price": 650.0},
                {"name": "Cricket Net", "sport": "cricket", "price": 1200.0},
                {"name": "Volleyball Court", "sport": "volleyball", "price": 500.0},
            ],
        },
        {
            "owner": "owner_raj",
            "name": "Racquet Masters Club",
            "city": "Hyderabad",
            "lat": 17.3900,
            "lng": 78.4800,
            "sports": ["tennis", "table_tennis", "badminton"],
            "courts": [
                {"name": "Hard Court 1", "sport": "tennis", "price": 900.0},
                {"name": "Hard Court 2", "sport": "tennis", "price": 900.0},
                {"name": "TT Table 1", "sport": "table_tennis", "price": 350.0},
                {"name": "TT Table 2", "sport": "table_tennis", "price": 350.0},
            ],
        },
    ]

    created_venues = {}

    for venue_data in venues_data:
        try:
            venue = venue_service.create_venue(
                db,
                venue_data["owner"],
                VenueCreateRequest(
                    name=venue_data["name"],
                    city=venue_data["city"],
                    geo=GeoPoint(lat=venue_data["lat"], lng=venue_data["lng"]),
                    sports=venue_data["sports"],
                ),
            )
            created_venues[venue.tenant_id] = venue_data
            print(f"\n  ✅ {venue_data['name']} (ID: {venue.tenant_id})")

            # Create courts
            for court_data in venue_data["courts"]:
                try:
                    court = court_service.create_court(
                        db,
                        venue.tenant_id,
                        CourtCreateRequest(
                            name=court_data["name"],
                            sport=court_data["sport"],
                            hourly_price=court_data["price"],
                            open_time="06:00",
                            close_time="23:00",
                            dynamic_pricing_enabled=False,
                        ),
                    )
                    print(f"     • {court_data['name']} ({court_data['sport']}) — ₹{court_data['price']}/hr")
                except Exception as e:
                    print(f"     ⚠️  {court_data['name']}: {str(e)[:40]}")
        except Exception as e:
            print(f"  ⚠️  {venue_data['name']}: {str(e)[:50]}")

    return created_venues


def generate_dummy_bookings(db, created_venues):
    """Create some dummy bookings and open matches."""
    print("\n📅 Creating dummy bookings...")

    if not created_venues:
        print("  ⚠️  No venues created, skipping bookings")
        return

    # Get first venue
    venue_id = list(created_venues.keys())[0]
    venue_data = created_venues[venue_id]

    # Get first court (badminton)
    badminton_courts = [c for c in venue_data["courts"] if c["sport"] == "badminton"]
    if not badminton_courts:
        print("  ⚠️  No badminton courts, skipping")
        return

    court_data = badminton_courts[0]
    courts = court_service.list_courts(db, venue_id)
    court = next((c for c in courts if c.name == court_data["name"]), None)

    if not court:
        print("  ⚠️  Court not found")
        return

    # Create bookings for different times
    booking_times = [
        ("06:00", "07:00", "player_rakesh"),
        ("07:30", "08:30", "player_priya"),
        ("18:00", "19:00", "player_amit"),
        ("19:30", "20:30", "player_neha"),
    ]

    today = datetime.now().date()

    for start, end, player_uid in booking_times:
        try:
            booking = booking_service.create_booking(
                db,
                venue_id,
                player_uid,
                BookingCreateRequest(
                    court_id=court.court_id,
                    date=today.isoformat(),
                    start_time=start,
                    end_time=end,
                    team_name=None,  # Will be auto-generated
                ),
            )
            print(f"  ✅ {player_uid} booked {start}-{end} — Team: {booking.team_name}")
        except Exception as e:
            print(f"  ⚠️  Booking {start}-{end}: {str(e)[:50]}")


def generate_dummy_open_matches(db, created_venues):
    """Create some open matches by opening bookings to community."""
    print("\n🎯 Opening matches for community...")

    from app.services import match_service
    from app.models.match import OpenToCommunityRequest

    if not created_venues:
        print("  ⚠️  No venues, skipping open matches")
        return

    try:
        # Get player's bookings
        player_bookings = booking_service.list_my_bookings(db, "player_rakesh")
        confirmed = [b for b in player_bookings if b.status == "confirmed" and not b.is_joinable]

        if confirmed:
            booking = confirmed[0]
            result = match_service.open_to_community(
                db,
                booking.tenant_id,
                booking.booking_id,
                "player_rakesh",
                OpenToCommunityRequest(slots_open=2),
            )
            print(f"  ✅ Opened {booking.sport} match — {booking.date} {booking.start_time}-{booking.end_time}")
            print(f"     🎽 Team: {booking.team_name}")
            print(f"     📍 Venue: {booking.tenant_name}")
            print(f"     👥 Slots available: {result.slots_open}")
        else:
            print("  ⚠️  No bookings to open")
    except Exception as e:
        print(f"  ⚠️  Error opening match: {str(e)[:50]}")


def print_summary(db):
    """Print summary of created data."""
    print("\n" + "="*60)
    print("📊 TEST DATA SUMMARY")
    print("="*60)

    try:
        from app.core.db import FieldFilter
        players = list(db.collection("users").where(filter=FieldFilter("roles.player", "==", True)).stream())
        print(f"\n👥 Players: {len(players)}")
        for doc in players[:8]:
            data = doc.to_dict()
            player_id = doc.id
            try:
                wallet_doc = db.collection("players").document(player_id).collection("wallet").document("wallet").get()
                if wallet_doc.exists:
                    wallet_data = wallet_doc.to_dict()
                    balance = wallet_data.get("balance", 0)
                    currency = wallet_data.get("currency", "INR")
                    print(f"   • {data.get('display_name', player_id)} ({player_id})")
                    print(f"     💰 {balance} {currency} (1 credit = 1 rupee)")
                else:
                    print(f"   • {data.get('display_name', player_id)} ({player_id}) - No wallet")
            except:
                print(f"   • {data.get('display_name', player_id)} ({player_id})")
    except Exception as e:
        print(f"Error fetching players: {e}")

    try:
        from app.core.db import FieldFilter
        owners = list(db.collection("users").where(filter=FieldFilter("roles.owner", "==", True)).stream())
        print(f"\n🏢 Owners: {len(owners)}")
        for doc in owners:
            data = doc.to_dict()
            print(f"   • {data.get('display_name', doc.id)}")
    except Exception as e:
        print(f"Error fetching owners: {e}")

    try:
        venues = list(db.collection("tenants").stream())
        print(f"\n🏟️  Venues: {len(venues)}")
        for doc in venues[:3]:
            data = doc.to_dict()
            print(f"   • {data.get('name', doc.id)}")
        if len(venues) > 3:
            print(f"   ... and {len(venues) - 3} more")
    except:
        pass

    print("\n✅ Test data generation complete!")
    print("\n🎮 WALLET SYSTEM")
    print("   • Initial balance: 5000 credits per player")
    print("   • Currency: INR (1 credit = 1 rupee)")
    print("   • When joining matches: wallet auto-deducts your share")
    print("   • When hosting matches: receive payment from joiners")
    print("\n🚀 Login credentials:")
    print("   Streamlit tab: Sign up")
    print("   Role: Player")
    print("   UID: player_rakesh (or any player_*)")
    print("   Name: Rakesh Kumar")
    print("   Phone: (any value)")
    print("\n💡 Try these player IDs:")
    print("   player_rakesh, player_priya, player_amit, player_neha,")
    print("   player_vikram, player_isha, player_arun, player_deepak")
    print("="*60)


def main():
    """Generate all test data."""
    print("🎮 SportsOS Test Data Generator")
    print("="*60)

    try:
        db = get_db()

        # Generate data
        generate_dummy_players(db)
        generate_dummy_owners(db)
        created_venues = generate_dummy_venues(db)
        generate_dummy_bookings(db, created_venues)
        generate_dummy_open_matches(db, created_venues)

        # Print summary
        print_summary(db)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
