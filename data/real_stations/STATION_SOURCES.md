# Real Station Data — Sources & Caveats

Source: [NOAA Integrated Surface Database (ISD-Lite)](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/),
NOAA National Centers for Environmental Information. Public domain (U.S. Government work).
Format spec: [isd-lite-format.txt](https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt).

Regenerate with:
```bash
python data/real_stations/fetch_and_process.py
```

## Station mapping

| SkyGuard profile | Real station | NOAA ID | Coordinates | Elevation | Years |
|---|---|---|---|---|---|
| `AWS_GAMMA_URBAN` | Safdarjung, Delhi, India | 421820-99999 | 28.585N, 77.206E | 214.9m | 2021-2023 |
| `AWS_BETA_COASTAL` | Bombay/Colaba, India | 430570-99999 | 18.900N, 72.817E | 11.0m | 2021-2023 |
| `AWS_DELTA_DESERT` | Jaisalmer, India | 423280-99999 | 26.900N, 70.917E | 231.0m | 2021-2023 |
| `AWS_ALPHA_MOUNTAIN` | Flagstaff Pulliam Airport, AZ, USA (KFLG) | 723750-03103 | 35.144N, -111.666W | 2133.3m | 2021-2023 |

Delhi, Mumbai, and Jaisalmer are near-exact lat/lon matches to the synthetic profiles
already defined in [`backend/app/core/config.py`](../../backend/app/core/config.py).

## Why the mountain station isn't Indian

Every high-elevation Indian station checked against ISD-Lite — Shimla, Leh/VILH,
Kodaikanal, Udhagamandalam, even Kempegowda Intl./VOBL (Bangalore, 915m) — reports
Sea Level Pressure as missing (`-9999`) in **every** record. This isn't a download
issue; it appears to be a systematic gap in how the India Meteorological Department's
feed reaches NOAA's global ingestion for this specific field. Since pressure is one
of the three parameters this whole project is about, a station missing it entirely
isn't usable. Flagstaff, AZ (KFLG) was used instead: a US ASOS station with >99%
complete SLP reporting, elevation within 1% of the synthetic profile's 2150m, and in
the same semi-arid mountain climate class the original fictional profile coordinate
(34.1N, -117.8W, Southern California) was modeling.

## Two caveats that matter if you extend this

1. **Pressure is Sea Level Pressure (SLP), not station-level pressure.** ISD-Lite
   only provides SLP — the barometric reduction to what pressure *would* read at sea
   level, which is the standard convention for cross-station synoptic comparison. All
   four real datasets sit in the same ~980-1035 hPa band regardless of station
   elevation, including Flagstaff at 2133m. This does **not** match the synthetic
   generator's per-station flat baselines in `config.py` (e.g. 785 hPa for the mountain
   profile, representing un-reduced station-level pressure at altitude). Both
   conventions are individually valid and internally consistent, but they are not the
   same number and shouldn't be compared directly. The isolation forest and
   autoencoder pretraining blend real + synthetic data specifically so the models
   accept both ranges rather than flagging one as anomalous relative to the other.

2. **Relative Humidity is derived, not measured.** ISD-Lite provides Temperature and
   Dew Point, not RH directly. RH is computed here via
   `100 * e_s(T_dewpoint) / e_s(T_air)` using the project's own Magnus-Tetens
   saturation curve (`backend/app/core/physics.py`), so every derived row is
   thermodynamically self-consistent by construction — dew point can never exceed air
   temperature in this data, because it's derived from air temperature. Real
   instrument RH readings would carry their own independent sensor noise that this
   derivation cannot reproduce.
