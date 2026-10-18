from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from .horizon import destination

API_URL = 'https://portal.opentopography.org/API/globaldem'

class TerrainDownloadError(RuntimeError): pass

def _terrain_cache_dir() -> Path:
    return Path(os.getenv('TERRAIN_CACHE_DIR', str(Path(__file__).resolve().parents[2] / 'data/dem/cache'))).resolve()

def _cop30_cache_path(cache: Path, latitude: float, longitude: float, radius_km: float) -> Path:
    cache_root = cache.resolve()
    digest = hashlib.sha256(f'{latitude:.8f}:{longitude:.8f}:{radius_km:.4f}'.encode('ascii')).hexdigest()[:32]
    output = (cache_root / f'cop30_{digest}.tif').resolve()
    if output.parent != cache_root:
        raise TerrainDownloadError('Invalid terrain cache path.')
    return output

def download_cop30(latitude: float, longitude: float, radius_km: float) -> Path:
    api_key=os.getenv('OPENTOPOGRAPHY_API_KEY')
    if not api_key: raise TerrainDownloadError('OpenTopography is not configured. Set OPENTOPOGRAPHY_API_KEY in backend/.env.')
    north,_=destination(latitude,longitude,0,radius_km*1000)
    south,_=destination(latitude,longitude,180,radius_km*1000)
    _,east=destination(latitude,longitude,90,radius_km*1000)
    _,west=destination(latitude,longitude,270,radius_km*1000)
    if west > east: raise TerrainDownloadError('Terrain downloads crossing the antimeridian are not supported yet.')
    cache=_terrain_cache_dir()
    cache.mkdir(parents=True,exist_ok=True)
    output=_cop30_cache_path(cache, latitude, longitude, radius_km)
    if output.is_file() and output.stat().st_size > 1024: return output
    query=urlencode({'demtype':'COP30','south':f'{south:.6f}','north':f'{north:.6f}','west':f'{west:.6f}','east':f'{east:.6f}','outputFormat':'GTiff','API_Key':api_key})
    temporary=output.with_suffix('.part')
    try:
        with urlopen(f'{API_URL}?{query}',timeout=90) as response:
            payload=response.read()
    except HTTPError as exc:
        raise TerrainDownloadError(f'OpenTopography rejected the DEM request ({exc.code}). Check the API key and request size.') from exc
    except URLError as exc:
        raise TerrainDownloadError('Could not reach OpenTopography. Check the network connection and retry.') from exc
    if len(payload)<1024 or payload[:2] not in {b'II',b'MM'}:
        raise TerrainDownloadError('OpenTopography did not return a GeoTIFF for this location.')
    temporary.write_bytes(payload)
    temporary.replace(output)
    return output
