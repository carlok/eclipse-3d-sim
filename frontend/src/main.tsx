import { lazy, StrictMode, Suspense } from 'react'; import { createRoot } from 'react-dom/client'; import './styles.css'; import App from './App';
const TerrainPage=lazy(()=>import('./TerrainPage'));
const page=window.location.pathname==='/terrain-view'?<Suspense fallback={<main>Loading terrain view…</main>}><TerrainPage/></Suspense>:<App/>;
createRoot(document.getElementById('root')!).render(<StrictMode>{page}</StrictMode>);
