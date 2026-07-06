"""Local demo UI for SportsOS — talks directly to app/services/*.py (no HTTP,
no Firebase Auth) against the local JSON-backed fake Firestore, so the full
demo flow can be exercised with dummy data before pointing at real Firestore.

Run with: streamlit run streamlit_app.py
"""

from datetime import date, time

import streamlit as st
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.db import get_db
from app.models.booking import BookingCreateRequest
from app.models.court import CourtCreateRequest
from app.models.match import OpenToCommunityRequest
from app.models.matchmaking import MatchRequestCreate
from app.models.user import OwnerRegisterRequest, PlayerRegisterRequest
from app.models.venue import GeoPoint, VenueCreateRequest
from app.services import (
    booking_service,
    court_service,
    match_service,
    matchmaking_service,
    user_service,
    venue_service,
    wallet_service,
)

st.set_page_config(page_title="SportsOS demo", layout="wide")

settings = get_settings()
if settings.data_backend != "local_json":
    st.error(
        "DATA_BACKEND is set to 'firestore'. This demo UI is for local dummy-data "
        "testing only — set DATA_BACKEND=local_json in .env before using it."
    )
    st.stop()

db = get_db()


def run(fn, *args, **kwargs):
    """Call a service function, surfacing HTTPException details as a Streamlit error."""
    try:
        return fn(*args, **kwargs)
    except HTTPException as exc:
        st.error(f"{exc.status_code}: {exc.detail}")
        return None


def list_users() -> list[dict]:
    return [{"uid": doc.id, **doc.to_dict()} for doc in db.collection("users").stream()]


def list_venues() -> list[dict]:
    return [{"tenant_id": doc.id, **doc.to_dict()} for doc in db.collection("tenants").stream()]


# --- Sidebar: identity + reset ---
st.sidebar.title("SportsOS demo")

users = list_users()
user_labels = {u["uid"]: f"{u['uid']} — {u.get('display_name', '?')}" for u in users}
acting_as = st.sidebar.selectbox(
    "Acting as",
    options=list(user_labels.keys()) or ["(no users registered yet)"],
    format_func=lambda uid: user_labels.get(uid, uid),
)

if st.sidebar.button("Reset demo data", type="secondary"):
    db.reset()
    st.sidebar.success("Local data cleared.")
    st.rerun()

st.sidebar.caption(f"Storage: `{settings.local_data_path}`")

tab_users, tab_venues, tab_bookings, tab_matches, tab_queue, tab_wallet = st.tabs(
    [
        "Register / Users",
        "Venues & Courts",
        "Book & Availability",
        "Hybrid Booking",
        "Join Match (queue)",
        "Wallet",
    ]
)

# --- Tab 1: Register / Users ---
with tab_users:
    st.subheader("Register a dummy user")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Player**")
        with st.form("register_player"):
            uid = st.text_input("uid", key="player_uid", placeholder="demo_player_1")
            name = st.text_input("display name", key="player_name")
            phone = st.text_input("phone", key="player_phone", placeholder="+91...")
            if st.form_submit_button("Register player") and uid:
                run(user_service.register_player, db, uid, PlayerRegisterRequest(display_name=name, phone=phone))
                st.rerun()

    with col2:
        st.markdown("**Venue owner**")
        with st.form("register_owner"):
            uid = st.text_input("uid", key="owner_uid", placeholder="demo_owner_1")
            name = st.text_input("display name", key="owner_name")
            phone = st.text_input("phone", key="owner_phone", placeholder="+91...")
            if st.form_submit_button("Register owner") and uid:
                run(user_service.register_owner, db, uid, OwnerRegisterRequest(display_name=name, phone=phone))
                st.rerun()

    st.subheader("Registered users")
    st.dataframe(list_users(), use_container_width=True)

