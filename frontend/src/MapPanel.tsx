import { CircleMarker, MapContainer, Marker, Polyline, TileLayer, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
const markerIcon=L.divIcon({className:'map-pin',html:'●',iconSize:[20,20],iconAnchor:[10,10]});
function Clicker({set}:{set:(p:[number,number])=>void}) { useMapEvents({click:e=>set([e.latlng.lat,e.latlng.lng])}); return null; }
export function MapPanel({position,setPosition,azimuth}:{position:[number,number];setPosition:(p:[number,number])=>void;azimuth?:number}) {
  const end:[number,number]=azimuth===undefined?position:[position[0]+Math.cos(azimuth*Math.PI/180)*.08,position[1]+Math.sin(azimuth*Math.PI/180)*.08];
  return <MapContainer center={position} zoom={8} className="map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><Clicker set={setPosition}/><Marker draggable icon={markerIcon} position={position} eventHandlers={{dragend:e=>{const p=e.target.getLatLng();setPosition([p.lat,p.lng])}}}/><CircleMarker center={position} radius={14} pathOptions={{color:'#f6bd42'}}/>{azimuth!==undefined&&<Polyline positions={[position,end]} pathOptions={{color:'#f6bd42',weight:3}}/>}</MapContainer>
}
