"""Probe a source and create timestamped contact sheets. Pillow is required."""
import argparse,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float)
    p.add_argument('--step',type=float,default=2)
    a=p.parse_args()
    if a.step<=0 or a.start<0 or (a.end is not None and a.end<=a.start):p.error('Invalid sampling range')
    a.output.mkdir(parents=True,exist_ok=True)
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(a.source)],encoding='utf-8'))
    (a.output/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    cmd=['ffmpeg','-v','error','-ss',str(a.start),'-i',str(a.source)]
    if a.end is not None:cmd+=['-t',str(a.end-a.start)]
    cmd+=['-vf',f'fps=1/{a.step},scale=180:320:force_original_aspect_ratio=decrease,pad=180:320:(ow-iw)/2:(oh-ih)/2','-pix_fmt','rgb24','-f','rawvideo','-threads','1','-']
    frame_bytes=180*320*3; page=0; idx=0; canvas=None
    with subprocess.Popen(cmd,stdout=subprocess.PIPE) as proc:
        while True:
            data=proc.stdout.read(frame_bytes)
            if not data:break
            if len(data)!=frame_bytes:raise RuntimeError('Incomplete decoded frame')
            if idx%20==0:canvas=Image.new('RGB',(900,4*345))
            pos=idx%20; canvas.paste(Image.frombytes('RGB',(180,320),data),(pos%5*180,pos//5*345))
            ImageDraw.Draw(canvas).text((pos%5*180+4,pos//5*345+323),f'~{a.start+idx*a.step:.2f}s',fill='white')
            idx+=1
            if idx%20==0:canvas.save(a.output/f'sheet-{page:03}.jpg');page+=1
        if idx%20:canvas.save(a.output/f'sheet-{page:03}.jpg')
        if proc.wait()!=0:raise RuntimeError('FFmpeg sampling failed')
    print(f'{idx} frames; labels are approximate sampling-grid times, not exact cut boundaries.')

if __name__=='__main__':main()
