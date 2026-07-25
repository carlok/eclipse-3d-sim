# Eclipse sightline — 12 August 2026

An offline-friendly local solar-eclipse visibility simulator. It calculates astronomical circumstances with Astronomy Engine, then compares the apparent solar disc against terrain and manually modelled obstacles.

## Run locally

```bash
cd backend && python3.14 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

Or run `docker compose up --build`. To enable terrain profiling, put a WGS84 GeoTIFF in `data/dem/terrain.tif`; Docker mounts this directory read-only. Set `TERRAIN_DEM_PATH` to another path for direct backend runs.

To download a terrain GeoTIFF automatically for the selected point, set `OPENTOPOGRAPHY_API_KEY` in `backend/.env`. The **Generate local terrain** action requests a bounded Copernicus 30 m DEM around the observer, stores it in `data/dem/cache`, and then builds the horizon profile. The API key never leaves the backend.

## API

`POST /api/eclipse/2026-08-12/report` returns a summary and an optional C1–C4 track. `state` returns one instant, `horizon-analysis` combines manual points/obstacles with the track, `terrain-horizon` ray-casts a configured local GeoTIFF, and `terrain-download` downloads then profiles a bounded Copernicus DEM. See the OpenAPI document at `/docs` while the backend is running.

Coordinates use north/east-positive decimal degrees. Azimuth is true-north clockwise (0° north, 90° east); altitude is positive above the astronomical horizon. Visibility uses apparent solar altitude; geometric altitude is retained for inspection.

Magnitude is the fraction of solar diameter eclipsed. Obscuration is the fraction of solar area covered, and is the primary coverage percentage.

Terrain data cannot model trees, buildings, cranes, or temporary objects—add those using the obstacle editor. This app is not a substitute for an on-site inspection.

After **Find best clear time**, the simulator also compares flat-horizon sunset with terrain/obstacle sunset using the apparent lower solar limb. It warns when the combined horizon hides the full solar disc before astronomical sunset.

**Never observe the Sun directly without certified solar viewing protection, except during the brief total phase at a location inside the path of totality. High obscuration does not make unfiltered viewing safe.**

## Demonstration

Use the default Rome point, press **Calculate eclipse**, then import `examples/rome-horizon.json` or add an obstacle. Press **Find best clear time** to compare visibility. For a totality example, try a coordinate on the 2026 path and load `examples/totality-horizon.json`.
