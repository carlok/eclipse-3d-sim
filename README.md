# Eclipse sightline — 12 August 2026

A local web app that computes the circumstances of the 12 August 2026 solar eclipse for a chosen observer position, then checks whether the solar disc clears the local horizon — a horizon built from manual points, manually entered obstacles (buildings, trees, cranes) and, optionally, terrain ray-cast from a digital elevation model (DEM).

It is a FastAPI backend (Python) plus a React/Vite frontend with a Leaflet map, a 2D Sun/Moon diagram, a Sun-path chart and a three.js observer-eye view.

> **Never observe the Sun directly without certified solar viewing protection, except during the brief total phase at a location inside the path of totality. High obscuration does not make unfiltered viewing safe.**

## What it does

- **Local eclipse circumstances.** For a latitude, longitude, elevation and timezone, the backend returns the eclipse type, contact times C1–C4 and maximum (UTC and local time, with solar altitude), and the Sun/Moon state at maximum.
- **Time track.** Optionally, the Sun/Moon state sampled every `sample_seconds` (1–300 s) from C1 to C4.
- **Horizon analysis.** Each track sample is classified against the combined horizon as `clear`, `partially_blocked`, `fully_blocked` or `below_astronomical_horizon`. The response includes the clear sample with the highest obscuration and the partially visible sample with the highest obscuration.
- **Terrain-corrected sunset.** Compares flat-horizon sunset with the time the lower solar limb drops below the terrain/obstacle horizon, and warns when the combined horizon hides the full disc at least a minute early.
- **Terrain horizon from a DEM.** Ray-casts a local GeoTIFF, or downloads a Copernicus 30 m DEM (COP30) from OpenTopography around the observer and ray-casts that.
- **Browser UI.** Pick the observer on a map (click, drag the marker, or use browser geolocation), play back the eclipse, edit horizon points and obstacles, import/export them as JSON, and open a full-screen 3D view toward the Sun at maximum obscuration.

## How it works

### Astronomy (`backend/app/astronomy.py`)

