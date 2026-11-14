import test from 'node:test';
import assert from 'node:assert/strict';
import {parseCoordinate,matchedFrames,difference,stack,sharedScale,fieldURL} from '../public/science.js';

test('coordinates retain decimal degree units and parse challenge sexagesimal coordinates',()=>{
  assert.equal(parseCoordinate('269.446268',true),269.446268);
  assert.ok(Math.abs(parseCoordinate('08h55m10.831s',true)-133.7951291667)<1e-7);
  assert.ok(Math.abs(parseCoordinate('-7:14:42.53')+7.2451472222)<1e-7);
  assert.equal(parseCoordinate('-0:30:00'),-.5);
  for(const value of ['', 'NaN', 'Infinity', '360', '-1', '25:00:00','12:60:00'])assert.throws(()=>parseCoordinate(value,true));
  assert.throws(()=>parseCoordinate('90:00:01'));
});
test('wavelength matching excludes missing measurements and values outside the tolerance',()=>{
  const frames=[{wavelength_um:2},{wavelength_um:2.1},{wavelength_um:2.11},{wavelength_um:null}];
  assert.deepEqual(matchedFrames(frames,0,true),[0,1]);
  assert.deepEqual(matchedFrames(frames,0,false),[0,1,2,3]);
  assert.deepEqual(matchedFrames(frames,3,true),[3]);
});
test('difference and stacking preserve masked pixels without turning them into flux',()=>{
  assert.deepEqual(difference([1,null,4],[3,2,null]),[-2,null,null]);
  assert.deepEqual(stack([{pixels:[1,null,4]},{pixels:[3,null,null]}]),[2,null,4]);
  const scale=sharedScale([{pixels:[null,null]}]);assert.ok(scale.high>scale.low);
});
test('shared URLs preserve coordinates and clear stale query parameters',()=>{
  const url=new URL(fieldURL('https://example.org/?secret=stale',{ra:12,dec:-4,fov:6,detector:'D6'}));
  assert.equal(url.searchParams.get('dec'),'-4');assert.equal(url.searchParams.has('secret'),false);
  assert.equal(url.hash,'#observatory');
});
