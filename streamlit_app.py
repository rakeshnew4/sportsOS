"""Local demo UI for SportsOS — talks directly to app/services/*.py (no HTTP,
no Firebase Auth) against the local JSON-backed fake Firestore, so the full
demo flow can be exercised with dummy data before pointing at real Firestore.

Run with: streamlit run streamlit_app.py
"""

from datetime import date, time

import pandas as pd
import streamlit as st
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.db import FieldFilter, get_db
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
    team_service,
    user_service,
    venue_service,
    wallet_service,
    waitlist_service,
    kpi_service,
    pricing_service,
    recommendations_service,
    notifications_service,
)
from app.models.kpi import PlayerKPIScope

st.set_page_config(page_title="SportsOS demo", page_icon="🏟️", layout="wide")

SPORT_EMOJI = {
    "badminton": "🏸",
    "cricket": "🏏",
    "football": "⚽",
    "tennis": "🎾",
    "table_tennis": "🏓",
    "volleyball": "🏐",
    "basketball": "🏀",
    "pickleball": "🥒",
    "swimming": "🏊",
    "gym": "🏋️",
    "snooker": "🎱",
}
STATUS_COLOR = {
    "confirmed": "green",
    "waiting": "orange",
    "matched": "green",
    "cancelled": "red",
    "completed": "blue",
    "pending_payment": "orange",
}


def sport_emoji(sport: str) -> str:
    return SPORT_EMOJI.get((sport or "").lower(), "🏟️")


def status_text(label: str) -> str:
    color = STATUS_COLOR.get(label, "gray")
    return f":{color}[**{label}**]"


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
        st.error(f"{exc.status_code}: {exc.detail}", icon="⚠️")
        return None


