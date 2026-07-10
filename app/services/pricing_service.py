"""Dynamic pricing based on demand (peak hours, occupancy) — PostgreSQL-backed."""

from sqlalchemy.orm import Session

from app.db.orm import Booking, Court


def _get_peak_hours_heatmap(db: Session, tenant_id: str) -> dict[str, int]:
    bookings = db.query(Booking).filter(Booking.tenant_id == tenant_id, Booking.status == "confirmed").all()
    hour_counts: dict[str, int] = {}
    for b in bookings:
        try:
            start_h = int(b.start_time.split(":")[0])
            key = f"{start_h:02d}:00"
            hour_counts[key] = hour_counts.get(key, 0) + 1
        except (ValueError, IndexError):
            pass
    return hour_counts


def get_dynamic_price(
    db: Session, tenant_id: str, court_id: str, date: str, start_time: str, base_hourly_price: float,
) -> float:
    peak_hours = _get_peak_hours_heatmap(db, tenant_id)
    try:
        hour = int(start_time.split(":")[0])
        hour_str = f"{hour:02d}:00"
    except (ValueError, IndexError):
        return base_hourly_price

    bookings_at_hour = max(peak_hours.get(hour_str, 0), 1)
    time_multiplier = 1.0
    if 18 <= hour < 21:
        time_multiplier = 1.3
    elif 12 <= hour < 14:
        time_multiplier = 1.15
    elif 6 <= hour < 9:
        time_multiplier = 0.85
    occupancy_multiplier = 1.0 + min(bookings_at_hour / 10, 1.0)
    return round(base_hourly_price * time_multiplier * occupancy_multiplier, 2)


def should_use_dynamic_pricing(db: Session, tenant_id: str, court_id: str) -> bool:
    try:
        court = db.query(Court).filter(Court.court_id == court_id, Court.tenant_id == tenant_id).first()
        return bool(court and court.dynamic_pricing_enabled)
    except Exception:
        return False


def explain_dynamic_price(db: Session, tenant_id: str, court_id: str, date: str, start_time: str, base_hourly_price: float) -> dict:
    try:
        hour = int(start_time.split(":")[0])
    except (ValueError, IndexError):
        return {"base_price": base_hourly_price, "final_price": base_hourly_price}

    peak_hours = _get_peak_hours_heatmap(db, tenant_id)
    bookings_at_hour = max(peak_hours.get(f"{hour:02d}:00", 0), 1)
    time_multiplier = 1.0
    if 18 <= hour < 21:
        time_multiplier = 1.3
    elif 12 <= hour < 14:
        time_multiplier = 1.15
    elif 6 <= hour < 9:
        time_multiplier = 0.85
    occupancy_multiplier = 1.0 + min(bookings_at_hour / 10, 1.0)
    final = round(base_hourly_price * time_multiplier * occupancy_multiplier, 2)
    return {
        "base_price": base_hourly_price,
        "time_multiplier": time_multiplier,
        "occupancy_multiplier": round(occupancy_multiplier, 2),
        "final_price": final,
    }