# --- Tab 2: Venues & Courts ---
with tab_venues:
    st.subheader(f"Create a venue (as {acting_as})")
    with st.form("create_venue"):
        v_name = st.text_input("Venue name", value="SportsOS Demo Arena")
        v_city = st.text_input("City", value="Hyderabad")
        v_lat = st.number_input("Latitude", value=17.4, format="%.4f")
        v_lng = st.number_input("Longitude", value=78.4, format="%.4f")
        v_sports = st.text_input("Sports (comma-separated)", value="badminton,cricket")
        if st.form_submit_button("Create venue"):
            venue = run(
                venue_service.create_venue,
                db,
                acting_as,
                VenueCreateRequest(
                    name=v_name,
                    city=v_city,
                    geo=GeoPoint(lat=v_lat, lng=v_lng),
                    sports=[s.strip() for s in v_sports.split(",") if s.strip()],
                ),
            )
            if venue:
                st.success(f"Created venue {venue.tenant_id}")
                st.rerun()

    st.subheader("Venues & courts")
    for venue in list_venues():
        with st.expander(f"{venue['name']} ({venue['city']}) — {venue['tenant_id']}"):
            courts = court_service.list_courts(db, venue["tenant_id"])
            st.dataframe([c.model_dump() for c in courts], use_container_width=True)

            with st.form(f"add_court_{venue['tenant_id']}"):
                c_name = st.text_input("Court name", value="Court 1", key=f"cname_{venue['tenant_id']}")
                c_sport = st.text_input("Sport", value="badminton", key=f"csport_{venue['tenant_id']}")
                c_price = st.number_input("Hourly price", value=600.0, key=f"cprice_{venue['tenant_id']}")
                c_open = st.time_input("Open time", value=time(6, 0), key=f"copen_{venue['tenant_id']}")
                c_close = st.time_input("Close time", value=time(23, 0), key=f"cclose_{venue['tenant_id']}")
                if st.form_submit_button("Add court"):
                    run(
                        court_service.create_court,
                        db,
                        venue["tenant_id"],
                        CourtCreateRequest(
                            name=c_name,
                            sport=c_sport,
                            hourly_price=c_price,
                            open_time=c_open.strftime("%H:%M"),
                            close_time=c_close.strftime("%H:%M"),
                        ),
                    )
                    st.rerun()

# --- Tab 3: Book & Availability ---
with tab_bookings:
    venues = list_venues()
    if not venues:
        st.info("Create a venue first.")
    else:
        venue_choice = st.selectbox(
            "Venue", options=venues, format_func=lambda v: f"{v['name']} ({v['tenant_id']})", key="book_venue"
        )
        courts = court_service.list_courts(db, venue_choice["tenant_id"])
        if not courts:
            st.info("Add a court to this venue first.")
        else:
            court_choice = st.selectbox(
                "Court", options=courts, format_func=lambda c: f"{c.name} ({c.sport})", key="book_court"
            )
            book_date = st.date_input("Date", value=date.today(), key="book_date")

            avail = booking_service.get_availability(db, venue_choice["tenant_id"], court_choice.court_id, book_date.isoformat())
            st.write("**Open slots:**", [f"{s.start_time}-{s.end_time}" for s in avail.open_slots])
            st.write("**Booked slots:**", [f"{s.start_time}-{s.end_time}" for s in avail.booked_slots])

            with st.form("create_booking"):
                start = st.time_input("Start time", value=time(18, 0))
                end = st.time_input("End time", value=time(19, 0))
                if st.form_submit_button(f"Book as {acting_as}"):
                    booking = run(
                        booking_service.create_booking,
                        db,
                        venue_choice["tenant_id"],
                        acting_as,
                        BookingCreateRequest(
                            court_id=court_choice.court_id,
                            date=book_date.isoformat(),
                            start_time=start.strftime("%H:%M"),
                            end_time=end.strftime("%H:%M"),
                        ),
                    )
                    if booking:
                        st.success(f"Booked {booking.booking_id} — price {booking.price}")
                        st.rerun()

    st.subheader(f"{acting_as}'s bookings")
    my_bookings = booking_service.list_my_bookings(db, acting_as)
    for b in my_bookings:
        cols = st.columns([4, 1])
        cols[0].write(
            f"`{b.booking_id}` — {b.sport} on {b.date} {b.start_time}-{b.end_time} — "
            f"{b.status} — joinable={b.is_joinable} ({b.slots_open}/{b.slots_total} open)"
        )
        if b.status == "confirmed" and cols[1].button("Cancel", key=f"cancel_{b.booking_id}"):
            run(booking_service.cancel_booking, db, b.tenant_id, b.booking_id, acting_as, False)
            st.rerun()

