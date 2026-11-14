"""Render real aligned data for human inspection; optional Pillow dependency."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


def main():
    targets=json.loads((ROOT/'public/data/targets.json').read_text(encoding='utf-8'))
    canvas=Image.new('RGB',(1100,1350),'#080d16')
    draw=ImageDraw.Draw(canvas)
    try:
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
        small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    except OSError: font=small=ImageFont.load_default()
    draw.text((25,20),'Planet X · SPHEREx / real-observation data inspection',font=font,fill='#b6efd5')
    draw.text((25,52),'First and last wavelength-matched frames · North up / East left · shared stretch per field',font=small,fill='#8c9aaa')
    for row,target in enumerate(targets):
        data=json.loads((ROOT/'public/data'/f"{target['id']}.json").read_text(encoding='utf-8'))
        frames=data['frames']
        groups=[[f for f in frames if abs(f['wavelength_um']/r['wavelength_um']-1)<=.05+1e-10] for r in frames]
        selected=max(groups,key=lambda g:(g[-1]['mjd']-g[0]['mjd'])*100+len(g))
        arrays=[np.array([np.nan if x is None else x for x in f['pixels']]).reshape(data['height'],data['width']) for f in selected]
        values=np.concatenate([a[np.isfinite(a)] for a in arrays])
        low,high=np.percentile(values,[8,99.7])
        y=100+row*240
        draw.text((25,y+30),target['name'],font=font,fill='#edf2f4')
        draw.text((25,y+65),f"{data['detector']} · {len(selected)} matched frames",font=small,fill='#8c9aaa')
        draw.text((25,y+90),f"{selected[-1]['mjd']-selected[0]['mjd']:.1f} day baseline",font=small,fill='#8c9aaa')
        for col,(f,array) in enumerate([(selected[0],arrays[0]),(selected[-1],arrays[-1])]):
            linear=np.maximum(0,(array-low)/max(1e-9,high-low))
            display=np.clip(np.arcsinh(linear*18)/np.arcsinh(18),0,1)
            display=np.nan_to_num(display)
            pixels=(display*255).astype('uint8')
            image=Image.fromarray(np.flipud(pixels)).resize((200,200),Image.Resampling.NEAREST).convert('RGB')
            x=340+col*350
            canvas.paste(image,(x,y))
            draw.text((x,y+205),f"{f['date'][:10]} · {f['wavelength_um']:.3f} µm",font=small,fill='#c7d4d9')
    draw.text((25,1320),'Quick-look data, not a motion/variability measurement. Dark pixels include masks. See SCIENCE.md.',font=small,fill='#8c9aaa')
    canvas.save(ROOT/'docs/target-preview.png')


if __name__=='__main__':main()
