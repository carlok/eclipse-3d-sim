import { Canvas } from '@react-three/fiber';
import { Billboard, OrbitControls, Sky } from '@react-three/drei';
import { useMemo } from 'react';
import * as THREE from 'three';
import './terrain-3d.css';
import type { HorizonPoint, Obstacle, Sample } from './types';

const RAD=Math.PI/180;
function inArc(az:number,start:number,end:number){return start<=end?az>=start&&az<=end:az>=start||az<=end}
function horizonAt(az:number, profile:HorizonPoint[], obstacles:Obstacle[]){
  const p=[...profile].sort((a,b)=>a.azimuth_deg-b.azimuth_deg); let altitude=0;
  if(p.length){const x=az%360;const loop=[{...p[p.length-1],azimuth_deg:p[p.length-1].azimuth_deg-360},...p,{...p[0],azimuth_deg:p[0].azimuth_deg+360}];for(let i=1;i<loop.length;i++)if(loop[i-1].azimuth_deg<=x&&x<=loop[i].azimuth_deg){const a=loop[i-1],b=loop[i];altitude=a.altitude_deg+(b.altitude_deg-a.altitude_deg)*(x-a.azimuth_deg)/(b.azimuth_deg-a.azimuth_deg);break}}
  return Math.max(altitude,...obstacles.filter(o=>o.enabled&&inArc(az,o.azimuth_start_deg,o.azimuth_end_deg)).map(o=>o.top_altitude_deg));
}
function MountainRing({profile,obstacles}:{profile:HorizonPoint[];obstacles:Obstacle[]}){
  const {geometry,ridge}=useMemo(()=>{const radius=80, vertices:number[]=[], ridgeVertices:number[]=[];for(let az=0;az<=360;az+=2){const a=az%360,h=Math.max(-4,Math.min(48,Math.tan(horizonAt(a,profile,obstacles)*RAD)*radius));ridgeVertices.push(Math.sin(a*RAD)*radius,h,-Math.cos(a*RAD)*radius);if(az<360){const next=az+2, nextHeight=Math.max(-4,Math.min(48,Math.tan(horizonAt(next,profile,obstacles)*RAD)*radius));vertices.push(0,-3,0,Math.sin(a*RAD)*radius,h,-Math.cos(a*RAD)*radius,Math.sin(next*RAD)*radius,nextHeight,-Math.cos(next*RAD)*radius)}}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));const r=new THREE.BufferGeometry();r.setAttribute('position',new THREE.Float32BufferAttribute(ridgeVertices,3));return {geometry:g,ridge:r}},[profile,obstacles]);
  return <><mesh geometry={geometry}><meshBasicMaterial color="#2a696f" side={THREE.DoubleSide}/></mesh><lineSegments geometry={ridge}><lineBasicMaterial color="#8ed1c0"/></lineSegments></>
}
function SunMarker({sample}:{sample:Sample}){const position=useMemo(()=>{const r=70,a=sample.sun.azimuth_deg*RAD,e=sample.sun.altitude_apparent_deg*RAD;return [Math.sin(a)*Math.cos(e)*r,Math.sin(e)*r,-Math.cos(a)*Math.cos(e)*r] as [number,number,number]},[sample]);const solarRadius=2.7;const moonRadius=solarRadius*sample.moon.angular_radius_deg/sample.sun.angular_radius_deg;const moonX=solarRadius*sample.moon.offset_right_deg/sample.sun.angular_radius_deg;const moonY=solarRadius*sample.moon.offset_up_deg/sample.sun.angular_radius_deg;return <><group position={position}><Billboard follow><mesh><circleGeometry args={[solarRadius,48]}/><meshBasicMaterial color="#ffe27a"/></mesh><mesh position={[moonX,moonY,.01]}><circleGeometry args={[moonRadius,48]}/><meshBasicMaterial color="#02050a"/></mesh></Billboard></group><pointLight position={position} color="#ffc84f" intensity={5} distance={50}/><line><bufferGeometry><bufferAttribute attach="attributes-position" args={[new Float32Array([0,0,0,...position]),3]}/></bufferGeometry><lineBasicMaterial color="#f6bd42"/></line></>}
export function TerrainView3D({sample,profile,obstacles}:{sample:Sample;profile:HorizonPoint[];obstacles:Obstacle[]}){
  if(!window.WebGLRenderingContext)return <p className="webgl-fallback">WebGL is unavailable in this browser. Use the 2D sun-path chart instead.</p>;
  const sun=`Sun: ${sample.sun.azimuth_deg.toFixed(1)}° azimuth, ${sample.sun.altitude_apparent_deg.toFixed(2)}° altitude`;
  const terrain=profile.map(point=>point.altitude_deg); const range=terrain.length?`${Math.min(...terrain).toFixed(1)}°–${Math.max(...terrain).toFixed(1)}° horizon`: 'flat horizon';
  return <section className="terrain-3d"><div className="view-label"><strong>Observer-eye terrain view</strong><span>{sun} · {range}</span></div><Canvas camera={{position:[0,2,0],fov:70}} dpr={[1,Math.min(window.devicePixelRatio,2)]}><color attach="background" args={['#07101c']}/><fog attach="fog" args={['#07101c',40,140]}/><Sky distance={450000} sunPosition={[0,1,0]} inclination={0.45} azimuth={0.25}/><MountainRing profile={profile} obstacles={obstacles}/><SunMarker sample={sample}/><gridHelper args={[160,16,'#35526b','#1b3146']}/><OrbitControls target={[Math.sin(sample.sun.azimuth_deg*RAD)*60,Math.tan(sample.sun.altitude_apparent_deg*RAD)*60,-Math.cos(sample.sun.azimuth_deg*RAD)*60]} minDistance={1} maxDistance={100} maxPolarAngle={Math.PI*.49}/></Canvas><p className="caption">The black lunar disc uses the actual angular-radius ratio and right/up offset at maximum obscuration. Terrain is shown at true vertical scale.</p></section>
}