# --- Tab 4: Hybrid Booking (captain books a court, then opens leftover slots) ---
with tab_matches:
    st.caption(
        "A captain books a court first, then opens leftover player slots to the community. "
        "For pure PUBG-style matchmaking with no prior booking, see the **Join Match (queue)** tab."
    )
    st.subheader(f"Open one of {acting_as}'s bookings to the community")
    my_bookings = [b for b in booking_service.list_my_bookings(db, acting_as) if b.status == "confirmed" and not b.is_joinable]
    if not my_bookings:
        st.info("No confirmed, not-yet-open bookings for this user.")
    else:
        booking_choice = st.selectbox(
            "Booking",
            options=my_bookings,
            format_func=lambda b: f"{b.sport} {b.date} {b.start_time}-{b.end_time} ({b.booking_id})",
            key="open_booking",
        )
        slots = st.number_input("Slots to open", min_value=1, value=3, step=1)
        if st.button("Open to community"):
            run(
                match_service.open_to_community,
                db,
                booking_choice.tenant_id,
                booking_choice.booking_id,
                acting_as,
                OpenToCommunityRequest(slots_open=int(slots)),
            )
            st.rerun()

    st.subheader("Discover open matches")
    sport_filter = st.text_input("Filter by sport (optional)", key="discover_sport")
    date_filter = st.date_input("Filter by date (optional)", value=None, key="discover_date")
    matches = match_service.discover_matches(
        db, sport=sport_filter or None, date=date_filter.isoformat() if date_filter else None
    )
    for m in matches:
        cols = st.columns([4, 1])
        cols[0].write(
            f"`{m.booking_id}` — {m.tenant_name} — {m.sport} on {m.date} {m.start_time}-{m.end_time} — "
            f"{m.slots_open}/{m.slots_total} open"
        )
        if m.created_by != acting_as and cols[1].button("Join", key=f"join_{m.booking_id}"):
            run(match_service.join_match, db, m.tenant_id, m.booking_id, acting_as)
            st.rerun()

        with st.expander(f"Participants of {m.booking_id}"):
            st.dataframe([p.model_dump() for p in match_service.list_participants(db, m.tenant_id, m.booking_id)])

# --- Tab 5: Join Match (queue) — PUBG-style matchmaking, no prior booking ---
with tab_queue:
    st.caption(
        "No captain, no pre-existing booking: queue for an open slot, and once enough players "
        "(per-sport minimum) queue for the exact same slot, the system forms the match, books "
        "the court, and splits the cost automatically."
    )
    venues = list_venues()
    if not venues:
        st.info("Create a venue and court first (see the Venues & Courts tab).")
    else:
        q_venue = st.selectbox(
            "Venue", options=venues, format_func=lambda v: f"{v['name']} ({v['tenant_id']})", key="queue_venue"
        )
        q_courts = court_service.list_courts(db, q_venue["tenant_id"])
        if not q_courts:
            st.info("Add a court to this venue first.")
        else:
            q_court = st.selectbox(
                "Court", options=q_courts, format_func=lambda c: f"{c.name} ({c.sport})", key="queue_court"
            )
            min_players = matchmaking_service.MIN_PLAYERS.get(q_court.sport, matchmaking_service.DEFAULT_MIN_PLAYERS)
            st.caption(f"Minimum players to form a match for {q_court.sport}: **{min_players}**")

            q_date = st.date_input("Date", value=date.today(), key="queue_date")
            q_start = st.time_input("Start time", value=time(18, 0), key="queue_start")
            q_end = st.time_input("End time", value=time(19, 0), key="queue_end")

            if st.button(f"Queue to play as {acting_as}"):
                result = run(
                    matchmaking_service.create_match_request,
                    db,
                    q_venue["tenant_id"],
                    acting_as,
                    MatchRequestCreate(
                        court_id=q_court.court_id,
                        date=q_date.isoformat(),
                        start_time=q_start.strftime("%H:%M"),
                        end_time=q_end.strftime("%H:%M"),
                    ),
                )
                if result:
                    if result.status == "matched":
                        st.success(f"Match formed! Booking {result.matched_booking_id} — you've been charged your share.")
                    else:
                        st.success(f"Queued — {result.current_count}/{result.min_players} players so far.")
                    st.rerun()

            st.subheader(f"Queue for {q_court.name} on {q_date.isoformat()}")
            requests = matchmaking_service.list_match_requests(db, q_venue["tenant_id"], q_court.court_id, q_date.isoformat())
            for r in requests:
                cols = st.columns([4, 1])
                cols[0].write(
                    f"{r.start_time}-{r.end_time} — `{r.uid}` — {r.status} "
                    f"({r.current_count}/{r.min_players})" + (f" — booking {r.matched_booking_id}" if r.matched_booking_id else "")
                )
                if r.uid == acting_as and r.status == "waiting" and cols[1].button("Cancel", key=f"cancel_req_{r.request_id}"):
                    run(matchmaking_service.cancel_match_request, db, q_venue["tenant_id"], r.request_id, acting_as)
                    st.rerun()

# --- Tab 6: Wallet ---
with tab_wallet:
    st.subheader(f"{acting_as}'s wallet")
    wallet = run(wallet_service.get_wallet, db, acting_as)
    if wallet:
        st.metric("Balance", wallet.balance)

        with st.form("topup"):
            amount = st.number_input("Top-up amount", min_value=0.0, value=500.0, step=50.0)
            if st.form_submit_button("Top up (demo only, no real payment)"):
                run(wallet_service.credit_wallet, db, acting_as, amount, "Streamlit demo top-up")
                st.rerun()

        st.subheader("Transaction ledger")
        txns = wallet_service.list_transactions(db, acting_as)
        st.dataframe([t.model_dump() for t in txns], use_container_width=True)
    else:
        st.info("This user has no wallet — register them as a player first.")
