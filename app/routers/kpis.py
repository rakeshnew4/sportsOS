"""KPI and analytics API endpoints — measure what matters."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.kpi import (
    PlayerEngagementKPI, PlatformAdminKPI, PlayerKPIScope, VenueKPIScope, VenueOverviewKPI,
    CaptainRewardMetric, CreditsMetric, TeamNetworkMetric, ReferralMetric, MatchCompletionMetric
)
from app.services import kpi_service

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/venues/{tenant_id}/overview", response_model=VenueOverviewKPI)
def get_venue_overview(tenant_id: str, scope: VenueKPIScope = VenueKPIScope.TODAY, db: Session = Depends(get_db)) -> VenueOverviewKPI:
    """
    Venue north-star KPIs: daily revenue, court occupancy, customer activity, Join Match queue health.

    Shows: total revenue, bookings count, court-by-court utilization %, active players, repeat rate,
    queue matches formed, fill rate.
    """
    try:
        return kpi_service.get_venue_overview_kpi(db, tenant_id, scope)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/players/{uid}/engagement", response_model=PlayerEngagementKPI)
def get_player_engagement(uid: str, scope: PlayerKPIScope = PlayerKPIScope.MONTH, db: Session = Depends(get_db)) -> PlayerEngagementKPI:
    """
    Player north-star metrics: matches played, hours, total spend, wallet balance, favorite venues/sports,
    retention indicators.

    Shows: everything a player needs to see about their activity and impact.
    """
    try:
        return kpi_service.get_player_engagement_kpi(db, uid, scope)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/platform/admin", response_model=PlatformAdminKPI)
def get_platform_admin_kpi(db: Session = Depends(get_db)) -> PlatformAdminKPI:
    """
    System-wide health dashboard: DAU, MAU, GMV, MRR/ARR, retention, churn.

    Restricted to admin users (will be gated by auth in production).
    Shows: business health, growth metrics, payment health, player retention trends.
    """
    try:
        return kpi_service.get_platform_admin_kpi(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/platform/credits", response_model=CreditsMetric)
def get_credits_kpi(db: Session = Depends(get_db)) -> CreditsMetric:
    """SportsOS Credits system metrics: issued, redeemed, outstanding, redemption rate, ROI."""
    try:
        return kpi_service.get_credits_metric(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/platform/teams", response_model=TeamNetworkMetric)
def get_team_network_kpi(db: Session = Depends(get_db)) -> TeamNetworkMetric:
    """Team network metrics: team count, team-vs-team matches, challenge acceptance rate, maturity."""
    try:
        return kpi_service.get_team_network_metric(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/platform/referrals", response_model=ReferralMetric)
def get_referral_kpi(db: Session = Depends(get_db)) -> ReferralMetric:
    """Referral metrics: new players, referral rate, LTV of referred players, top referrer."""
    try:
        return kpi_service.get_referral_metric(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/platform/match-completion", response_model=MatchCompletionMetric)
def get_match_completion_kpi(db: Session = Depends(get_db)) -> MatchCompletionMetric:
    """Match quality metrics: completion rate, no-show rate, dispute rate, rewards issued."""
    try:
        return kpi_service.get_match_completion_metric(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/players/me/captain", response_model=CaptainRewardMetric)
def get_my_captain_reward_kpi(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> CaptainRewardMetric:
    """Get my own captain reward metrics."""
    try:
        return kpi_service.get_captain_reward_metric(db, user.uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")


@router.get("/players/{uid}/captain", response_model=CaptainRewardMetric)
def get_captain_reward_kpi(uid: str, db: Session = Depends(get_db)) -> CaptainRewardMetric:
    """Captain-specific reward metrics: credits earned, matches hosted, new players brought, acceptance rate."""
    try:
        return kpi_service.get_captain_reward_metric(db, uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")
