"""SQLAlchemy ORM models for the sports arena platform."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True, default=_new_uuid)
    display_name = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=False, index=True)
    is_player = Column(Boolean, nullable=False, default=False)
    skill_levels = Column(JSONB, nullable=False, default=dict)   # {sport: "beginner"|"intermediate"|"advanced"|"pro"}
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # Admin auth (venue owners / superadmins only — players never get these set).
    # Provisioned out-of-band by a superadmin; there is no public self-signup for them.
    email = Column(String, unique=True, nullable=True, index=True)
    password_hash = Column(String, nullable=True)
    is_superadmin = Column(Boolean, nullable=False, default=False)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wallet_transactions = relationship("WalletTransaction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    rewards = relationship("Reward", back_populates="user", cascade="all, delete-orphan")


class UserRole(Base):
    """Stores owner/staff roles for a user at a specific tenant."""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    role_type = Column(String, nullable=False)   # 'owner' | 'staff'
    tenant_id = Column(String, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("uid", "role_type", "tenant_id", name="uq_user_role_tenant"),)

    user = relationship("User", back_populates="roles")


# ---------------------------------------------------------------------------
# Tenants (Venues)
# ---------------------------------------------------------------------------

class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True, default=_new_uuid)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False, index=True)
    geo_lat = Column(Float, nullable=False)
    geo_lng = Column(Float, nullable=False)
    sports = Column(JSONB, nullable=False, default=list)   # list[str]
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    amenities = Column(JSONB, nullable=False, default=list)   # list[str]
    cover_image_url = Column(String, nullable=True)
    upi_id = Column(String, nullable=True)          # For direct pay-at-venue bookings
    booking_phone = Column(String, nullable=True)   # WhatsApp/call contact for coordinating a booking
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    courts = relationship("Court", back_populates="tenant", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tenant", cascade="all, delete-orphan")
    match_requests = relationship("MatchRequest", back_populates="tenant", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Courts
# ---------------------------------------------------------------------------

class Court(Base):
    __tablename__ = "courts"

    court_id = Column(String, primary_key=True, default=_new_uuid)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    sport = Column(String, nullable=False, index=True)
    hourly_price = Column(Float, nullable=False)
    open_time = Column(String, nullable=False)    # "HH:MM"
    close_time = Column(String, nullable=False)   # "HH:MM"
    is_active = Column(Boolean, nullable=False, default=True)
    dynamic_pricing_enabled = Column(Boolean, nullable=False, default=False)
    min_players = Column(Integer, nullable=True)  # Queue threshold to auto-confirm a booking; null = sport default

    tenant = relationship("Tenant", back_populates="courts")
    bookings = relationship("Booking", back_populates="court")


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(String, primary_key=True, default=_new_uuid)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False, index=True)
    court_id = Column(String, ForeignKey("courts.court_id", ondelete="RESTRICT"), nullable=False, index=True)
    sport = Column(String, nullable=False)
    date = Column(String, nullable=False, index=True)     # "YYYY-MM-DD"
    start_time = Column(String, nullable=False)           # "HH:MM"
    end_time = Column(String, nullable=False)             # "HH:MM"
    price = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending_payment", index=True)
    created_by = Column(String, ForeignKey("users.uid", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_name = Column(String, nullable=True)
    team_id = Column(String, nullable=True)
    team_name = Column(String, nullable=True)
    is_joinable = Column(Boolean, nullable=False, default=False)
    slots_total = Column(Integer, nullable=False, default=0)
    slots_open = Column(Integer, nullable=False, default=0)
    tenant_name = Column(String, nullable=True)
    geo_lat = Column(Float, nullable=True)
    geo_lng = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="bookings")
    court = relationship("Court", back_populates="bookings")
    participants = relationship("BookingParticipant", back_populates="booking", cascade="all, delete-orphan")
    waitlist = relationship("Waitlist", back_populates="booking", cascade="all, delete-orphan")


class BookingParticipant(Base):
    __tablename__ = "booking_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    display_name = Column(String, nullable=True)
    joined_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("booking_id", "uid", name="uq_booking_participant"),)

    booking = relationship("Booking", back_populates="participants")


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

class Team(Base):
    __tablename__ = "teams"

    team_id = Column(String, primary_key=True, default=_new_uuid)
    team_name = Column(String, nullable=False)
    sport = Column(String, nullable=False, index=True)
    captain_uid = Column(String, ForeignKey("users.uid", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String, nullable=False, default="forming")
    booking_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    created_by = Column(String, nullable=True)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    match_history = relationship("TeamMatchHistory", back_populates="team", cascade="all, delete-orphan")
    stats = relationship("TeamStats", back_populates="team", uselist=False, cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    display_name = Column(String, nullable=True)
    joined_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("team_id", "uid", name="uq_team_member"),)

    team = relationship("Team", back_populates="members")


class TeamMatchHistory(Base):
    __tablename__ = "team_match_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(String, nullable=False)
    booking_id = Column(String, nullable=False)
    opponent_team_id = Column(String, nullable=True)
    opponent_team_name = Column(String, nullable=True)
    result = Column(String, nullable=False)   # 'win' | 'loss' | 'draw'
    player_count = Column(Integer, nullable=False, default=0)
    played_at = Column(String, nullable=False)
    venue_id = Column(String, nullable=True)

    team = relationship("Team", back_populates="match_history")


class TeamStats(Base):
    __tablename__ = "team_stats"

    team_id = Column(String, ForeignKey("teams.team_id", ondelete="CASCADE"), primary_key=True)
    total_matches = Column(Integer, nullable=False, default=0)
    wins = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)
    draws = Column(Integer, nullable=False, default=0)
    win_rate = Column(Float, nullable=False, default=0.0)
    rating = Column(Float, nullable=False, default=1200.0)
    last_match_at = Column(String, nullable=True)

    team = relationship("Team", back_populates="stats")


# ---------------------------------------------------------------------------
# Wallets
# ---------------------------------------------------------------------------

class Wallet(Base):
    __tablename__ = "wallets"

    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), primary_key=True)
    balance = Column(Float, nullable=False, default=0.0)
    currency = Column(String, nullable=False, default="INR")

    user = relationship("User", back_populates="wallet")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    tx_id = Column(String, primary_key=True, default=_new_uuid)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)            # 'credit' | 'debit'
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    reason = Column(String, nullable=False)
    related_booking_id = Column(String, nullable=True)
    balance_after = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="wallet_transactions")


# ---------------------------------------------------------------------------
# Match Requests (PUBG-style matchmaking)
# ---------------------------------------------------------------------------

class MatchRequest(Base):
    __tablename__ = "match_requests"

    request_id = Column(String, primary_key=True, default=_new_uuid)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False, index=True)
    court_id = Column(String, ForeignKey("courts.court_id", ondelete="CASCADE"), nullable=False, index=True)
    sport = Column(String, nullable=False)
    date = Column(String, nullable=False, index=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="waiting")  # waiting | matched | cancelled
    min_players = Column(Integer, nullable=False, default=4)
    matched_booking_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="match_requests")


# ---------------------------------------------------------------------------
# Waitlist
# ---------------------------------------------------------------------------

class Waitlist(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    status = Column(String, nullable=False, default="waiting")  # waiting | promoted | expired

    __table_args__ = (UniqueConstraint("booking_id", "uid", name="uq_waitlist_entry"),)

    booking = relationship("Booking", back_populates="waitlist")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=_new_uuid)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSONB, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class DeviceToken(Base):
    """FCM push-notification device tokens registered by a user's web/Android client."""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String, nullable=False)  # "web" | "android"
    token = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("uid", "token", name="uq_device_token"),)


