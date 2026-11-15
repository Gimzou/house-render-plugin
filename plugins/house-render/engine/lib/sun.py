"""Solar position (NOAA-style low-precision formulae, ~0.1 deg) and model-space sun vector. Pure Python.

Azimuth is a compass bearing (0 = N, 90 = E, clockwise). Model axes: +Y points to the garden
bearing (<level>.json orientation.plan_up_bearing_deg; legacy garden_bearing_deg), +X is 90 deg clockwise from +Y.
"""
import math
from datetime import datetime, timezone, timedelta


def julian_day(dt_utc):
    return dt_utc.timestamp() / 86400.0 + 2440587.5


def sun_position(lat, lon, dt_utc):
    """Return (azimuth_deg, elevation_deg) for a timezone-aware UTC datetime."""
    n = julian_day(dt_utc) - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    ha = math.radians((gmst + lon / 15.0) * 15.0) - ra
    la = math.radians(lat)
    el = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha))
    az = math.atan2(-math.sin(ha), math.tan(dec) * math.cos(la) - math.sin(la) * math.cos(ha))
    return math.degrees(az) % 360, math.degrees(el)


def local_to_utc(date_str, time_str, utc_offset_h):
    dt = datetime.fromisoformat(f"{date_str}T{time_str}")
    return (dt - timedelta(hours=utc_offset_h)).replace(tzinfo=timezone.utc)


def model_vector(azimuth_deg, elevation_deg, garden_bearing_deg):
    """Unit vector from the house toward the sun, in model coordinates."""
    d = math.radians(azimuth_deg - garden_bearing_deg)
    h = math.radians(elevation_deg)
    return (math.sin(d) * math.cos(h), math.cos(d) * math.cos(h), math.sin(h))


if __name__ == "__main__":  # self-test: python3 src/lib/sun.py
    def noon_el(date):
        best = max((sun_position(50.84, 4.42, local_to_utc(date, f"{h:02d}:{m:02d}", 1))[1], h, m)
                   for h in range(11, 15) for m in range(0, 60, 2))
        return best
    for date, want in (("2026-03-20", 39.3), ("2026-06-21", 62.6), ("2026-12-21", 15.7)):
        el, h, m = noon_el(date)
        print(f"{date}: max elevation {el:.1f} (want ~{want}) at {h}:{m:02d} UTC+1")
        assert abs(el - want) < 0.7
    az, el = sun_position(50.84, 4.42, local_to_utc("2026-03-20", "12:50", 1))
    print(f"equinox 12:50 CET: az {az:.1f} el {el:.1f}")
    assert abs(az - 180) < 2
    print("OK")