def generate_hourly_slots(open_time_str: str, close_time_str: str) -> list[dict]:
    """1-hour slots starting every 30 min, fully within [open_time, close_time]."""
    court_open = time(*map(int, open_time_str.split(':')))
    court_close = time(*map(int, close_time_str.split(':')))

    slots = []
    current = court_open
    while current < court_close:
        start_min = current.hour * 60 + current.minute
        end_min = start_min + 60
        if end_min <= court_close.hour * 60 + court_close.minute:
            end_slot = time(end_min // 60, end_min % 60)
            slots.append({
                'start': current.strftime("%H:%M"),
                'end': end_slot.strftime("%H:%M"),
                'label': f"{current.strftime('%H:%M')}–{end_slot.strftime('%H:%M')}",
            })
        h, m = current.hour, current.minute + 30
        if m >= 60:
            h, m = h + 1, m - 60
        if h >= 24:
            break
        current = time(h, m)
    return slots


def list_users() -> list[dict]:
    return [{"uid": doc.id, **doc.to_dict()} for doc in db.collection("users").stream()]


def list_venues() -> list[dict]:
    return [{"tenant_id": doc.id, **doc.to_dict()} for doc in db.collection("tenants").stream()]


def find_user_by_phone(phone: str) -> dict | None:
    phone = phone.strip()
    if not phone:
        return None
    for doc in db.collection("users").where(filter=FieldFilter("phone", "==", phone)).stream():
        return {"uid": doc.id, **doc.to_dict()}
    return None


# --- Onboarding / login gate ---
if "logged_in_uid" not in st.session_state:
    st.session_state.logged_in_uid = None

if not st.session_state.logged_in_uid:
    st.title("🏟️ Welcome to SportsOS")
    st.caption("Local demo — log in with a phone number, or sign up as a new player or venue owner.")

    login_tab, signup_tab = st.tabs(["🔑 Log in", "📝 Sign up"])

    with login_tab, st.container(border=True), st.form("login_form"):
        phone = st.text_input("Phone number", placeholder="+91...", key="login_phone")
        if st.form_submit_button("Log in", use_container_width=True):
            found = find_user_by_phone(phone)
            if found:
                st.session_state.logged_in_uid = found["uid"]
                st.rerun()
            else:
                st.error("No account found with that phone number — sign up instead.", icon="⚠️")

    with signup_tab:
        role = st.radio("I am a...", ["Player", "Venue owner"], horizontal=True, key="signup_role")
        with st.container(border=True), st.form("signup_form"):
            su_name = st.text_input("Display name", key="signup_name")
            su_phone = st.text_input("Phone number", placeholder="+91...", key="signup_phone")
            if st.form_submit_button("Create account", use_container_width=True) and su_phone:
                try:
                    if role == "Player":
                        me = user_service.register_player(db, PlayerRegisterRequest(display_name=su_name, phone=su_phone))
                    else:
                        me = user_service.register_owner(db, OwnerRegisterRequest(display_name=su_name, phone=su_phone))
                    st.session_state.logged_in_uid = me.uid
                    st.rerun()
                except HTTPException as exc:
                    st.error(f"{exc.status_code}: {exc.detail}", icon="⚠️")

    st.stop()

acting_as = st.session_state.logged_in_uid

# --- Sidebar: identity + reset ---
st.sidebar.markdown("## 🏟️ SportsOS")
st.sidebar.caption("Local dummy-data demo")
st.sidebar.divider()

users = list_users()
current_user = next((u for u in users if u["uid"] == acting_as), None)

st.sidebar.markdown(f"**Logged in as**  \n{(current_user or {}).get('display_name', acting_as)} (`{acting_as}`)")
if current_user:
    roles = current_user.get("roles", {})
    badges = []
    if roles.get("player"):
        badges.append("🎽 Player")
    if roles.get("owner"):
        badges.append(f"🏢 Owner ×{len(roles['owner'])}")
    if roles.get("staff"):
        badges.append(f"🧑‍💼 Staff ×{len(roles['staff'])}")
    st.sidebar.caption(" · ".join(badges) if badges else "No roles yet")

    wallet_doc = db.collection("players").document(acting_as).collection("wallet").document("wallet").get()
    if wallet_doc.exists:
        st.sidebar.metric("Wallet balance", f"₹{wallet_doc.to_dict()['balance']:.0f}")

    # Notifications
    try:
        unread = notifications_service.get_unread_notifications(db, acting_as, limit=5)
        if unread:
            st.sidebar.divider()
            st.sidebar.markdown(f"**Notifications ({len(unread)})**")
            for notif in unread:
                with st.sidebar.container(border=True):
                    # Icon by type
                    icon = {
                        "match_formed": "🎉",
                        "match_filling": "⏳",
                        "recommendation": "✨",
                        "booking_reminder": "⏰",
                    }.get(notif["type"], "🔔")
                    st.caption(f"{icon} {notif['title']}")
                    st.caption(notif['body'])
                    if st.button("Dismiss", key=f"dismiss_{notif['id']}", use_container_width=True):
                        notifications_service.mark_as_read(db, acting_as, notif['id'])
                        st.rerun()
    except Exception:
        pass

if st.sidebar.button("🚪 Log out", use_container_width=True):
    st.session_state.logged_in_uid = None
    st.rerun()

with st.sidebar.expander("🔧 Switch user (testing shortcut)"):
    user_labels = {u["uid"]: f"{u['uid']} — {u.get('display_name', '?')}" for u in users}
    uid_options = list(user_labels.keys())
    switch_choice = st.selectbox(
        "Act as a different registered user",
        options=uid_options,
        format_func=lambda uid: user_labels.get(uid, uid),
        index=uid_options.index(acting_as) if acting_as in uid_options else 0,
        key="switch_user_select",
    )
    if st.button("Switch", key="switch_user_btn", use_container_width=True):
        st.session_state.logged_in_uid = switch_choice
        st.rerun()

st.sidebar.divider()
if st.sidebar.button("🗑️ Reset demo data", type="secondary", use_container_width=True):
    db.reset()
    st.session_state.logged_in_uid = None
    st.sidebar.success("Local data cleared.")
    st.rerun()

st.sidebar.caption(f"Storage: `{settings.local_data_path}`")

st.title("🏟️ SportsOS")
st.caption(
    f"Logged in as `{acting_as}`. Find venues, book courts, or play with others."
)

tab_home, tab_discover, tab_mybookings, tab_matches, tab_queue, tab_wallet, tab_teams, tab_notifications, tab_waitlist, tab_staff, tab_admin = st.tabs(
    [
        "🏠 Home",
        "🔍 Discover Venues",
        "📅 My Bookings",
        "🤝 Hybrid Booking",
        "🎮 Join Match (queue)",
        "💰 Wallet",
        "👥 Teams",
        "📢 Notifications",
        "⏳ Waitlist",
        "🏢 Staff Dashboard",
        "⚙️ Admin",
    ]
)

# --- Tab 0: Home ---
with tab_home:
    st.subheader(f"Welcome back, {(current_user or {}).get('display_name', acting_as)}! 👋")

    # Quick stats
    col1, col2, col3 = st.columns(3)
    wallet_doc = db.collection("players").document(acting_as).collection("wallet").document("wallet").get()
    balance = wallet_doc.to_dict()["balance"] if wallet_doc.exists else 0
    my_bookings = booking_service.list_my_bookings(db, acting_as)
    col1.metric("💰 Wallet Balance", f"₹{balance:.0f}")
    col2.metric("📅 Upcoming bookings", len([b for b in my_bookings if b.status == "confirmed"]))
    col3.metric("👥 Your role", "Player" if (current_user or {}).get("roles", {}).get("player") else "Venue Owner" if (current_user or {}).get("roles", {}).get("owner") else "Unknown")

    st.divider()

    # Quick actions
    st.subheader("🎯 Quick Actions")
    col_action1, col_action2, col_action3 = st.columns(3)

    with col_action1:
        if st.button("🔍 Find a match", use_container_width=True, key="home_discover"):
            st.session_state.active_tab = "discover"

    with col_action2:
        if st.button("📅 My bookings", use_container_width=True, key="home_bookings"):
            st.session_state.active_tab = "bookings"

    with col_action3:
        if st.button("💰 Top up wallet", use_container_width=True, key="home_wallet"):
            st.session_state.active_tab = "wallet"

    st.divider()

    # Player KPIs
    try:
        player_kpi = kpi_service.get_player_engagement_kpi(db, acting_as, PlayerKPIScope.MONTH)
        st.subheader("📊 Your Stats (This Month)")
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("Matches played", player_kpi.matches_played)
        kpi_col2.metric("Hours played", f"{player_kpi.hours_played:.1f}h")
        kpi_col3.metric("Wallet spent", f"₹{player_kpi.wallet_total_spend:.0f}")
        kpi_col4.metric("Favorite sport", player_kpi.favorite_sport or "—")

        kpi_col5, kpi_col6, kpi_col7 = st.columns(3)
        kpi_col5.metric("Venues visited", player_kpi.repeat_venues)
        kpi_col6.metric("Weekly sessions", f"{player_kpi.weekly_sessions:.1f}")
        kpi_col7.metric("Favorite venue", player_kpi.favorite_venue or "—")
    except Exception as e:
        st.caption(f"_KPI data not available yet_")

    st.divider()

    # Upcoming bookings
    if my_bookings:
        st.subheader("📅 Your upcoming bookings")
        upcoming = [b for b in my_bookings if b.status == "confirmed"]
        if upcoming:
            for b in upcoming[:3]:  # Show top 3
                with st.container(border=True):
                    team_info = f" · 🎽 **{b.team_name}**" if b.team_name else ""
                    st.markdown(
                        f"{sport_emoji(b.sport)} **{b.sport}** · {b.date} {b.start_time}–{b.end_time}{team_info}  \n"
                        f"💵 ₹{b.price} · {status_text(b.status)}"
                    )
        else:
            st.caption("No upcoming bookings yet — explore venues below!")

    # Smart recommendations
    st.subheader("🎯 Recommended for you")
    try:
        recommendations = recommendations_service.get_player_recommendations(db, acting_as, limit=5)
        if recommendations:
            for rec in recommendations:
                with st.container(border=True):
                    score_bar = "🔥 " * (rec["score"] // 5) if rec["score"] >= 15 else "✓ " * (rec["score"] // 5)
                    st.markdown(f"{sport_emoji(rec['sport'])} **{rec['sport'].upper()}** · {rec['venue']} · {rec['date']} {rec['time']}")
                    st.caption(f"{rec['slots']} players · {score_bar} {', '.join(rec['reasons'][:2])}")
                    if st.button(f"Join this match", key=f"join_rec_{rec['booking_id']}", use_container_width=True):
                        st.info("Redirect to Hybrid Booking tab to join", icon="ℹ️")
        else:
            st.caption("_No recommendations available yet — play some matches first!_")
    except Exception as e:
        st.caption(f"_Recommendations not available_")

    st.divider()

    # Popular sports
    st.subheader("⭐ Popular sports")
    venues_all = list_venues()
    if venues_all:
        all_sports = {}
        for v in venues_all:
            for sport in v.get("sports", []):
                all_sports[sport] = all_sports.get(sport, 0) + 1
        if all_sports:
            col_sports = st.columns(min(4, len(all_sports)))
            for idx, (sport, count) in enumerate(sorted(all_sports.items(), key=lambda x: x[1], reverse=True)[:4]):
                with col_sports[idx]:
                    st.button(f"{sport_emoji(sport)} {sport.title()}\n({count} venues)", use_container_width=True, key=f"sport_btn_{sport}")


# --- Tab 7: Teams (Phase 3) ---
with tab_teams:
    st.subheader("👥 My Teams")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Create Team", use_container_width=True):
            st.session_state.show_create_team = True

    if st.session_state.get("show_create_team"):
        with st.container(border=True):
            st.markdown("### Create New Team")
            team_name = st.text_input("Team Name", placeholder="e.g., Elite Shuttlers")
            sport = st.selectbox("Sport", ["badminton", "basketball", "tennis", "volleyball"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create", use_container_width=True):
                    team = run(team_service.create_team, db, acting_as, sport, team_name)
                    if team:
                        st.success(f"✅ Team '{team_name}' created!")
                        st.session_state.show_create_team = False
                        st.rerun()
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_create_team = False
        st.divider()

    # List user's teams
    my_teams = team_service.list_player_teams(db, acting_as)

    if not my_teams:
        st.info("You don't have any teams yet. Create one to get started!", icon="🎯")
    else:
        for team in my_teams:
            stats = team_service.get_team_stats(db, team.team_id)

            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.markdown(f"**{sport_emoji(team.sport)} {team.team_name}**")
                captain_label = "You" if team.captain_uid == acting_as else team.captain_uid
                st.caption(f"{team.total_members} members · Captain: {captain_label}")

            with col2:
                st.metric("⭐ Rating", f"{stats['rating']:.0f}")

            with col3:
                st.metric("Record", f"{stats['wins']}W-{stats['losses']}L")

            with col4:
                if st.button("View", key=f"team_{team.team_id}", use_container_width=True):
                    st.session_state.selected_team = team.team_id

            # Show team details if selected
            if st.session_state.get("selected_team") == team.team_id:
                st.divider()
                st.markdown(f"### Team Details: {team.team_name}")

                team_tab1, team_tab2, team_tab3 = st.tabs(["Members", "History", "Stats"])

                with team_tab1:
                    st.write("**Team Members:**")
                    members_data = {
                        "Player": [
                            f"{m.display_name or m.uid}{' (Captain)' if m.uid == team.captain_uid else ''}"
                            for m in team.members
                        ],
                        "Joined": [m.joined_at[:10] for m in team.members],
                    }
                    st.dataframe(pd.DataFrame(members_data), use_container_width=True)

                with team_tab2:
                    st.write("**Recent Matches:**")
                    history = team_service.get_team_history(db, team.team_id, limit=10)
                    if not history:
                        st.caption("No matches played yet.")
                    else:
                        st.dataframe(
                            pd.DataFrame([
                                {
                                    "Date": h["played_at"][:10],
                                    "Opponent": h["opponent_team_name"],
                                    "Result": h["result"].title(),
                                    "Players": h["player_count"],
                                }
                                for h in history
                            ]),
                            use_container_width=True,
                        )

                with team_tab3:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Matches", stats["total_matches"])
                    with col2:
                        st.metric("Win Rate", f"{stats['win_rate']:.0f}%")
                    with col3:
                        st.metric("ELO Rating", f"{stats['rating']:.0f}")

            st.divider()

# --- Tab 8: Notifications (Phase 4) ---
with tab_notifications:
    st.subheader("📢 Notifications")

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("⚙️ Preferences", use_container_width=True):
            st.session_state.show_notif_prefs = True

    # Notification preferences
    if st.session_state.get("show_notif_prefs"):
        with st.container(border=True):
            st.markdown("### Notification Preferences")

            notif_prefs = {
                "Match Needs Players": st.checkbox("Match Needs Players", value=True, key="pref_match"),
                "Waitlist Promotion": st.checkbox("Waitlist Promotion", value=True, key="pref_waitlist"),
                "Team Challenges": st.checkbox("Team Challenges", value=True, key="pref_challenges"),
                "Match Reminders": st.checkbox("Match Reminders (30 min before)", value=True, key="pref_reminders"),
                "Rewards Earned": st.checkbox("Rewards Earned", value=True, key="pref_rewards"),
            }

            if st.button("Save Preferences", use_container_width=True):
                try:
                    # Update preferences in database
                    notifications_service.update_notification_preferences(db, acting_as, notif_prefs)
                    st.success("✅ Preferences updated!")
                    st.session_state.show_notif_prefs = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save preferences: {e}")

        st.divider()

    # List notifications
    try:
        unread_notifs = notifications_service.get_unread_notifications(db, acting_as, limit=20)
        all_notifs = unread_notifs

        show_unread = st.checkbox("Show unread only", value=False)

        if not all_notifs:
            st.info("No notifications yet!", icon="🔔")
        else:
            for notif in all_notifs:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([5, 1, 1])

                    # Icon by type
                    icon = {
                        "promoted": "🎉",
                        "match_needs": "⏳",
                        "challenge": "⚔️",
                        "reminder": "⏰",
                        "reward": "⭐",
                    }.get(notif.get("type", ""), "🔔")

                    with col1:
                        st.markdown(f"""
                        {icon} **{notif.get('title', 'Notification')}**

                        {notif.get('body', '')}

                        *{notif.get('created_at', 'Just now')}*
                        """)

                    with col2:
                        if not notif.get('read'):
                            if st.button("✓", key=f"read_{notif.get('id')}", use_container_width=True):
                                try:
                                    notifications_service.mark_as_read(db, acting_as, notif['id'])
                                    st.rerun()
                                except Exception:
                                    pass

                    with col3:
                        if st.button("×", key=f"dismiss_{notif.get('id')}", use_container_width=True):
                            try:
                                notifications_service.mark_as_read(db, acting_as, notif['id'])
                                st.rerun()
                            except Exception:
                                pass
    except Exception as e:
        st.info("Notifications feature is being integrated...")

# --- Tab 9: Waitlist (Phase 4) ---
with tab_waitlist:
    st.subheader("⏳ Waitlist Management")

    # Get user's waitlist entries
    try:
        my_bookings = booking_service.list_my_bookings(db, acting_as)

        # Find any full bookings user is on waitlist for
        waitlist_entries = []
        for booking in my_bookings:
            if booking.status == "confirmed":  # Check if user is already in this booking
                pass  # Would need to query waitlist subcollection

        # Mock waitlist data
        mock_waitlist = [
            {
                "id": "wl-1",
                "booking_id": "booking-1",
                "sport": "Basketball",
                "venue": "City Arena",
                "date": "Today 7:30 PM",
                "position": 2,
                "status": "waiting",
                "joined_at": "5 minutes ago"
            },
            {
                "id": "wl-2",
                "booking_id": "booking-3",
                "sport": "Badminton",
                "venue": "Court B",
                "date": "Tomorrow 6:00 PM",
                "position": 1,
                "status": "promoted",
                "joined_at": "2 hours ago",
                "expires_at": "in 20 minutes"
            }
        ]

        if not mock_waitlist:
            st.info("You're not on any waitlists yet. Full matches show a waitlist option!", icon="⏳")
        else:
            for entry in mock_waitlist:
                with st.container(border=True):
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

                    with col1:
                        st.markdown(f"""
                        **{entry['sport']}** • {entry['venue']}

                        {entry['date']}
                        """)

                    with col2:
                        if entry['status'] == "promoted":
                            st.markdown("🎉 **PROMOTED**")
                        else:
                            st.markdown(f"⏳ **#{entry['position']}**")

                    with col3:
                        st.caption(entry['joined_at'])

                    with col4:
                        if entry['status'] == "promoted":
                            if st.button("✓ Confirm", key=f"confirm_{entry['id']}", use_container_width=True):
                                try:
                                    # Call confirm_promotion
                                    st.success("✅ Slot confirmed! See you at the match.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")

                    with col5:
                        if entry['status'] == "promoted":
                            if st.button("✗ Decline", key=f"decline_{entry['id']}", use_container_width=True):
                                try:
                                    # Call decline_promotion
                                    st.info("Declined. Next player promoted.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                        else:
                            if st.button("Leave", key=f"leave_{entry['id']}", use_container_width=True):
                                try:
                                    # Call remove_from_waitlist
                                    st.info("Left waitlist.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
    except Exception as e:
        st.info("Waitlist feature is being integrated...")

# --- Tab 10: Staff Dashboard (Phase 1) ---
with tab_staff:
    st.subheader("🏢 Venue Staff Dashboard")

    from app.models.kpi import VenueKPIScope

    # Check if user is staff or owner at any venues
    users_data = list_users()
    current_user_data = next((u for u in users_data if u["uid"] == acting_as), None)

    owner_venues = current_user_data.get("roles", {}).get("owner", []) if current_user_data else []
    staff_venues = current_user_data.get("roles", {}).get("staff", []) if current_user_data else []

    managed_venues = owner_venues + staff_venues

    if not managed_venues:
        st.info("You're not a staff member or owner at any venues yet.", icon="🏢")
    else:
        venue_choice = st.selectbox(
            "Select Venue",
            options=managed_venues,
            key="staff_venue"
        )

        venues_list = list_venues()
        selected_venue = next((v for v in venues_list if v["tenant_id"] == venue_choice), None)

        if selected_venue:
            tenant_id = selected_venue["tenant_id"]
            st.markdown(f"### {selected_venue['name']}")

            today_str = date.today().isoformat()
            today_bookings = booking_service.list_venue_bookings(db, tenant_id, date=today_str)
            confirmed_today = [b for b in today_bookings if b.status == "confirmed"]
            overview_today = kpi_service.get_venue_overview_kpi(db, tenant_id, VenueKPIScope.TODAY)

            staff_roster = []
            for u in users_data:
                roles = u.get("roles", {})
                if tenant_id in roles.get("owner", []):
                    staff_roster.append({"uid": u["uid"], "display_name": u.get("display_name") or u["uid"], "role": "Owner"})
                elif tenant_id in roles.get("staff", []):
                    staff_roster.append({"uid": u["uid"], "display_name": u.get("display_name") or u["uid"], "role": "Staff"})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Today Revenue", f"₹{overview_today.revenue.total_revenue:.0f}")
            with col2:
                st.metric("Occupancy (today)", f"{overview_today.avg_occupancy_percent:.0f}%")
            with col3:
                st.metric("Active Bookings", str(len(confirmed_today)))
            with col4:
                st.metric("Staff Members", str(len(staff_roster)))

            st.divider()

            courts_by_id = {c.court_id: c for c in court_service.list_courts(db, tenant_id)}

            # Tabs for staff functions
            staff_tab1, staff_tab2, staff_tab3, staff_tab4 = st.tabs([
                "📅 Today's Bookings",
                "⏳ Waitlists",
                "👥 Staff",
                "📊 Analytics"
            ])

            with staff_tab1:
                st.markdown("**Today's Bookings**")
                if not today_bookings:
                    st.caption("No bookings today.")
                else:
                    rows = []
                    for b in today_bookings:
                        court = courts_by_id.get(b.court_id)
                        participant_count = len(list(
                            db.collection("tenants").document(tenant_id)
                            .collection("bookings").document(b.booking_id)
                            .collection("participants").stream()
                        ))
                        attendees = 1 + participant_count
                        players = f"{attendees}/{b.slots_total + 1}" if b.is_joinable else str(attendees)
                        rows.append({
                            "Time": f"{b.start_time}-{b.end_time}",
                            "Sport": b.sport.title(),
                            "Court": court.name if court else b.court_id,
                            "Players": players,
                            "Revenue": f"₹{b.price:.0f}",
                            "Status": b.status.title(),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)

            with staff_tab2:
                st.markdown("**Active Waitlists**")
                any_waitlist = False
                for b in today_bookings:
                    wl = waitlist_service.get_waitlist(db, tenant_id, b.booking_id)
                    if wl["total_waiting"] > 0:
                        any_waitlist = True
                        court = courts_by_id.get(b.court_id)
                        first = wl["queue"][0]
                        col1, col2, col3, col4 = st.columns([2, 1, 1.5, 1])
                        with col1:
                            st.markdown(f"**{sport_emoji(b.sport)} {b.sport.title()} {b.start_time}** · {court.name if court else b.court_id}")
                        with col2:
                            st.markdown(f"{wl['total_waiting']} waiting")
                        with col3:
                            st.markdown(f"#1: `{first['player_uid']}`")
                        with col4:
                            if st.button("Promote", key=f"promote_staff_{b.booking_id}", use_container_width=True):
                                run(waitlist_service.promote_from_waitlist, db, tenant_id, b.booking_id)
                                st.rerun()
                if not any_waitlist:
                    st.caption("No one on a waitlist right now.")

            with staff_tab3:
                st.markdown("**Staff Members**")

                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("➕ Add Staff", use_container_width=True):
                        st.session_state.show_add_staff = True

                if st.session_state.get("show_add_staff"):
                    with st.container(border=True):
                        st.markdown("### Add Staff Member")
                        existing_uids = {s["uid"] for s in staff_roster}
                        candidates = [u for u in users_data if u["uid"] not in existing_uids]
                        if not candidates:
                            st.caption("No other registered users to add. Sign up more test accounts first.")
                        else:
                            new_staff = st.selectbox(
                                "Registered user",
                                options=candidates,
                                format_func=lambda u: f"{u.get('display_name') or u['uid']} ({u['uid']})",
                                key="new_staff_pick",
                            )
                            new_role = st.selectbox("Role", ["staff", "owner"], key="new_staff_role")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Add", use_container_width=True):
                                    roles = new_staff.get("roles", {})
                                    role_list = roles.get(new_role, [])
                                    if tenant_id not in role_list:
                                        role_list.append(tenant_id)
                                    roles[new_role] = role_list
                                    db.collection("users").document(new_staff["uid"]).update({"roles": roles})
                                    st.success(f"Added {new_staff.get('display_name') or new_staff['uid']} as {new_role}!")
                                    st.session_state.show_add_staff = False
                                    st.rerun()
                            with col2:
                                if st.button("Cancel", use_container_width=True):
                                    st.session_state.show_add_staff = False
                    st.divider()

                if not staff_roster:
                    st.caption("No staff on record.")
                else:
                    st.dataframe(
                        pd.DataFrame([
                            {"Name": s["display_name"], "UID": s["uid"], "Role": s["role"]}
                            for s in staff_roster
                        ]),
                        use_container_width=True,
                    )

            with staff_tab4:
                st.markdown("**Venue Analytics (last 7 days)**")
                overview_week = kpi_service.get_venue_overview_kpi(db, tenant_id, VenueKPIScope.WEEK)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Weekly Revenue", f"₹{overview_week.revenue.total_revenue:.0f}")
                with col2:
                    st.metric("Avg Occupancy", f"{overview_week.avg_occupancy_percent:.0f}%")
                with col3:
                    st.metric("Repeat Players", f"{overview_week.customers.repeat_booking_percent:.0f}%")

                st.divider()

                all_bookings = booking_service.list_bookings(db, tenant_id)
                daily_revenue: dict[str, float] = {}
                today = date.today()
                for b in all_bookings:
                    if b.status != "confirmed":
                        continue
                    try:
                        bdate = date.fromisoformat(b.date)
                    except ValueError:
                        continue
                    if not (0 <= (today - bdate).days <= 6):
                        continue
                    daily_revenue[b.date] = daily_revenue.get(b.date, 0.0) + b.price

                if not daily_revenue:
                    st.caption("No confirmed bookings in the last 7 days yet.")
                else:
                    ordered_dates = sorted(daily_revenue)
                    chart_data = pd.DataFrame(
                        {"Revenue": [daily_revenue[d] for d in ordered_dates]},
                        index=ordered_dates,
                    )
                    st.line_chart(chart_data)

# --- Tab 1: Users / Admin ---
with tab_admin:
    st.caption("You already signed up via the login gate. Use this tab to add more test accounts for multi-user testing.")
    st.subheader("Register another dummy user")
    col1, col2 = st.columns(2)

    with col1, st.container(border=True):
        st.markdown("**🎽 Player**")
        with st.form("register_player"):
            uid = st.text_input("uid", key="player_uid", placeholder="demo_player_1")
            name = st.text_input("display name", key="player_name")
            phone = st.text_input("phone", key="player_phone", placeholder="+91...")
            if st.form_submit_button("Register player", use_container_width=True) and uid:
                run(user_service.register_player, db, PlayerRegisterRequest(display_name=name, phone=phone), uid=uid)
                st.rerun()

    with col2, st.container(border=True):
        st.markdown("**🏢 Venue owner**")
        with st.form("register_owner"):
            uid = st.text_input("uid", key="owner_uid", placeholder="demo_owner_1")
            name = st.text_input("display name", key="owner_name")
            phone = st.text_input("phone", key="owner_phone", placeholder="+91...")
            if st.form_submit_button("Register owner", use_container_width=True) and uid:
                run(user_service.register_owner, db, OwnerRegisterRequest(display_name=name, phone=phone), uid=uid)
                st.rerun()

    st.subheader("Registered users")
    all_users = list_users()
    if not all_users:
        st.info("No users registered yet — use the forms above to add some.", icon="👋")
    else:
        st.dataframe(
            all_users,
            use_container_width=True,
            hide_index=True,
            column_config={
                "uid": st.column_config.TextColumn("UID"),
                "display_name": st.column_config.TextColumn("Name"),
                "phone": st.column_config.TextColumn("Phone"),
                "created_at": None,
            },
        )

# --- Tab 1.5: Discover Venues ---
with tab_discover:
    st.subheader("🔍 Discover Venues")
    venues = list_venues()

    if not venues:
        st.info("No venues available yet. Venue owners can create one in the Admin tab.", icon="🏗️")
    else:
        # Filtering section
        col_filter1, col_filter2, col_filter3 = st.columns(3)

        # Get all available sports
        all_sports_set = set()
        for v in venues:
            all_sports_set.update(v.get("sports", []))
        all_sports_list = sorted(list(all_sports_set))

        with col_filter1:
            sport_filter = st.multiselect(
                "Filter by sport",
                options=all_sports_list,
                key="discover_sport_filter",
                default=[]
            )

        with col_filter2:
            city_filter = st.text_input(
                "Filter by city (optional)",
                key="discover_city_filter",
                placeholder="e.g., Hyderabad"
            )

        with col_filter3:
            price_range = st.slider(
                "Price range (₹/hr)",
                min_value=0,
                max_value=2000,
                value=(0, 2000),
                step=50,
                key="discover_price_filter"
            )

        st.divider()

        # Filter venues
        filtered_venues = []
        for v in venues:
            # Sport filter
            if sport_filter:
                if not any(s in v.get("sports", []) for s in sport_filter):
                    continue

            # City filter
            if city_filter and city_filter.lower() not in v.get("city", "").lower():
                continue

            filtered_venues.append(v)

        # Display filtered venues
        if not filtered_venues:
            st.info("No venues match your filters. Try adjusting them.", icon="🔍")
        else:
            st.subheader(f"Found {len(filtered_venues)} venue(s)")

            for venue in filtered_venues:
                with st.container(border=True):
                    col_info, col_action = st.columns([3, 1])

                    with col_info:
                        sports_line = " ".join(sport_emoji(s) for s in venue.get("sports", []))
                        st.markdown(
                            f"### 🏟️ {venue['name']}\n"
                            f"📍 {venue.get('city', 'Unknown')} · {sports_line}"
                        )
                        st.caption(f"ID: `{venue['tenant_id']}`")

                    with col_action:
                        if st.button("📅 Book", key=f"view_venue_{venue['tenant_id']}", use_container_width=True):
                            st.session_state.booking_venue = venue['tenant_id']

                    # Show courts
                    courts = court_service.list_courts(db, venue["tenant_id"])
                    if courts:
                        st.write("**Courts:**")
                        court_cols = st.columns(len(courts))
                        for idx, court in enumerate(courts):
                            with court_cols[idx]:
                                price_ok = price_range[0] <= court.hourly_price <= price_range[1]
                                st.metric(
                                    f"{sport_emoji(court.sport)} {court.name}",
                                    f"₹{court.hourly_price}/hr",
                                    delta="✓ In range" if price_ok else "Out of range",
                                    delta_color="normal" if price_ok else "off"
                                )
                    else:
                        st.caption("_No courts added yet_")

                # Booking flow - show when this venue is selected
                if "booking_venue" in st.session_state and st.session_state.booking_venue == venue["tenant_id"]:
                    st.divider()
                    st.subheader(f"🎫 Book a court at {venue['name']}")

                    courts = court_service.list_courts(db, venue["tenant_id"])
                    if not courts:
                        st.warning("This venue has no courts yet.")
                    else:
                        court_choice = st.selectbox(
                            "Select a court",
                            options=courts,
                            format_func=lambda c: f"{sport_emoji(c.sport)} {c.name} — ₹{c.hourly_price}/hr",
                            key=f"book_court_{venue['tenant_id']}",
                        )

                        book_date = st.date_input("Select date", value=date.today(), key=f"book_date_{venue['tenant_id']}")
                        avail = booking_service.get_availability(db, venue["tenant_id"], court_choice.court_id, book_date.isoformat())

                        booking_slots = generate_hourly_slots(court_choice.open_time, court_choice.close_time)

                        # Check if a slot is available
                        def is_booking_slot_available(start_str, end_str):
                            start_min = booking_service.to_minutes(start_str)
                            end_min = booking_service.to_minutes(end_str)
                            for booked in avail.booked_slots:
                                booked_start = booking_service.to_minutes(booked.start_time)
                                booked_end = booking_service.to_minutes(booked.end_time)
                                # Check overlap
                                if start_min < booked_end and end_min > booked_start:
                                    return False
                            return True

                        # Display booking slots grid
                        with st.container(border=True):
                            st.markdown("**📅 Available 1-Hour Slots**")
                            st.caption(f"Showing slots for {book_date.strftime('%A, %B %d')}")

                            slot_cols = st.columns(3)
                            for idx, slot in enumerate(booking_slots):
                                available = is_booking_slot_available(slot['start'], slot['end'])
                                col = slot_cols[idx % 3]

                                if available:
                                    if col.button(
                                        f"🟢 {slot['label']}\n₹{court_choice.hourly_price:.0f}",
                                        key=f"slot_{venue['tenant_id']}_{slot['start']}_{slot['end']}",
                                        use_container_width=True
                                    ):
                                        st.session_state[f"selected_slot_{venue['tenant_id']}"] = slot
                                        st.rerun()
                                else:
                                    col.markdown(f":gray[🔴 {slot['label']}]\n:gray[Booked]", help="This slot is booked")

                            st.caption("🟢 = Click to book | 🔴 = Already booked")

                        # Check if a slot was selected
                        selected_slot_key = f"selected_slot_{venue['tenant_id']}"
                        if selected_slot_key not in st.session_state:
                            st.info("👆 Click on an available slot above to select it", icon="⏰")
                        else:
                            selected_slot = st.session_state[selected_slot_key]

                            with st.form(f"create_booking_{venue['tenant_id']}"):
                                st.markdown(f"### 📅 Selected: **{selected_slot['label']}**")

                                team_name = st.text_input(
                                    "Team name (optional - auto-generated if empty)",
                                    value="",
                                    key=f"team_name_{venue['tenant_id']}",
                                    placeholder=f"e.g., {(current_user or {}).get('display_name', 'Team')}'s Squad"
                                )

                                # Allow duration extension beyond 1 hour
                                duration_options = ["1 hour", "1.5 hours", "2 hours", "2.5 hours", "3 hours"]
                                duration_str = st.selectbox(
                                    "Duration (extends end time)",
                                    options=duration_options,
                                    index=0,
                                    key=f"duration_{venue['tenant_id']}"
                                )
                                duration_hours = float(duration_str.split()[0])

                                # Calculate actual times
                                start = time(*map(int, selected_slot['start'].split(':')))
                                start_min = start.hour * 60 + start.minute
                                end_min = start_min + int(duration_hours * 60)

                                # Check if extended time is available
                                extended_end_hour = end_min // 60
                                extended_end_min = end_min % 60
                                extended_end = time(extended_end_hour, extended_end_min) if extended_end_hour < 24 else time(23, 59)

                                # Verify extended time doesn't conflict
                                conflicts = []
                                for booked in avail.booked_slots:
                                    booked_start = booking_service.to_minutes(booked.start_time)
                                    booked_end = booking_service.to_minutes(booked.end_time)
                                    if start_min < booked_end and end_min > booked_start:
                                        conflicts.append(f"{booked.start_time}–{booked.end_time}")

                                if conflicts:
                                    st.error(f"⚠️ Extended time conflicts with bookings: {', '.join(conflicts)}")
                                    duration_hours = None
                                else:
                                    st.caption(f"⏱️ Booking: **{selected_slot['start']} → {extended_end.strftime('%H:%M')}** ({duration_hours} hr{'s' if duration_hours > 1 else ''})")

                                    # Show dynamic pricing if enabled
                                    if court_choice.dynamic_pricing_enabled:
                                        price_breakdown = pricing_service.explain_dynamic_price(
                                            db, venue["tenant_id"], court_choice.court_id, book_date.isoformat(),
                                            selected_slot['start'], court_choice.hourly_price
                                        )
                                        with st.container(border=True):
                                            st.caption(f"**Dynamic pricing breakdown:**")
                                            st.caption(f"Base rate: ₹{price_breakdown['base_price']:.0f}/hr {price_breakdown.get('time_reason', '')}")
                                            st.caption(f"Occupancy surge: {(price_breakdown['occupancy_multiplier'] - 1) * 100:.0f}% {price_breakdown.get('occupancy_reason', '')}")
                                            st.caption(f"→ Adjusted rate: ₹{price_breakdown['final_price']:.0f}/hr")
                                        display_price = price_breakdown['final_price'] * duration_hours
                                    else:
                                        display_price = court_choice.hourly_price * duration_hours

                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.form_submit_button(f"💳 Book for ₹{display_price:.0f}", use_container_width=True):
                                            booking = run(
                                                booking_service.create_booking,
                                                db,
                                                venue["tenant_id"],
                                                acting_as,
                                                BookingCreateRequest(
                                                    court_id=court_choice.court_id,
                                                    date=book_date.isoformat(),
                                                    start_time=selected_slot['start'],
                                                    end_time=extended_end.strftime("%H:%M"),
                                                    team_name=team_name if team_name else None,
                                                ),
                                            )
                                            if booking:
                                                st.success(f"🎉 Booking confirmed! {selected_slot['label']}", icon="✅")
                                                del st.session_state[selected_slot_key]
                                                st.balloons()
                                                st.rerun()
                                    with col2:
                                        if st.form_submit_button("← Change slot", use_container_width=True):
                                            del st.session_state[selected_slot_key]
                                            st.rerun()
                                    with col3:
                                        if st.form_submit_button("Cancel", use_container_width=True):
                                            st.session_state.booking_venue = None
                                            st.rerun()

# --- Tab 2: My Bookings ---
with tab_mybookings:
    st.subheader(f"📅 {acting_as}'s bookings")
    my_bookings = booking_service.list_my_bookings(db, acting_as)

    if not my_bookings:
        st.info("You haven't booked anything yet. Go to **Discover Venues** to find a court!", icon="🎯")
    else:
        # Organize by status
        confirmed = [b for b in my_bookings if b.status == "confirmed"]
        cancelled = [b for b in my_bookings if b.status == "cancelled"]

        if confirmed:
            st.subheader(f"✅ Active Bookings ({len(confirmed)})")
            for b in confirmed:
                with st.container(border=True):
                    cols = st.columns([5, 1])
                    joinable_note = f" · {b.slots_open} slot(s) open" if b.is_joinable else ""
                    team_info = f" · 🎽 {b.team_name}" if b.team_name else ""
                    cols[0].markdown(
                        f"{sport_emoji(b.sport)} **{b.sport}** · {b.date} · {b.start_time}–{b.end_time}{team_info} · "
                        f"{status_text(b.status)}{joinable_note} · `{b.booking_id}`"
                    )
                    if cols[1].button("Cancel", key=f"cancel_{b.booking_id}", use_container_width=True):
                        run(booking_service.cancel_booking, db, b.tenant_id, b.booking_id, acting_as, False)
                        st.rerun()

        if cancelled:
            st.subheader(f"❌ Cancelled Bookings ({len(cancelled)})")
            for b in cancelled:
                with st.container(border=True):
                    st.markdown(
                        f"{sport_emoji(b.sport)} **{b.sport}** · {b.date} · {b.start_time}–{b.end_time} · "
                        f"{status_text(b.status)} · `{b.booking_id}`"
                    )

    st.divider()
    st.subheader(f"Create a venue (as {acting_as})")
    with st.container(border=True), st.form("create_venue"):
        v_name = st.text_input("Venue name", value="SportsOS Demo Arena")
        v_city = st.text_input("City", value="Hyderabad")
        col_lat, col_lng = st.columns(2)
        v_lat = col_lat.number_input("Latitude", value=17.4, format="%.4f")
        v_lng = col_lng.number_input("Longitude", value=78.4, format="%.4f")
        v_sports = st.text_input("Sports (comma-separated)", value="badminton,cricket")
        if st.form_submit_button("Create venue", use_container_width=True):
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
                st.success(f"Created venue {venue.tenant_id}", icon="✅")
                st.rerun()

    st.subheader("Venues & courts management")
    venues_list = list_venues()
    if not venues_list:
        st.info("No venues yet — create one above.", icon="🏗️")
    for venue in venues_list:
        sports_line = " ".join(sport_emoji(s) for s in venue.get("sports", []))
        with st.expander(f"🏟️ {venue['name']} — {venue['city']} {sports_line}"):
            st.caption(f"tenant_id: `{venue['tenant_id']}`")
            courts = court_service.list_courts(db, venue["tenant_id"])
            if courts:
                st.dataframe(
                    [c.model_dump() for c in courts],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "court_id": st.column_config.TextColumn("Court ID"),
                        "name": st.column_config.TextColumn("Name"),
                        "sport": st.column_config.TextColumn("Sport"),
                        "hourly_price": st.column_config.NumberColumn("₹/hr"),
                        "open_time": st.column_config.TextColumn("Opens"),
                        "close_time": st.column_config.TextColumn("Closes"),
                        "is_active": st.column_config.CheckboxColumn("Active"),
                        "tenant_id": None,
                    },
                )
            else:
                st.caption("No courts yet.")

            with st.form(f"add_court_{venue['tenant_id']}"):
                c_name = st.text_input("Court name", value="Court 1", key=f"cname_{venue['tenant_id']}")
                c_sport = st.text_input("Sport", value="badminton", key=f"csport_{venue['tenant_id']}")
                c_price = st.number_input("Hourly price (₹)", value=600.0, key=f"cprice_{venue['tenant_id']}")
                col_open, col_close = st.columns(2)
                c_open = col_open.time_input("Open time", value=time(6, 0), key=f"copen_{venue['tenant_id']}")
                c_close = col_close.time_input("Close time", value=time(23, 0), key=f"cclose_{venue['tenant_id']}")
                c_dynamic = st.checkbox("Enable dynamic pricing (surge 6-9pm, discount 6-9am)", value=False, key=f"cdynamic_{venue['tenant_id']}")
                if st.form_submit_button("Add court", use_container_width=True):
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
                            dynamic_pricing_enabled=c_dynamic,
                        ),
                    )
                    st.rerun()

    # Venue KPIs
    st.divider()
    st.subheader("📊 Venue Analytics")
    owner_venues = [v for v in venues_list if v.get("owner_uid") == acting_as or acting_as in (v.get("roles", {}).get("owner") or [])]
    if owner_venues:
        venue_choice = st.selectbox(
            "Select a venue to view KPIs",
            options=owner_venues,
            format_func=lambda v: f"{v['name']} ({v['tenant_id']})",
            key="kpi_venue"
        )
        try:
            from app.models.kpi import VenueKPIScope
            venue_kpi = kpi_service.get_venue_overview_kpi(db, venue_choice["tenant_id"], VenueKPIScope.TODAY)

            # Revenue
            st.markdown(f"**Today's Revenue:** Rs{venue_kpi.revenue.total_revenue:.0f} ({venue_kpi.revenue.transaction_count} bookings)")

            # Occupancy
            occupancy_col1, occupancy_col2 = st.columns(2)
            occupancy_col1.metric("Average occupancy", f"{venue_kpi.avg_occupancy_percent:.1f}%")
            occupancy_col2.metric("Total active courts", len(venue_kpi.occupancy))

            # Customers
            customer_col1, customer_col2, customer_col3 = st.columns(3)
            customer_col1.metric("Active players", venue_kpi.customers.active_customers)
            customer_col2.metric("New players", venue_kpi.customers.new_customers)
            customer_col3.metric("Repeat %", f"{venue_kpi.customers.repeat_booking_percent:.1f}%")

            # Join Match performance
            st.markdown("**Join Match Queue Performance**")
            match_col1, match_col2, match_col3 = st.columns(3)
            match_col1.metric("Matches formed", venue_kpi.matchmaking.matches_formed)
            match_col2.metric("Fill rate", f"{venue_kpi.matchmaking.match_fill_rate:.1f}%")
            match_col3.metric("Queue cancellations", venue_kpi.matchmaking.queue_cancellations)

            # Court-by-court breakdown
            st.markdown("**Court Utilization**")
            for occ in venue_kpi.occupancy:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    col1.markdown(f"**{occ.court_name}** ({occ.sport})")
                    col2.metric("Utilization", f"{occ.utilization_percent:.1f}%")
                    col3.metric("Bookings", occ.bookings_count)
        except Exception as e:
            st.caption(f"_KPI data not available: {str(e)}_")

# --- Tab 4: Hybrid Booking (captain books a court, then opens leftover slots) ---
with tab_matches:
    st.caption(
        "🤝 A captain books a court first, then opens leftover player slots to the community. "
        "For pure PUBG-style matchmaking with no prior booking, see the **🎮 Join Match (queue)** tab."
    )
    st.subheader(f"Open one of {acting_as}'s bookings to the community")
    my_bookings = [b for b in booking_service.list_my_bookings(db, acting_as) if b.status == "confirmed" and not b.is_joinable]
    if not my_bookings:
        st.info("No confirmed, not-yet-open bookings for this user.", icon="ℹ️")
    else:
        booking_choice = st.selectbox(
            "Booking",
            options=my_bookings,
            format_func=lambda b: f"{sport_emoji(b.sport)} {b.sport} {b.date} {b.start_time}-{b.end_time} ({b.booking_id})",
            key="open_booking",
        )
        slots = st.number_input("Slots to open", min_value=1, value=3, step=1)
        if st.button("Open to community", use_container_width=True):
            run(
                match_service.open_to_community,
                db,
                booking_choice.tenant_id,
                booking_choice.booking_id,
                acting_as,
                OpenToCommunityRequest(slots_open=int(slots)),
            )
            st.rerun()

    st.divider()
    st.subheader("Discover open matches")
    col_sport, col_date = st.columns(2)
    sport_filter = col_sport.text_input("Filter by sport (optional)", key="discover_sport")
    date_filter = col_date.date_input("Filter by date (optional)", value=None, key="discover_date")
    matches = match_service.discover_matches(
        db, sport=sport_filter or None, date=date_filter.isoformat() if date_filter else None
    )
    if not matches:
        st.caption("No open matches right now.")
    for m in matches:
        with st.container(border=True):
            cols = st.columns([5, 1])
            team_info = f" · 🎽 **{m.team_name}**" if m.team_name else ""
            cols[0].markdown(
                f"{sport_emoji(m.sport)} **{m.tenant_name}** · {m.sport} · {m.date} · {m.start_time}–{m.end_time}{team_info} · "
                f"`{m.booking_id}`"
            )

            # Visual slot display (PUBG-style)
            filled = m.slots_total - m.slots_open
            slot_display = ""
            for i in range(m.slots_total):
                if i < filled:
                    slot_display += "🟦"  # Filled slot
                else:
                    slot_display += "⬜"  # Empty slot
            st.markdown(f"**Squad:** {slot_display} `{filled}/{m.slots_total}`")

            if m.created_by != acting_as and cols[1].button("Join", key=f"join_{m.booking_id}", use_container_width=True):
                run(match_service.join_match, db, m.tenant_id, m.booking_id, acting_as)
                st.rerun()

            with st.expander(f"👥 Players ({filled})"):
                st.dataframe([p.model_dump() for p in match_service.list_participants(db, m.tenant_id, m.booking_id)], hide_index=True)

# --- Tab 5: Join Match (queue) — PUBG-style matchmaking, no prior booking ---
with tab_queue:
    st.caption(
        "🎮 No captain, no pre-existing booking: queue for an open slot, and once enough players "
        "(per-sport minimum) queue for the exact same slot, the system forms the match, books "
        "the court, and splits the cost automatically."
    )
    venues = list_venues()
    if not venues:
        st.info("Create a venue and court first (see the Venues & Courts tab).", icon="🏗️")
    else:
        q_venue = st.selectbox(
            "Venue", options=venues, format_func=lambda v: f"{v['name']} ({v['tenant_id']})", key="queue_venue"
        )
        q_courts = court_service.list_courts(db, q_venue["tenant_id"])
        if not q_courts:
            st.info("Add a court to this venue first.", icon="🏗️")
        else:
            q_court = st.selectbox(
                "Court",
                options=q_courts,
                format_func=lambda c: f"{sport_emoji(c.sport)} {c.name} ({c.sport})",
                key="queue_court",
            )
            min_players = matchmaking_service.MIN_PLAYERS.get(q_court.sport, matchmaking_service.DEFAULT_MIN_PLAYERS)
            st.caption(f"Minimum players to form a match for {sport_emoji(q_court.sport)} {q_court.sport}: **{min_players}**")

            q_date = st.date_input("Date", value=date.today(), key="queue_date")

            avail = booking_service.get_availability(db, q_venue["tenant_id"], q_court.court_id, q_date.isoformat())
            requests = matchmaking_service.list_match_requests(db, q_venue["tenant_id"], q_court.court_id, q_date.isoformat())
            queue_counts = {(r.start_time, r.end_time): r.current_count for r in requests if r.status == "waiting"}
            my_queued_slots = {(r.start_time, r.end_time) for r in requests if r.status == "waiting" and r.uid == acting_as}

            def queue_slot_is_booked(start_str, end_str):
                start_min = booking_service.to_minutes(start_str)
                end_min = booking_service.to_minutes(end_str)
                for booked in avail.booked_slots:
                    booked_start = booking_service.to_minutes(booked.start_time)
                    booked_end = booking_service.to_minutes(booked.end_time)
                    if start_min < booked_end and end_min > booked_start:
                        return True
                return False

            with st.container(border=True):
                st.markdown(f"**🎮 Slots for {sport_emoji(q_court.sport)} {q_court.name}** — min **{min_players}** players")
                st.caption(f"Showing slots for {q_date.strftime('%A, %B %d')}")

                slot_cols = st.columns(3)
                for idx, slot in enumerate(generate_hourly_slots(q_court.open_time, q_court.close_time)):
                    col = slot_cols[idx % 3]
                    slot_key = (slot['start'], slot['end'])
                    if queue_slot_is_booked(slot['start'], slot['end']):
                        col.markdown(f":gray[🔴 {slot['label']}]\n:gray[Court booked]")
                    elif slot_key in my_queued_slots:
                        count = queue_counts[slot_key]
                        col.markdown(f"🟦 **{slot['label']}**\nYou're queued · {count}/{min_players}")
                    else:
                        count = queue_counts.get(slot_key, 0)
                        icon = "🟡" if count else "🟢"
                        button_label = f"{count}/{min_players} queued — join" if count else "Start a queue"
                        if col.button(
                            f"{icon} {slot['label']}\n{button_label}",
                            key=f"queue_slot_{q_venue['tenant_id']}_{q_court.court_id}_{q_date.isoformat()}_{slot['start']}",
                            use_container_width=True,
                        ):
                            result = run(
                                matchmaking_service.create_match_request,
                                db,
                                q_venue["tenant_id"],
                                acting_as,
                                MatchRequestCreate(
                                    court_id=q_court.court_id,
                                    date=q_date.isoformat(),
                                    start_time=slot['start'],
                                    end_time=slot['end'],
                                ),
                            )
                            if result:
                                if result.status == "matched":
                                    st.success(
                                        f"🎉 Match formed! Booking {result.matched_booking_id} — you've been charged your share.",
                                        icon="🎉",
                                    )
                                else:
                                    st.success(f"Queued — {result.current_count}/{result.min_players} players so far.", icon="⏳")
                                st.rerun()

                st.caption("🟢 = Start a queue · 🟡 = Join existing queue · 🟦 = You're queued · 🔴 = Court already booked")

            st.divider()
            st.subheader(f"Queue for {sport_emoji(q_court.sport)} {q_court.name} on {q_date.isoformat()}")
            if not requests:
                st.caption("No one queued for this court/date yet.")
            for r in requests:
                with st.container(border=True):
                    cols = st.columns([5, 1])
                    cols[0].markdown(
                        f"{r.start_time}–{r.end_time} · `{r.uid}` · {status_text(r.status)}"
                        + (f" · booking `{r.matched_booking_id}`" if r.matched_booking_id else "")
                    )

                    # Visual slot display (PUBG-style)
                    slot_display = ""
                    for i in range(r.min_players):
                        if i < r.current_count:
                            slot_display += "🟦"  # Filled slot
                        else:
                            slot_display += "⬜"  # Empty slot

                    remaining = r.min_players - r.current_count
                    remaining_text = f"Need **{remaining}** more" if remaining > 0 else "✅ Match ready!"
                    st.markdown(f"**Queue:** {slot_display} `{r.current_count}/{r.min_players}` — {remaining_text}")

                    if r.uid == acting_as and r.status == "waiting" and cols[1].button("Cancel", key=f"cancel_req_{r.request_id}", use_container_width=True):
                        run(matchmaking_service.cancel_match_request, db, q_venue["tenant_id"], r.request_id, acting_as)
                        st.rerun()

# --- Tab 6: Wallet ---
with tab_wallet:
    st.subheader(f"{acting_as}'s wallet")
    wallet = run(wallet_service.get_wallet, db, acting_as)
    if wallet:
        txns = wallet_service.list_transactions(db, acting_as)
        total_credit = sum(t.amount for t in txns if t.type == "credit")
        total_debit = sum(t.amount for t in txns if t.type == "debit")

        col1, col2, col3 = st.columns(3)
        col1.metric("Balance", wallet.balance)
        col2.metric("Total credited", f"₹{total_credit:.0f}")
        col3.metric("Total debited", f"₹{total_debit:.0f}")

        with st.container(border=True), st.form("topup"):
            amount = st.number_input("Top-up amount", min_value=0.0, value=500.0, step=50.0)
            if st.form_submit_button("Top up (demo only, no real payment)", use_container_width=True):
                run(wallet_service.credit_wallet, db, acting_as, amount, "Streamlit demo top-up")
                st.rerun()

        st.subheader("Transaction ledger")
        if not txns:
            st.caption("No transactions yet.")
        else:
            st.dataframe(
                [t.model_dump() for t in txns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "tx_id": None,
                    "type": st.column_config.TextColumn("Type"),
                    "amount": st.column_config.NumberColumn("Amount (₹)"),
                    "reason": st.column_config.TextColumn("Reason"),
                    "related_booking_id": st.column_config.TextColumn("Booking"),
                    "balance_after": st.column_config.NumberColumn("Balance after (₹)"),
                    "created_at": st.column_config.TextColumn("When"),
                },
            )
    else:
        st.info("This user has no wallet — register them as a player first.", icon="👋")
