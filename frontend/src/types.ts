export type HorizonPoint = { azimuth_deg: number; altitude_deg: number };
export type Sun = { azimuth_deg:number; altitude_apparent_deg:number; altitude_geometric_deg:number; angular_radius_deg:number; angular_diameter_deg:number; lower_limb_altitude_deg:number; upper_limb_altitude_deg:number };
export type Moon = { azimuth_deg:number; altitude_deg:number; angular_radius_deg:number; angular_diameter_deg:number; offset_right_deg:number; offset_up_deg:number; position_angle_deg:number };
export type Sample = { time:{utc:string;local:string;timezone:string}; sun:Sun; moon:Moon; magnitude:number; magnitude_percent:number; obscuration_fraction:number; obscuration_percent:number; sun_moon_separation_deg:number; horizon_altitude_deg?:number; visibility?:string };
export type Report = { event:{name:string;date:string}; observer:{latitude:number;longitude:number;elevation_m:number;timezone:string}; eclipse_type:string; maximum:Sample; contacts:Record<string, {utc:string;local:string;sun_altitude_deg:number}|null>; track:Sample[] };
export type Obstacle = { name:string; azimuth_start_deg:number; azimuth_end_deg:number; bottom_altitude_deg:number; top_altitude_deg:number; enabled:boolean };
