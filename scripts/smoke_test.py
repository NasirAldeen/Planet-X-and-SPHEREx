"""Exercise the real HTTP server, bundled targets and a live IRSA search."""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT=Path(__file__).resolve().parents[1]


def main():
    base='http://127.0.0.1:8765'
    process=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--port','8765'],
                             cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    checks=[]
    try:
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError(process.stdout.read().decode(errors='replace'))
            try:
                response=requests.get(base+'/api/health',timeout=1)
                if response.ok: break
            except requests.RequestException: pass
            time.sleep(.25)
        else: raise RuntimeError('Server failed readiness check')
        checks.append('Waitress HTTP server started and health endpoint returned 200.')
        for path in ['/', '/style.css','/app.js','/science.js','/icon.svg']:
            response=requests.get(base+path,timeout=10)
            assert response.status_code==200, path
        checks.append('HTML, CSS, JavaScript modules and icon served successfully.')
        targets=requests.get(base+'/data/targets.json',timeout=10).json()
        for target in targets:
            response=requests.get(base+'/data/'+target['id']+'.json',timeout=10)
            assert response.ok and len(response.json()['frames'])>=2, target['id']
        checks.append('All five real-observation target packs returned HTTP 200 and multiple frames.')
        assert requests.get(base+'/.git/config',timeout=10).status_code==404
        assert requests.post(base+'/api/search',json={'ra':360,'dec':0},timeout=10).status_code==400
        checks.append('Private project paths blocked; invalid coordinate search rejected.')
        target=targets[0]
        response=requests.post(base+'/api/search',json={
            'ra':target['ra'],'dec':target['dec'],'fov':target['fov'],'detector':target['detector']},timeout=10)
        assert response.status_code==202,response.text
        job=response.json()['id']
        started=time.monotonic()
        while time.monotonic()-started<240:
            result=requests.get(base+'/api/jobs/'+job,timeout=20).json()
            print(result['status'],result.get('message',''),flush=True)
            if result['status']=='error': raise RuntimeError(result['message'])
            if result['status']=='done': break
            time.sleep(2)
        else: raise RuntimeError('Live archive job timed out')
        frames=result['result']['frames']
        assert len(frames)>=2
        assert all(f['wavelength_um'] is not None for f in frames)
        checks.append(f"Live Barnard’s Star search completed through POST /api/search and job polling: {len(frames)} real aligned exposures, with measured wavelengths.")
        report='# HTTP and live archive verification\n\n'+datetime.now(timezone.utc).isoformat()+'\n\n'
        report+='\n'.join('- '+line for line in checks)
        report+='\n\nNo browser was driven by this test. Visual layout and browser interactions remain unverified.\n'
        (ROOT/'docs/SMOKE_TEST.md').write_text(report,encoding='utf-8')
        print(report,flush=True)
    finally:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill();process.wait()


if __name__=='__main__':main()
