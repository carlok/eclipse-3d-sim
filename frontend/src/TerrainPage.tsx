import { TerrainView3D } from './TerrainView3D';
import './terrain-page.css';
import type { HorizonPoint, Sample } from './types';

type SavedScene={sample:Sample;profile:HorizonPoint[]};
function savedScene():SavedScene|undefined { try { const raw=sessionStorage.getItem('eclipse-terrain-view'); return raw?JSON.parse(raw):undefined; } catch { return undefined; } }
export default function TerrainPage(){
  const scene=savedScene();
  return <main className="terrain-page"><header><div><p className="eyebrow">SIGHTLINE INSPECTION</p><h1>Observer-eye terrain view</h1></div><a className="back-link" href="/">← Back to simulator</a></header>{scene?<><p className="notice">This full-screen scene points toward the Sun at maximum obscuration. The terrain ring is the horizon profile currently loaded in the simulator.</p><TerrainView3D sample={scene.sample} profile={scene.profile} obstacles={[]}/></>:<section className="empty-scene"><h2>No terrain scene yet</h2><p>Return to the simulator, calculate the eclipse, then open this view from the Sun path and horizon panel.</p><a className="terrain-page-link" href="/">Open simulator</a></section>}</main>;
}
