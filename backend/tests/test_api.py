from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health(): assert client.get('/api/health').json()=={'status':'ok'}
def test_report_uses_aware_times():
    r=client.post('/api/eclipse/2026-08-12/report',json={'latitude':43.0,'longitude':-4.0,'elevation_m':10,'timezone':'Europe/Madrid','sample_seconds':60,'include_track':False})
    assert r.status_code==200
    data=r.json(); assert data['maximum']['time']['utc'].endswith('+00:00'); assert 0<=data['maximum']['obscuration_percent']<=100
def test_invalid_timezone():
    r=client.post('/api/eclipse/2026-08-12/report',json={'latitude':43,'longitude':-4,'timezone':'Mars/Olympus'})
    assert r.status_code==422

def test_horizon_analysis_handles_unsampled_maximum():
    r=client.post('/api/eclipse/2026-08-12/horizon-analysis',json={'latitude':43,'longitude':-4,'timezone':'Europe/Madrid','sample_seconds':17,'horizon_profile':[],'obstacles':[]})
    assert r.status_code==200
    assert r.json()['astronomical_maximum_visibility']['status'] in {'clear','partially_blocked','fully_blocked','below_astronomical_horizon'}

def test_horizon_analysis_reports_terrain_adjusted_sunset():
    r=client.post('/api/eclipse/2026-08-12/horizon-analysis',json={'latitude':43,'longitude':-4,'timezone':'Europe/Madrid','sample_seconds':60,'horizon_profile':[{'azimuth_deg':0,'altitude_deg':12},{'azimuth_deg':359,'altitude_deg':12}],'obstacles':[]})
    assert r.status_code==200
    sunset=r.json()['sunset']
    assert sunset['flat_horizon_sunset'] is not None
    assert sunset['terrain_horizon_sunset'] is not None
    assert sunset['difference_seconds'] < 0
