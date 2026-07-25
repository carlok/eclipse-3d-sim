from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .astronomy import EclipseNotVisible, report, state, timezone_for
from .horizon import classify, effective_horizon, sunset_analysis, terrain_profile
from .opentopography import TerrainDownloadError, download_cop30
from .models import HorizonAnalysisRequest, ReportRequest, StateRequest, TerrainRequest
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('backend/.env')
load_dotenv()

app = FastAPI(title='Eclipse Visibility Simulator', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('ALLOWED_ORIGINS','http://localhost:5173').split(','), allow_methods=['*'], allow_headers=['*'])

def error(status: int, code: str, message: str):
    raise HTTPException(status_code=status, detail={'error': {'code':code,'message':message}})

@app.exception_handler(ValueError)
async def invalid_request(_, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=422, content={'error':{'code':'VALIDATION_ERROR','message':str(exc)}})

@app.get('/api/health')
def health(): return {'status':'ok'}

REPORT_CACHE: dict[tuple, dict] = {}
def cached_report(latitude,longitude,elevation,timezone,sample_seconds,include_track):
    # Rounding is used only to group cache entries. The first calculation for a
    # key retains the exact observer coordinate supplied by the user.
    key=('2026-08-12',round(latitude,5),round(longitude,5),round(elevation,1),timezone,sample_seconds,include_track)
    if key not in REPORT_CACHE:
        if len(REPORT_CACHE) >= 128: REPORT_CACHE.pop(next(iter(REPORT_CACHE)))
        REPORT_CACHE[key]=report(latitude,longitude,elevation,timezone_for(latitude,longitude,timezone),sample_seconds,include_track)
    return REPORT_CACHE[key]

@app.post('/api/eclipse/2026-08-12/report')
def eclipse_report(request: ReportRequest):
    try:
        return cached_report(request.latitude,request.longitude,request.elevation_m,request.timezone,request.sample_seconds,request.include_track)
    except EclipseNotVisible as exc: error(422,'ECLIPSE_NOT_VISIBLE',str(exc))

@app.post('/api/eclipse/2026-08-12/state')
def eclipse_state(request: StateRequest):
    return state(request.latitude,request.longitude,request.elevation_m,request.time_utc,timezone_for(request.latitude,request.longitude,request.timezone))

@app.post('/api/eclipse/2026-08-12/horizon-analysis')
def horizon_analysis(request: HorizonAnalysisRequest):
    try: result = cached_report(request.latitude,request.longitude,request.elevation_m,request.timezone,request.sample_seconds,True)
    except EclipseNotVisible as exc: error(422,'ECLIPSE_NOT_VISIBLE',str(exc))
    analyzed=[]
    for sample in result['track']:
        h=effective_horizon(sample['sun']['azimuth_deg'],request.horizon_profile,request.obstacles)
        status, clearance=classify(sample['sun'],h,request.safety_margin_deg)
        analyzed.append({**sample,'horizon_altitude_deg':h,'visibility':status,**clearance})
    clear=[s for s in analyzed if s['visibility']=='clear']
    partial=[s for s in analyzed if s['visibility']=='partially_blocked']
    maximum=result['maximum']
    maximum_horizon=effective_horizon(maximum['sun']['azimuth_deg'],request.horizon_profile,request.obstacles)
    maximum_status, maximum_clearance=classify(maximum['sun'],maximum_horizon,request.safety_margin_deg)
    sunset=sunset_analysis(request.latitude,request.longitude,request.elevation_m,timezone_for(request.latitude,request.longitude,request.timezone),request.horizon_profile,request.obstacles,request.safety_margin_deg,datetime.fromisoformat(result['event']['date']))
    return {'best_clear_sample':max(clear,key=lambda x:x['obscuration_fraction']) if clear else None,'best_partially_visible_sample':max(partial,key=lambda x:x['obscuration_fraction']) if partial else None,'astronomical_maximum_visibility':{'status':maximum_status,**maximum_clearance},'sunset':sunset,'track':analyzed}

@app.post('/api/eclipse/2026-08-12/terrain-horizon')
def terrain(request: TerrainRequest):
    try:
        profile, source=terrain_profile(request.latitude,request.longitude,request.elevation_m,request.max_distance_km,request.azimuth_step_deg,request.distance_step_m)
        return {'horizon_profile':profile,'source':source}
    except FileNotFoundError as exc: error(503,'TERRAIN_UNAVAILABLE',str(exc))

@app.post('/api/eclipse/2026-08-12/terrain-download')
def terrain_download(request: TerrainRequest):
    try:
        dem=download_cop30(request.latitude,request.longitude,request.max_distance_km)
        profile, source=terrain_profile(request.latitude,request.longitude,request.elevation_m,request.max_distance_km,request.azimuth_step_deg,request.distance_step_m,str(dem))
        source.update({'provider':'opentopography_cop30','cached_file':dem.name})
        return {'horizon_profile':profile,'source':source}
    except TerrainDownloadError as exc: error(502,'TERRAIN_DOWNLOAD_FAILED',str(exc))
