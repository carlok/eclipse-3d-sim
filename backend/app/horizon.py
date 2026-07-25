from __future__ import annotations

import math, os
from pathlib import Path
import numpy as np
from .models import AngularObstacle, HorizonPoint

EARTH_RADIUS_M = 6_371_000

def circular_interpolate(points: list[HorizonPoint], azimuth: float) -> float:
    if not points: return 0.0
    samples = sorted((p.azimuth_deg % 360, p.altitude_deg) for p in points)
    target = azimuth % 360
    extended = [(samples[-1][0]-360, samples[-1][1]), *samples, (samples[0][0]+360, samples[0][1])]
    for (a,b), (c,d) in zip(extended, extended[1:]):
        if a <= target <= c:
            return b if c == a else b + (d-b)*(target-a)/(c-a)
    return samples[0][1]

def _in_arc(azimuth: float, start: float, end: float) -> bool:
    return start <= end and start <= azimuth <= end or start > end and (azimuth >= start or azimuth <= end)

def effective_horizon(azimuth: float, profile: list[HorizonPoint], obstacles: list[AngularObstacle]) -> float:
    result = circular_interpolate(profile, azimuth)
    for obstacle in obstacles:
        if obstacle.enabled and _in_arc(azimuth % 360, obstacle.azimuth_start_deg, obstacle.azimuth_end_deg):
            result = max(result, obstacle.top_altitude_deg)
    return result

def classify(sun: dict, horizon_altitude: float, margin: float) -> tuple[str, dict]:
    lower, upper, center = sun['lower_limb_altitude_deg'], sun['upper_limb_altitude_deg'], sun['altitude_apparent_deg']
    if upper < 0: return 'below_astronomical_horizon', {'center_clearance_deg': center, 'lower_limb_clearance_deg': lower, 'upper_limb_clearance_deg': upper}
    clearance = {'center_clearance_deg': center-horizon_altitude-margin, 'lower_limb_clearance_deg': lower-horizon_altitude-margin, 'upper_limb_clearance_deg': upper-horizon_altitude-margin}
    if clearance['lower_limb_clearance_deg'] >= 0: return 'clear', clearance
    if clearance['upper_limb_clearance_deg'] <= 0: return 'fully_blocked', clearance
    return 'partially_blocked', clearance

def destination(latitude: float, longitude: float, bearing: float, distance_m: float) -> tuple[float,float]:
    phi, lam, theta, delta = map(math.radians, (latitude, longitude, bearing, distance_m/EARTH_RADIUS_M*180/math.pi))
    phi2 = math.asin(math.sin(phi)*math.cos(delta)+math.cos(phi)*math.sin(delta)*math.cos(theta))
    lam2 = lam + math.atan2(math.sin(theta)*math.sin(delta)*math.cos(phi), math.cos(delta)-math.sin(phi)*math.sin(phi2))
    return math.degrees(phi2), (math.degrees(lam2)+540)%360-180

def terrain_profile(latitude: float, longitude: float, observer_m: float, max_distance_km: float, azimuth_step_deg: float, distance_step_m: float, dem_path: str | None = None) -> tuple[list[dict],dict]:
    path = dem_path or os.environ.get('TERRAIN_DEM_PATH')
    if not path or not Path(path).is_file(): raise FileNotFoundError('No local DEM is configured. Set TERRAIN_DEM_PATH to a GeoTIFF.')
    import rasterio
    profile=[]
    with rasterio.open(path) as dataset:
        for azimuth in np.arange(0,360,azimuth_step_deg):
            maximum=-90.0
            for distance in np.arange(distance_step_m, max_distance_km*1000+1, distance_step_m):
                lat, lon = destination(latitude,longitude,float(azimuth),float(distance))
                try:
                    elevation = next(dataset.sample([(lon,lat)]))[0]
                    if dataset.nodata is not None and elevation == dataset.nodata: continue
                    corrected_distance = distance * (1-distance/(2*EARTH_RADIUS_M))
                    angle = math.degrees(math.atan2(float(elevation)-observer_m-distance*distance/(2*EARTH_RADIUS_M), corrected_distance))
                    maximum=max(maximum,angle)
                except Exception: continue
            profile.append({'azimuth_deg':round(float(azimuth),6),'altitude_deg':round(maximum,6)})
    return profile, {'provider':'local_geotiff','path':Path(path).name,'max_distance_km':max_distance_km,'azimuth_step_deg':azimuth_step_deg}
