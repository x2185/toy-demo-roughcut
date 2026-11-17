"""Render a reviewed edit list with FFmpeg; no cloud service or ML dependency."""
import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],encoding='utf-8'))

def display_dimensions(stream):
    rotation=next((x['rotation'] for x in stream.get('side_data_list',[]) if 'rotation' in x),float(stream.get('tags',{}).get('rotate',0)))
    w,h=stream['width'],stream['height']
    return (h,w) if round(abs(rotation))%180==90 else (w,h)

def validate_clips(clips,duration,fps=30,allow_reorder=False):
    if not clips:raise ValueError('The edit list is empty')
    result=[]; previous_end=0
    for clip in clips:
        a,b,speed=float(clip['start']),float(clip['end']),float(clip.get('speed',1))
        if not all(math.isfinite(x) for x in [a,b,speed]):raise ValueError('Non-finite timing')
        if not (0<=a<b<=duration+0.001) or not (0.25<=speed<=4):raise ValueError(f'Invalid range or speed: {clip}')
        if not allow_reorder and a<previous_end-0.001:raise ValueError('Overlapping/reordered source ranges require allow_reorder=true')
        frames=round((b-a)/speed*fps)
        if frames<1:raise ValueError('Clip shorter than one output frame')
        result.append(dict(clip,start=a,end=b,speed=speed,frames=frames))
        previous_end=b
    return result

def atempo(speed):
    filters=[]
    while speed>2:filters.append('atempo=2'); speed/=2
    while speed<0.5:filters.append('atempo=0.5'); speed/=0.5
    return ','.join(filters+[f'atempo={speed:.9f}'])

def run(cmd):subprocess.run(cmd,check=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan',type=Path)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise SystemExit('Install FFmpeg and ffprobe and add them to PATH')
    plan=json.loads(args.plan.read_text(encoding='utf-8-sig'))
    base=args.plan.resolve().parent
    source=Path(plan['source']); source=source if source.is_absolute() else base/source
    target=Path(plan['output']); target=target if target.is_absolute() else base/target
    if source.resolve()==target.resolve():raise ValueError('Output must differ from source')
    if target.exists():raise FileExistsError(f'Choose a new output name: {target}')
    if target.with_suffix('.edit.json').exists():raise FileExistsError(f'Edit record already exists: {target.with_suffix(".edit.json")}')
    info=probe(source); video=next(x for x in info['streams'] if x['codec_type']=='video')
    has_audio=any(x['codec_type']=='audio' for x in info['streams'])
    duration=float(info['format']['duration']); fps=float(plan.get('fps',30))
    if not math.isfinite(fps) or not 1<=fps<=120:raise ValueError('Invalid fps')
    clips=validate_clips(plan['clips'],duration,fps,plan.get('allow_reorder',False))
    color=plan.get('color_mode','sdr'); audio=plan.get('audio','keep')
    if color not in ['sdr','preserve-hdr'] or audio not in ['keep','mute']:raise ValueError('Unsupported color/audio mode')
    transfer=video.get('color_transfer'); hdr=transfer in ['arib-std-b67','smpte2084']
    if color=='preserve-hdr' and not hdr:raise ValueError('Source is not identified as supported HLG/PQ HDR')
    w,h=display_dimensions(video)
    summary={'source':str(source),'output':str(target),'dimensions':[w,h],'fps':fps,'expected_duration':sum(c['frames'] for c in clips)/fps,'clips':clips,'color_mode':color,'source_transfer':transfer,'audio':audio,'dolby_vision':'dynamic metadata not retained when re-encoding'}
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    if args.check_only:return
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='roughcut-',dir=target.parent) as tmp:
        temp=Path(tmp)
        for index,clip in enumerate(clips):
            vf=f"setpts=(PTS-STARTPTS)/{clip['speed']},fps={fps}"
            encoding=['-c:v','libx264','-preset','fast','-crf','18','-threads','4']
            colors=['-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709']
            if hdr and color=='sdr':
                vf+=',zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv'
            if color=='preserve-hdr':
                vf+=',format=yuv420p10le'
                encoding=['-c:v','libx265','-preset','fast','-crf','20','-x265-params',f'pools=4:frame-threads=2:log-level=error:colorprim=bt2020:transfer={transfer}:colormatrix=bt2020nc','-tag:v','hvc1']
                colors=['-color_primaries','bt2020','-color_trc',transfer,'-colorspace','bt2020nc']
            else:vf+=',format=yuv420p'
            # Per-part VIDEO ONLY. AAC per part adds encoder padding and accumulates gaps.
            run(['ffmpeg','-v','error','-n','-ss',str(clip['start']),'-t',str(clip['end']-clip['start']),'-i',str(source),'-map','0:v:0','-an','-vf',vf,'-frames:v',str(clip['frames']),*encoding,*colors,'-metadata:s:v:0','rotate=0',str(temp/f'part{index:03}.mp4')])
            print(f'Rendered {index+1}/{len(clips)}',flush=True)
        listing=temp/'concat.txt'
        listing.write_text(''.join(f"file 'part{i:03}.mp4'\n" for i in range(len(clips))),encoding='utf-8')
        inputs=['-f','concat','-safe','0','-i',str(listing)]
        sound=['-an']
        if has_audio and audio=='keep':
            chains=[]
            for i,c in enumerate(clips):
                chains.append(f"[0:a:0]atrim=start={c['start']}:end={c['end']},asetpts=PTS-STARTPTS,{atempo(c['speed'])},apad,atrim=duration={c['frames']/fps}[a{i}]")
            chains.append(''.join(f'[a{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=0:a=1[out]')
            graph=temp/'audio.txt'; graph.write_text(';'.join(chains),encoding='utf-8')
            wav=temp/'audio.wav'
            run(['ffmpeg','-v','error','-n','-i',str(source),'-filter_complex',';'.join(chains),'-map','[out]','-ar','48000','-c:a','pcm_s16le',str(wav)])
            inputs+=['-i',str(wav)]
            sound=['-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','192k','-shortest']
        run(['ffmpeg','-v','error','-n',*inputs,'-c:v','copy',*sound,'-movflags','+faststart',str(target)])
    actual=probe(target); v=next(s for s in actual['streams'] if s['codec_type']=='video')
    if (v['width'],v['height'])!=(w,h):raise RuntimeError('Output dimensions changed unexpectedly')
    if abs(float(actual['format']['duration'])-summary['expected_duration'])>max(0.15,2/fps):raise RuntimeError('Output duration exceeds tolerance')
    run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'])
    summary['actual_duration']=float(actual['format']['duration'])
    target.with_suffix('.edit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('VERIFIED',target,flush=True)

if __name__=='__main__':main()
