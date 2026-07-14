"""Superadmin broadcast notifications — targets a computed audience of uids
(all players, all admins, everyone tied to a sport/court/team, optionally
narrowed by venue or city) and fans a notification out to each of them.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Booking, BookingParticipant, Team, TeamMember, Tenant, User, UserRole
from app.models.broadcast import BroadcastRequest
from app.services import notification_service


def _dedupe(uids: list[str]) -> list[str]:
    return list(dict.fromkeys(uids))


def _uids_from_bookings(
    db: Session, sport: str | None = None, court_id: str | None = None,
    tenant_id: str | None = None, city: str | None = None,
) -> list[str]:
    query = db.query(Booking)
    if sport:
        query = query.filter(Booking.sport == sport)
    if court_id:
        query = query.filter(Booking.court_id == court_id)
    if tenant_id:
        query = query.filter(Booking.tenant_id == tenant_id)
    if city:
        query = query.join(Tenant, Tenant.tenant_id == Booking.tenant_id).filter(Tenant.city.ilike(city))
    bookings = query.all()

    uids = [b.created_by for b in bookings]
    booking_ids = [b.booking_id for b in bookings]
    if booking_ids:
        participants = (
            db.query(BookingParticipant.uid)
            .filter(BookingParticipant.booking_id.in_(booking_ids))
            .all()
        )
        uids += [p[0] for p in participants]
    return _dedupe(uids)


def resolve_audience(db: Session, req: BroadcastRequest) -> list[str]:
    if req.target == "all_players":
        query = db.query(User.uid).filter(User.is_player == True)
        if req.tenant_id or req.city:
            scoped_uids = _uids_from_bookings(db, tenant_id=req.tenant_id, city=req.city)
            query = query.filter(User.uid.in_(scoped_uids))
        return [r[0] for r in query.all()]

    if req.target == "all_admins":
        query = db.query(User.uid).filter(User.password_hash.isnot(None))
        if req.tenant_id:
            query = query.join(UserRole, UserRole.uid == User.uid).filter(UserRole.tenant_id == req.tenant_id)
        return _dedupe([r[0] for r in query.all()])

    if req.target == "sport":
        if not req.sport:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sport is required for target=sport")
        return _uids_from_bookings(db, sport=req.sport, tenant_id=req.tenant_id, city=req.city)

    if req.target == "court":
        if not req.court_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="court_id is required for target=court")
        return _uids_from_bookings(db, court_id=req.court_id)

    if req.target == "team":
        if not req.team_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="team_id is required for target=team")
        uids = [r[0] for r in db.query(TeamMember.uid).filter(TeamMember.team_id == req.team_id).all()]
        team = db.query(Team).filter(Team.team_id == req.team_id).first()
        if team:
            uids.append(team.captain_uid)
        return _dedupe(uids)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown broadcast target")


def send_broadcast(db: Session, req: BroadcastRequest) -> int:
    uids = resolve_audience(db, req)
    for uid in uids:
        notification_service.record_notification(db, uid, "platform_announcement", req.title, req.body, {})
    db.commit()
    return len(uids)
