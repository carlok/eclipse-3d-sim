from app.horizon import circular_interpolate, classify, effective_horizon
from app.models import AngularObstacle, HorizonPoint
import numpy as np
import rasterio
from rasterio.transform import from_origin
from app.horizon import terrain_profile
def test_circular_interpolation():
    points=[HorizonPoint(azimuth_deg=359,altitude_deg=2),HorizonPoint(azimuth_deg=1,altitude_deg=4)]
    assert circular_interpolate(points,0)==3
def test_obstacle_overrides_profile():
    assert effective_horizon(250,[HorizonPoint(azimuth_deg=250,altitude_deg=2)],[AngularObstacle(name='tree',azimuth_start_deg=245,azimuth_end_deg=255,top_altitude_deg=8)])==8
def test_limb_classification():
    sun={'altitude_apparent_deg':4,'lower_limb_altitude_deg':3.7,'upper_limb_altitude_deg':4.3}
    assert classify(sun,3,.1)[0]=='clear'
    assert classify(sun,4,.1)[0]=='partially_blocked'
    assert classify(sun,5,.1)[0]=='fully_blocked'

def test_terrain_profile_reads_local_geotiff(tmp_path, monkeypatch):
    dem=tmp_path/'fixture.tif'
    with rasterio.open(dem,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:4326',transform=from_origin(12,43,1,1)) as dst:
        dst.write(np.full((1,2,2),100,dtype='float32'))
    monkeypatch.setenv('TERRAIN_DEM_PATH',str(dem))
    profile, source=terrain_profile(42,12.5,10,1,180,500)
    assert len(profile)==2 and source['provider']=='local_geotiff'
