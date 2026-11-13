import math
from datetime import date

INVALID_DATE_MSG = "Pass Expiry: INVALID (expected YYYY/MM/DD)"


def parse_season_pass_validity(date_str):
    """Parse 'YYYY/MM/DD' and report whether the pass is VALID or EXPIRED.

    Returns a descriptive message (never raises) for None, non-string,
    empty, malformed, non-numeric or impossible calendar dates.
    """
    if not isinstance(date_str, str):
        return INVALID_DATE_MSG

    parts = date_str.strip().split('/')
    if len(parts) != 3:
        return INVALID_DATE_MSG

    try:
        year, month, day = (int(p) for p in parts)
        date(year, month, day)          # rejects 2026/02/30, month 13, year 0, ...
    except (ValueError, OverflowError):
        return INVALID_DATE_MSG

    valid = year >= 2026
    return f"Pass Expiry: {year:04d}-{month:02d}-{day:02d} ({'VALID' if valid else 'EXPIRED'})"


def compute_trail_gradient(elevation_str):
    """Compute gradient % from 'drop:distance'.

    Returns None for any invalid input (None, wrong format, non-numeric,
    NaN/inf, zero or negative distance, or an overflowing result).
    """
    if not isinstance(elevation_str, str):
        return None

    parts = elevation_str.split(':')
    if len(parts) != 2:
        return None

    try:
        drop = float(parts[0])
        distance = float(parts[1])
    except (ValueError, OverflowError):
        return None

    if not (math.isfinite(drop) and math.isfinite(distance)) or distance <= 0:
        return None

    try:
        gradient_pct = (drop / distance) * 100.0
    except (ZeroDivisionError, OverflowError):
        return None

    if not math.isfinite(gradient_pct):
        return None
    return round(gradient_pct, 2)


ZONE_RATES = {
    "BEG": 35.0,
    "INT": 60.0,
    "ADV": 85.0,
    "ALL": 110.0,
}


def calculate_lift_access_tier(zone_code):
    """Return the lift price for a zone code (BEG/INT/ADV/ALL prefix).

    Returns None for None, non-string, empty or unknown zone codes.
    """
    if not isinstance(zone_code, str):
        return None
    prefix = zone_code.strip().upper()[:3]
    return ZONE_RATES.get(prefix)


def main():
    print("==== Running parse_season_pass_validity ====")
    d_input = input("Enter pass expiry (YYYY/MM/DD): ")
    print(parse_season_pass_validity(d_input))

    print("\n==== Running compute_trail_gradient ====")
    e_input = input("Enter drop:distance (e.g. 250:1000): ")
    gradient = compute_trail_gradient(e_input)
    print("Gradient %:", gradient if gradient is not None else "Invalid input (expected drop:distance, distance > 0)")

    print("\n==== Running calculate_lift_access_tier ====")
    z_input = input("Enter zone code (e.g. BEG, INT, ALL): ")
    price = calculate_lift_access_tier(z_input)
    if price is None:
        print("Lift Pass Price: Invalid zone code (use BEG, INT, ADV or ALL)")
    else:
        print("Lift Pass Price: $", price)


if __name__ == "__main__":
    main()
