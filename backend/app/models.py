from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class ObserverRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float = Field(default=0, ge=-500, le=10000)
    timezone: str | None = None

class ReportRequest(ObserverRequest):
    sample_seconds: int = Field(default=30, ge=1, le=300)
    include_track: bool = True

class StateRequest(ObserverRequest):
    time_utc: datetime
    @field_validator('time_utc')
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError('time_utc must include a UTC offset')
        return value

class HorizonPoint(BaseModel):
    azimuth_deg: float
    altitude_deg: float = Field(ge=-90, le=90)
    @field_validator('azimuth_deg')
    @classmethod
    def normalize(cls, value: float) -> float:
        return value % 360

class AngularObstacle(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    azimuth_start_deg: float
    azimuth_end_deg: float
    bottom_altitude_deg: float = Field(default=0, ge=-90, le=90)
    top_altitude_deg: float = Field(ge=-90, le=90)
    enabled: bool = True
    @field_validator('azimuth_start_deg', 'azimuth_end_deg')
    @classmethod
    def normalize(cls, value: float) -> float:
        return value % 360

class HorizonAnalysisRequest(ReportRequest):
    safety_margin_deg: float = Field(default=0.1, ge=0, le=10)
    horizon_profile: list[HorizonPoint] = []
    obstacles: list[AngularObstacle] = []

class TerrainRequest(ObserverRequest):
    max_distance_km: float = Field(default=50, gt=0, le=200)
    azimuth_step_deg: float = Field(default=1, gt=0, le=30)
    distance_step_m: float = Field(default=100, ge=10, le=2000)

class ApiError(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ApiError

Visibility = Literal['clear', 'partially_blocked', 'fully_blocked', 'below_astronomical_horizon']
