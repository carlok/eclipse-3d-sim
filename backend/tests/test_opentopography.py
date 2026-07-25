import pytest
from app.opentopography import TerrainDownloadError, download_cop30

def test_download_requires_configured_key(monkeypatch):
    monkeypatch.delenv('OPENTOPOGRAPHY_API_KEY', raising=False)
    with pytest.raises(TerrainDownloadError, match='OPENTOPOGRAPHY_API_KEY'):
        download_cop30(41.9,12.5,40)