- Uses [Astronomy Engine](https://github.com/cosinekitty/astronomy) (`astronomy-engine`). `SearchLocalSolarEclipse`, starting from 2026-08-12 00:00 UTC, provides the eclipse kind and the contact events.
- For each instant, topocentric Sun and Moon equatorial coordinates are converted to azimuth/altitude. Sun altitude is reported both **apparent** (with normal atmospheric refraction) and **geometric** (airless). Visibility decisions use apparent altitude.
- Angular radii come from the body radii (Sun 695,700 km, Moon 1,737.4 km) and the current distances.
- **Magnitude** is the fraction of the solar diameter covered: `(r_sun + r_moon − separation) / (2 · r_sun)`, clamped to 0–1.5.
- **Obscuration** is the fraction of the solar disc's area covered, from the circle–circle overlap area. It is the main coverage percentage shown in the UI.
- The Moon's position relative to the Sun is also returned as right/up offsets and a position angle, which the frontend uses to draw the discs.
- If no timezone is supplied, one is looked up from the coordinates with `timezonefinder` (falling back to UTC).

### Horizon and visibility (`backend/app/horizon.py`)

- **Horizon profile**: a list of `(azimuth_deg, altitude_deg)` points, linearly interpolated in azimuth with wrap-around at north.
- **Obstacles**: azimuth arcs (which may wrap through north) with a top altitude. The effective horizon at an azimuth is the maximum of the interpolated profile and every enabled obstacle covering it.
- **Classification** compares the solar limbs with the effective horizon plus a safety margin (default 0.1°):
  - `clear` — the lower limb is above horizon + margin;
  - `fully_blocked` — the upper limb is at or below horizon + margin;
  - `partially_blocked` — anything in between;
  - `below_astronomical_horizon` — the upper limb is below 0° altitude.
- **Sunset**: the Sun is stepped minute by minute through the local day and the lower-limb crossing is refined by bisection, once with a flat horizon and once with the profile, obstacles and margin.

### Terrain (`backend/app/horizon.py`, `backend/app/opentopography.py`)

- For each azimuth step, points are sampled outward along the great circle every `distance_step_m` up to `max_distance_km`. The elevation angle of each DEM sample is computed with a spherical-Earth curvature correction (R = 6,371 km); the maximum angle along the ray becomes the horizon altitude for that azimuth. No-data cells are skipped. The DEM is sampled at longitude/latitude, so it must be a GeoTIFF in geographic WGS84 coordinates.
- The download endpoint requests a COP30 GeoTIFF for the bounding box around the observer from the OpenTopography Global DEM API. It checks that the response is a TIFF and caches it in `TERRAIN_CACHE_DIR` (keyed by coordinates and radius). Areas crossing the antimeridian are rejected. The API key stays on the backend.

## Requirements

- Python 3.11 or newer (the Docker image uses 3.12), with the packages in `backend/requirements.txt`: FastAPI, Uvicorn, astronomy-engine, timezonefinder, NumPy, rasterio, python-dotenv (plus pytest and httpx for the tests).
- Node.js 22 (the version used by the frontend Docker image) and npm.
- A browser with WebGL for the 3D view. The map loads OpenStreetMap tiles, so it needs internet access.
- Optional: a WGS84 GeoTIFF DEM, or an [OpenTopography](https://opentopography.org/) API key for automatic DEM downloads.

## Running

### Directly

```bash
# Backend, on http://localhost:8000
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend, on http://localhost:5173 (in a second terminal)
cd frontend
npm install
npm run dev
```

### With Docker Compose

```bash
docker compose up --build
```

This starts the backend on port 8000 and the frontend on port 5173. `./data/dem` is mounted **read-only** at `/data/dem`, and the backend reads `/data/dem/terrain.tif` as its local DEM. The OpenTopography download cache is written to `TERRAIN_CACHE_DIR`, which inside this container resolves to the read-only mount by default. For DEM downloads, use the direct setup or point `TERRAIN_CACHE_DIR` at a writable location.

### Configuration

Environment variables (see `.env.example`). The backend also loads a `.env` file via python-dotenv, for example `backend/.env`.

| Variable | Used for | Default |
|---|---|---|
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:5173` |
| `TERRAIN_DEM_PATH` | Local GeoTIFF for `terrain-horizon` | none (endpoint returns 503) |
| `OPENTOPOGRAPHY_API_KEY` | Enables `terrain-download` | none (endpoint returns 502) |
| `TERRAIN_CACHE_DIR` | Where downloaded DEMs are cached | `<repo>/data/dem/cache` |
| `VITE_API_BASE_URL` (frontend) | Backend base URL | `http://localhost:8000/api` |

### Tests

```bash
cd backend && pytest        # API, horizon, classification and GeoTIFF ray-casting tests
cd frontend && npm test     # vitest
```

## Using the app

1. Choose the observer: click the map, drag the marker, type coordinates, or press **Use my location**. The last observer is remembered in the browser.
2. Press **Calculate eclipse**. The summary shows the local maximum (magnitude, obscuration, Sun altitude/azimuth, solar and lunar diameters). The Sun/Moon diagram and timeline follow the 20-second track, with play/pause, ±1 minute, 1×–300× speed and a jump to maximum.
3. Build the horizon under **Horizon & obstacles**: add points and obstacles, **Import JSON** (for example `examples/rome-horizon.json`), or press **Generate local terrain**, which downloads an 80 km COP30 DEM and profiles it every 2° (needs `OPENTOPOGRAPHY_API_KEY`).
4. Press **Find best clear time**. The app reports whether the Sun at maximum is clear, partially or fully blocked, plus any terrain-sunset warning. The Sun-path chart shows the Sun's track against the horizon profile.
5. Open the **observer-eye terrain view** (`/terrain-view`) to see the horizon profile as a 3D ring, with the Sun and Moon discs at maximum obscuration. Manual obstacles are not drawn in this view.

For a totality example, pick a coordinate on the 2026 path of totality and load `examples/totality-horizon.json`.

## API

All endpoints take and return JSON. Interactive OpenAPI docs are served at `http://localhost:8000/docs`.

| Method & path | Purpose |
|---|---|
| `GET /api/health` | Liveness check |
| `POST /api/eclipse/2026-08-12/report` | Eclipse type, contacts, maximum, optional track |
| `POST /api/eclipse/2026-08-12/state` | Sun/Moon state at one instant (`time_utc` must include a UTC offset) |
| `POST /api/eclipse/2026-08-12/horizon-analysis` | Track classified against `horizon_profile` + `obstacles`, best samples, sunset comparison |
| `POST /api/eclipse/2026-08-12/terrain-horizon` | Horizon profile from the local GeoTIFF |
| `POST /api/eclipse/2026-08-12/terrain-download` | Download a COP30 DEM, then return its horizon profile |

Conventions: coordinates are decimal degrees, north/east positive. Azimuth is measured clockwise from true north (0° N, 90° E). Altitude is positive above the astronomical horizon. Times are ISO 8601 with an offset.

### Example

```bash
curl -s -X POST http://localhost:8000/api/eclipse/2026-08-12/report \
  -H 'content-type: application/json' \
  -d '{"latitude": 41.9028, "longitude": 12.4964, "elevation_m": 20,
       "timezone": "Europe/Rome", "include_track": false}'
```

Abridged response from a local run (Rome):

```json
{
  "eclipse_type": "partial",
  "contacts": {
    "c1":      {"local": "2026-08-12T19:32:39.966255+02:00", "sun_altitude_deg": 6.75, "...": "..."},
    "c2":      null,
    "maximum": {"local": "2026-08-12T20:24:28.505204+02:00", "sun_altitude_deg": -1.90, "...": "..."},
    "c3":      null,
    "c4":      {"local": "2026-08-12T21:13:36.914840+02:00", "sun_altitude_deg": -10.12, "...": "..."}
  },
  "maximum": {"magnitude": 0.958, "obscuration_percent": 95.48, "sun": {"azimuth_deg": 292.53, "...": "..."}, "...": "..."},
  "maximum_visible_above_flat_horizon": null,
  "track": []
}
```

In Rome, maximum falls after sunset, so `maximum_visible_above_flat_horizon` is `null`. Send the same body to `horizon-analysis` with a `horizon_profile` and `obstacles` (the format of `examples/*.json`) to get per-sample visibility.

## Limitations

- The model covers terrain and whatever obstacles you enter. Trees, buildings, cranes and temporary objects are not in the DEM, and the terrain ray-cast has no atmospheric refraction term. This app does not replace an on-site check.
- The backend returns the first solar eclipse visible from the location starting on 12 August 2026 and does not check its date. For locations where the 12 August 2026 eclipse is not visible, the result can describe a later eclipse. Check the dates in `contacts`.
- DEM downloads that cross the antimeridian are not supported.

## License

MIT — see [LICENSE](LICENSE).