# ---------------------------------------------------------------------------
# Rewards & Referrals
# ---------------------------------------------------------------------------

class Reward(Base):
    __tablename__ = "rewards"

    reward_id = Column(String, primary_key=True, default=_new_uuid)
    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    reward_type = Column(String, nullable=False)
    credits_amount = Column(Float, nullable=False, default=0.0)
    reason = Column(String, nullable=False)
    issued_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    data = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="rewards")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    referred_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class TeamChallenge(Base):
    __tablename__ = "team_challenges"

    id = Column(String, primary_key=True, default=_new_uuid)
    from_captain_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    to_captain_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | accepted | declined
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------

class Rating(Base):
    __tablename__ = "ratings"

    rating_id = Column(String, primary_key=True, default=_new_uuid)
    from_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    to_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True, default="")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("from_uid", "to_uid", "booking_id", name="uq_rating_booking"),)


# ---------------------------------------------------------------------------
# Match invitations
# ---------------------------------------------------------------------------

class PlayerInvitePreference(Base):
    __tablename__ = "player_invite_preferences"

    uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), primary_key=True)
    open_to_invites = Column(Boolean, nullable=False, default=False)
    radius_km = Column(Float, nullable=False, default=10.0)
    preferred_court_ids = Column(JSONB, nullable=False, default=list)  # [] = any court
    updated_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class MatchInvite(Base):
    __tablename__ = "match_invites"

    invite_id = Column(String, primary_key=True, default=_new_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    from_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    to_uid = Column(String, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False, index=True)
    tier = Column(String, nullable=False)  # "playmate" | "queue" | "nearby"
    status = Column(String, nullable=False, default="pending")  # pending | accepted | declined | expired
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("booking_id", "to_uid", name="uq_match_invite"),)

