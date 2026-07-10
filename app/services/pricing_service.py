"""Dynamic pricing based on demand (peak hours, occupancy)."""

from datetime import datetime

from app.core.db import Client, FieldFilter
from app.services import booking_service


def _get_peak_hours_heatmap(db: Client, tenant_id: str) -> dict[str, int]:
    """Get booking heatmap by hour for this venue."""
    bookings = booking_service.list_bookings(db, tenant_id)
    hour_counts = {}
    for booking in bookings:
        if booking.status != "confirmed":
            continue
        try:
            start_h = int(booking.start_time.split(":")[0])
            hour_counts[f"{start_h:02d}:00"] = hour_counts.get(f"{start_h:02d}:00", 0) + 1
        except (ValueError, IndexError):
            pass
    return hour_counts


def get_dynamic_price(
    db: Client,
    tenant_id: str,
    court_id: str,
    date: str,
    start_time: str,
    base_hourly_price: float,
) -> float:
    """
    Calculate dynamic price based on:
    - Peak hours (6-9pm are premium, 6-9am are discount)
    - Court occupancy (high demand = higher price)

    Returns adjusted hourly price.
    """

    # Get peak-hours heatmap for this venue
    peak_hours = _get_peak_hours_heatmap(db, tenant_id)

    # Extract hour from start_time (HH:MM format)
    try:
        hour = int(start_time.split(":")[0])
        hour_str = f"{hour:02d}:00"
    except (ValueError, IndexError):
        return base_hourly_price

    # Get bookings count at this hour (from peak_hours heatmap)
    bookings_at_hour = peak_hours.get(hour_str, 0)
    if bookings_at_hour == 0:
        bookings_at_hour = 1  # Avoid division by zero

    # Prime time surcharge: 6-9pm (18:00-21:00) = 1.3x, 12-2pm (12:00-14:00) = 1.15x
    time_multiplier = 1.0
    if 18 <= hour < 21:
        time_multiplier = 1.3  # Evening is premium
    elif 12 <= hour < 14:
        time_multiplier = 1.15  # Lunch hour surcharge
    elif 6 <= hour < 9:
        time_multiplier = 0.85  # Early morning discount

    # Occupancy-based multiplier
    # If this hour is booked by many courts, increase price
    # Normalize: assume max of 10 bookings in an hour = 2x price
    occupancy_multiplier = 1.0 + min(bookings_at_hour / 10, 1.0)

    dynamic_price = base_hourly_price * time_multiplier * occupancy_multiplier
    return round(dynamic_price, 2)


def should_use_dynamic_pricing(db: Client, tenant_id: str, court_id: str) -> bool:
    """Check if dynamic pricing is enabled for this court."""
    # Get court doc and check if dynamic_pricing flag is set
    try:
        doc = db.collection("tenants").document(tenant_id).collection("courts").document(court_id).get()
        if doc.exists:
            return doc.to_dict().get("dynamic_pricing_enabled", False)
    except Exception:
        pass
    return False


def explain_dynamic_price(
    db: Client,
    tenant_id: str,
    court_id: str,
    date: str,
    start_time: str,
    base_hourly_price: float,
) -> dict:
    """
    Return price breakdown for transparency.
    Shows base price, time multiplier, occupancy multiplier.
    """
    try:
        hour = int(start_time.split(":")[0])
        hour_str = f"{hour:02d}:00"
    except (ValueError, IndexError):
        return {
            "base_price": base_hourly_price,
            "time_multiplier": 1.0,
            "occupancy_multiplier": 1.0,
            "final_price": base_hourly_price,
            "reason": "Could not parse time",
        }

    peak_hours = _get_peak_hours_heatmap(db, tenant_id)
    bookings_at_hour = peak_hours.get(hour_str, 0) or 1

    time_multiplier = 1.0
    time_reason = "Base rate"
    if 18 <= hour < 21:
        time_multiplier = 1.3
        time_reason = "Prime time (6-9pm): +30%"
    elif 12 <= hour < 14:
        time_multiplier = 1.15
        time_reason = "Lunch hour: +15%"
    elif 6 <= hour < 9:
        time_multiplier = 0.85
        time_reason = "Early morning: -15%"

    occupancy_multiplier = 1.0 + min(bookings_at_hour / 10, 1.0)
    occ_reason = f"Occupancy ({bookings_at_hour} courts booked): {(occupancy_multiplier - 1) * 100:.0f}% surge"

    final_price = base_hourly_price * time_multiplier * occupancy_multiplier

    return {
        "base_price": base_hourly_price,
        "time_multiplier": time_multiplier,
        "time_reason": time_reason,
        "occupancy_multiplier": round(occupancy_multiplier, 2),
        "occupancy_reason": occ_reason,
        "final_price": round(final_price, 2),
    }
