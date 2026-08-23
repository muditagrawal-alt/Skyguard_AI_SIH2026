"""
SkyGuard AI - Real Historical AWS Data Acquisition (NOAA ISD-Lite)
Downloads real hourly surface observations from NOAA's Integrated Surface Database
(ISD-Lite) for four real stations chosen to match SkyGuard's synthetic station
profiles, derives Relative Humidity from Temperature + Dew Point using the project's
own Magnus-Tetens physics engine, and writes clean per-station CSVs that the model
training code and the real-data benchmark consume.

NOAA ISD data is produced by a U.S. government agency (NOAA/NCEI) and is in the
public domain. Source: https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/

Run:
    python data/real_stations/fetch_and_process.py
"""

import sys
import gzip
import io
from pathlib import Path
from datetime import datetime, timezone

import urllib.request

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.physics import physics_engine  # noqa: E402

RAW_DIR = Path(__file__).resolve().parent / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent / "processed"
ISD_LITE_BASE = "https://www.ncei.noaa.gov/pub/data/noaa/isd-lite"

# Real NOAA ISD stations chosen as physical analogs of SkyGuard's synthetic profiles.
# Safdarjung, Colaba, and Jaisalmer are near-exact lat/lon matches to the profiles
# already defined in backend/app/core/config.py.
#
# The mountain profile could NOT be matched to a real Indian hill station: every
# Himalayan/Western Ghats station checked (Shimla, Leh/VILH, Kodaikanal, Ooty, even
# Bangalore Intl/VOBL at 915m) reports Sea Level Pressure as -9999 (missing) in every
# ISD-Lite record -- India's high-elevation network apparently does not publish a
# barometric SLP reduction through NOAA's feed. Flagstaff, AZ (KFLG, elev. 2133m) is
# used instead: a US ASOS station with >99% complete SLP reporting, at an elevation
# within 1% of the synthetic profile's 2150m, in the same semi-arid mountain climate
# class as the original (fictional) 34.1N/-117.8W California profile coordinate.
STATION_MAP = {
    "AWS_ALPHA_MOUNTAIN": {"noaa_id": "723750-03103", "real_name": "Flagstaff Pulliam Airport, AZ, USA (KFLG)", "years": [2021, 2022, 2023]},
    "AWS_BETA_COASTAL": {"noaa_id": "430570-99999", "real_name": "Bombay/Colaba, India", "years": [2021, 2022, 2023]},
    "AWS_GAMMA_URBAN": {"noaa_id": "421820-99999", "real_name": "Safdarjung (Delhi), India", "years": [2021, 2022, 2023]},
    "AWS_DELTA_DESERT": {"noaa_id": "423280-99999", "real_name": "Jaisalmer, India", "years": [2021, 2022, 2023]},
}

MISSING = -9999


def _download_year(noaa_id: str, year: int) -> bytes:
    url = f"{ISD_LITE_BASE}/{year}/{noaa_id}-{year}.gz"
    dest = RAW_DIR / f"{noaa_id}-{year}.gz"
    if dest.exists():
        return dest.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "SkyGuardAI-research/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return data


def _parse_isd_lite(raw_gz_bytes: bytes):
    """
    Parses ISD-Lite fixed-width records (whitespace-delimited in practice).
    Fields: year month day hour airtemp(x10C) dewpoint(x10C) sea_level_pressure(x10hPa) ...
    Missing values are coded -9999. Returns list of dicts with year/month/day/hour/
    temp_c/dewpoint_c/pressure_hpa, skipping any record missing temp, dewpoint, or pressure.
    """
    records = []
    with gzip.open(io.BytesIO(raw_gz_bytes), mode="rt") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 7:
                continue
            year, month, day, hour = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            temp_raw, dew_raw, slp_raw = int(parts[4]), int(parts[5]), int(parts[6])
            if temp_raw == MISSING or dew_raw == MISSING or slp_raw == MISSING:
                continue

            temp_c = temp_raw / 10.0
            dewpoint_c = dew_raw / 10.0
            pressure_hpa = slp_raw / 10.0  # NOAA ISD reports Sea Level Pressure (SLP)

            # Physical sanity: dew point can never exceed air temperature. A handful of
            # ISD records violate this by a few tenths of a degree due to instrument/
            # rounding noise; clamp rather than propagate an already-invalid "clean" row.
            if dewpoint_c > temp_c:
                dewpoint_c = temp_c

            # Derive Relative Humidity from T and Td using the SAME Magnus-Tetens
            # saturation curve used everywhere else in the pipeline, so every derived
            # row is thermodynamically self-consistent by construction:
            #   RH = 100 * e_s(Td) / e_s(T)
            e_s_t = physics_engine.saturation_vapor_pressure(temp_c)
            e_s_td = physics_engine.saturation_vapor_pressure(dewpoint_c)
            humidity_pct = max(0.0, min(100.0, 100.0 * (e_s_td / e_s_t)))

            records.append({
                "timestamp": datetime(year, month, day, hour, tzinfo=timezone.utc).isoformat(),
                "temperature_c": round(temp_c, 2),
                "pressure_hpa": round(pressure_hpa, 2),
                "humidity_pct": round(humidity_pct, 2),
            })
    return records


def build_station_dataset(station_id: str, spec: dict) -> int:
    all_records = []
    for year in spec["years"]:
        try:
            raw_bytes = _download_year(spec["noaa_id"], year)
        except Exception as e:
            print(f"  [WARN] {station_id} {year}: download failed ({e}), skipping this year")
            continue
        year_records = _parse_isd_lite(raw_bytes)
        all_records.extend(year_records)
        print(f"  {station_id} {year}: {len(year_records)} valid hourly observations")

    all_records.sort(key=lambda r: r["timestamp"])

    out_path = PROCESSED_DIR / f"{station_id}.csv"
    with open(out_path, "w") as f:
        f.write("timestamp,temperature_c,pressure_hpa,humidity_pct\n")
        for r in all_records:
            f.write(f"{r['timestamp']},{r['temperature_c']},{r['pressure_hpa']},{r['humidity_pct']}\n")

    print(f"  -> Wrote {len(all_records)} rows to {out_path.relative_to(PROJECT_ROOT)}")
    return len(all_records)


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Fetching real NOAA ISD-Lite station data for SkyGuard AI")
    print("=" * 70)

    total = 0
    for station_id, spec in STATION_MAP.items():
        print(f"\n[{station_id}] real analog: {spec['real_name']} (NOAA {spec['noaa_id']})")
        total += build_station_dataset(station_id, spec)

    print("\n" + "=" * 70)
    print(f"Done. {total} total real observations across {len(STATION_MAP)} stations.")
    print("=" * 70)


if __name__ == "__main__":
    main()
