from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo
import astronomy
from timezonefinder import TimezoneFinder

SUN_RADIUS_KM = 695700.0
MOON_RADIUS_KM = 1737.4
EVENT_DATE = datetime(2026, 8, 12, tzinfo=UTC)
_tz_finder = TimezoneFinder()

class EclipseNotVisible(ValueError): pass

def timezone_for(latitude: float, longitude: float, supplied: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(supplied) if supplied else ZoneInfo(_tz_finder.timezone_at(lat=latitude, lng=longitude) or 'UTC')
    except Exception as exc:
        raise ValueError('timezone must be a valid IANA timezone') from exc

def iso_times(time: astronomy.Time, zone: ZoneInfo) -> dict:
    utc = time.Utc().replace(tzinfo=UTC)
    return {'utc': utc.isoformat(), 'local': utc.astimezone(zone).isoformat(), 'timezone': zone.key}

def _radius_deg(radius_km: float, distance_au: float) -> float:
    return math.degrees(math.asin(radius_km / (distance_au * astronomy.KM_PER_AU)))

def _separation_deg(sun_az: float, sun_alt: float, moon_az: float, moon_alt: float) -> float:
    a1, e1, a2, e2 = map(math.radians, (sun_az, sun_alt, moon_az, moon_alt))
    return math.degrees(math.acos(max(-1, min(1, math.sin(e1)*math.sin(e2)+math.cos(e1)*math.cos(e2)*math.cos(a1-a2)))))

def _overlap_fraction(r1: float, r2: float, distance: float) -> float:
    if distance >= r1 + r2: return 0.0
    if distance <= abs(r1-r2): return min(1.0, (min(r1,r2)/r1) ** 2)
    x = (distance*distance + r1*r1 - r2*r2) / (2*distance*r1)
    y = (distance*distance + r2*r2 - r1*r1) / (2*distance*r2)
    area = r1*r1*math.acos(max(-1,min(1,x))) + r2*r2*math.acos(max(-1,min(1,y))) - .5*math.sqrt(max(0,(-distance+r1+r2)*(distance+r1-r2)*(distance-r1+r2)*(distance+r1+r2)))
    return max(0, min(1, area/(math.pi*r1*r1)))

def state(latitude: float, longitude: float, elevation_m: float, when: datetime, zone: ZoneInfo) -> dict:
    when = when.astimezone(UTC)
    time = astronomy.Time.Make(when.year, when.month, when.day, when.hour, when.minute, when.second + when.microsecond/1e6)
    observer = astronomy.Observer(latitude, longitude, elevation_m)
    sun_eq = astronomy.Equator(astronomy.Body.Sun, time, observer, True, True)
    moon_eq = astronomy.Equator(astronomy.Body.Moon, time, observer, True, True)
    sun = astronomy.Horizon(time, observer, sun_eq.ra, sun_eq.dec, astronomy.Refraction.Normal)
    sun_geo = astronomy.Horizon(time, observer, sun_eq.ra, sun_eq.dec, astronomy.Refraction.Airless)
    moon = astronomy.Horizon(time, observer, moon_eq.ra, moon_eq.dec, astronomy.Refraction.Normal)
    sr, mr = _radius_deg(SUN_RADIUS_KM, sun_eq.dist), _radius_deg(MOON_RADIUS_KM, moon_eq.dist)
    sep = _separation_deg(sun.azimuth, sun.altitude, moon.azimuth, moon.altitude)
    magnitude = max(0, min(1.5, (sr + mr - sep) / (2 * sr)))
    az_delta = ((moon.azimuth - sun.azimuth + 180) % 360) - 180
    return {
      'time': iso_times(time, zone), 'sun': {'azimuth_deg': sun.azimuth, 'altitude_apparent_deg': sun.altitude, 'altitude_geometric_deg': sun_geo.altitude, 'zenith_angle_deg': 90-sun.altitude, 'angular_radius_deg': sr, 'angular_diameter_deg': 2*sr, 'upper_limb_altitude_deg': sun.altitude+sr, 'lower_limb_altitude_deg': sun.altitude-sr},
      'moon': {'azimuth_deg': moon.azimuth, 'altitude_deg': moon.altitude, 'angular_radius_deg': mr, 'angular_diameter_deg': 2*mr, 'offset_right_deg': az_delta*math.cos(math.radians(sun.altitude)), 'offset_up_deg': moon.altitude-sun.altitude, 'position_angle_deg': math.degrees(math.atan2(az_delta*math.cos(math.radians(sun.altitude)), moon.altitude-sun.altitude))%360},
      'magnitude': magnitude, 'magnitude_percent': magnitude*100, 'obscuration_fraction': _overlap_fraction(sr,mr,sep), 'obscuration_percent': _overlap_fraction(sr,mr,sep)*100, 'sun_moon_separation_deg': sep
    }

def report(latitude: float, longitude: float, elevation_m: float, zone: ZoneInfo, sample_seconds: int, include_track: bool) -> dict:
    observer = astronomy.Observer(latitude, longitude, elevation_m)
    eclipse = astronomy.SearchLocalSolarEclipse(astronomy.Time.Make(2026,8,12,0,0,0), observer)
    if eclipse.kind == astronomy.EclipseKind.Invalid or eclipse.partial_begin is None:
        raise EclipseNotVisible('The 12 August 2026 eclipse is not locally visible from this coordinate.')
    peak = state(latitude, longitude, elevation_m, eclipse.peak.time.Utc().replace(tzinfo=UTC), zone)
    def contact(event): return None if event is None else {**iso_times(event.time,zone), 'sun_altitude_deg': event.altitude}
    c1, c4 = eclipse.partial_begin.time.Utc().replace(tzinfo=UTC), eclipse.partial_end.time.Utc().replace(tzinfo=UTC)
    track = []
    if include_track:
        seconds = int((c4-c1).total_seconds())
        for offset in range(0, seconds+1, sample_seconds): track.append(state(latitude,longitude,elevation_m,c1+timedelta(seconds=offset),zone))
        if track[-1]['time']['utc'] != iso_times(eclipse.partial_end.time,zone)['utc']: track.append(state(latitude,longitude,elevation_m,c4,zone))
    return {'event': {'name':'Solar eclipse of 12 August 2026','date':'2026-08-12'}, 'observer': {'latitude':latitude,'longitude':longitude,'elevation_m':elevation_m,'timezone':zone.key}, 'eclipse_type': eclipse.kind.name.lower(), 'maximum': peak, 'contacts': {'c1':contact(eclipse.partial_begin),'c2':contact(eclipse.total_begin),'maximum':contact(eclipse.peak),'c3':contact(eclipse.total_end),'c4':contact(eclipse.partial_end)}, 'maximum_visible_above_flat_horizon': peak if peak['sun']['lower_limb_altitude_deg'] > 0 else None, 'track': track}
