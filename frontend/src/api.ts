import type { HorizonPoint, Obstacle, Report } from './types';
const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
async function call<T>(path:string, body:unknown):Promise<T> { const r=await fetch(`${base}${path}`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}); if(!r.ok) { const e=await r.json().catch(()=>null); throw new Error(e?.detail?.error?.message ?? e?.error?.message ?? 'Request failed'); } return r.json(); }
export const calculate=(body:object)=>call<Report>('/eclipse/2026-08-12/report',body);
export const analyze=(body:object)=>call<{track:Report['track'];best_clear_sample:unknown;astronomical_maximum_visibility:{status:string};sunset:{difference_seconds:number|null;warning:string|null}}>('/eclipse/2026-08-12/horizon-analysis',body);
export const terrain=(body:object)=>call<{horizon_profile:HorizonPoint[];source:object}>('/eclipse/2026-08-12/terrain-download',body);
export const exportHorizon=(profile:HorizonPoint[], obstacles:Obstacle[])=>JSON.stringify({horizon_profile:profile,obstacles},null,2);
