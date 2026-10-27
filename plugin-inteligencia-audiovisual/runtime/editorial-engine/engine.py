"""Motor audiovisual local. Tempos de segmentos em origem; eventos em saída."""
import argparse, hashlib, json, math, pathlib, subprocess, tempfile
from fractions import Fraction

def run(args):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-6000:])
    return p.stdout

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',path]))

def write(path,data):
    pathlib.Path(path).parent.mkdir(parents=True,exist_ok=True)
    pathlib.Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2))

def inspect(path):
    m=probe(path)
    r={'metadata':m,'scene_candidates':[], 'silence_candidates':[], 'warning':'Candidatos numéricos exigem revisão editorial; não são cortes aprovados.'}
    for name,args in [('scene',['-vf',"select=gt(scene\\,0.32),showinfo",'-an']),('audio',['-af','silencedetect=n=-35dB:d=0.4,volumedetect','-vn'])]:
        if name=='audio' and not any(x['codec_type']=='audio' for x in m['streams']):
            r['audio_log']='Sem faixa de áudio';continue
        p=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),*args,'-f','null','-'],capture_output=True,text=True)
        if p.returncode: raise RuntimeError(p.stderr[-3000:])
        r[name+'_log']=p.stderr
    return r

def number(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def validate(plan):
    if plan.get('version')!=1: raise ValueError('version deve ser 1')
    fps=Fraction(str(plan['fps']))
    if not 1<=fps<=120: raise ValueError('FPS inválido')
    for k in ('width','height'):
        if type(plan[k]) is not int or not 64<=plan[k]<=4096 or plan[k]%2: raise ValueError('Dimensões pares entre 64 e 4096')
    total=0
    if not plan.get('segments'): raise ValueError('Timeline vazia')
    for s in plan['segments']:
        if not all(number(s[k]) for k in ('in','out')) or not 0<=s['in']<s['out']: raise ValueError('Intervalo inválido')
        if not s.get('reason'): raise ValueError('Segmento precisa de justificativa')
        if not pathlib.Path(s['source']).is_file(): raise ValueError('Mídia ausente: '+s['source'])
        m=probe(s['source'])
        if not any(x['codec_type']=='video' for x in m['streams']): raise ValueError('Segmento exige vídeo')
        if s['out']>float(m['format']['duration'])+.001: raise ValueError('Segmento além da mídia')
        total+=round((s['out']-s['in'])*float(fps))/float(fps)
    for e in plan.get('events',[]):
        if e.get('type') not in ('title','caption','progress'): raise ValueError('Evento não implementado')
        if not all(number(e[k]) for k in ('start','end')) or not 0<=e['start']<e['end']<=total+.001: raise ValueError('Evento fora da timeline')
        if e['type']!='progress' and (not isinstance(e.get('text'),str) or not e['text'].strip()): raise ValueError('Texto vazio')
        if e.get('position','bottom') not in ('top','bottom'): raise ValueError('Posição não suportada')
    if plan.get('music'):
        if not pathlib.Path(plan['music']['source']).is_file() or not plan['music'].get('license'): raise ValueError('Música exige mídia e licença')
    return total

def ass_time(s):
    n=round(s*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'

def safe_ass(s):
    return s.replace('\\','／').replace('{','(').replace('}',')').replace('\r','').replace('\n','\\N')

def subtitles(plan,path):
    w,h=plan['width'],plan['height'];size=round(w*.052)
    head=f'''[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Main,DejaVu Sans,{size},&H00FFFFFF,&H0000CCFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,{round(w*.1)},{round(w*.1)},{round(h*.15)},1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
    lines=[]
    for e in plan.get('events',[]):
        if e['type']=='progress':
            x,y=round(w*.1),round(h*.88);length=round(w*.8);ms=round((e['end']-e['start'])*1000)
            tags=f'{{\\an7\\pos({x},{y})\\bord0\\shad0\\1c&H88CC88&\\clip({x},{y},{x+1},{y+6})\\t(0,{ms},\\clip({x},{y},{x+length},{y+6}))\\p1}}'
            lines.append(f"Dialogue: 0,{ass_time(e['start'])},{ass_time(e['end'])},Main,,0,0,0,,{tags}m 0 0 l {length} 0 l {length} 5 l 0 5")
            continue
        y=round(h*(.15 if e.get('position')=='top' else .80))
        tag=f'{{\\an5\\pos({w//2},{y})\\fad(120,120)}}'
        if e['type']=='title':tag=f'{{\\an5\\move({w//2},{y+25},{w//2},{y},0,240)\\fad(100,140)\\fscx95\\fscy95\\t(0,240,\\fscx100\\fscy100)}}'
        lines.append(f"Dialogue: 1,{ass_time(e['start'])},{ass_time(e['end'])},Main,,0,0,0,,{tag}{safe_ass(e['text'])}")
    pathlib.Path(path).write_text(head+'\n'.join(lines),encoding='utf-8')

def render(plan,output,cache=None):
    total=validate(plan);output=pathlib.Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    sources={pathlib.Path(s['source']).resolve() for s in plan['segments']}
    if plan.get('music'):sources.add(pathlib.Path(plan['music']['source']).resolve())
    if output in sources:raise ValueError('Não sobrescrever original')
    if output.exists():raise ValueError('Saída já existe; escolha arquivo novo')
    cache=pathlib.Path(cache or output.parent/'.render-cache');cache.mkdir(parents=True,exist_ok=True)
    w,h,fps=plan['width'],plan['height'],str(plan['fps']);chunks=[];hits=0
    for s in plan['segments']:
        src=pathlib.Path(s['source']).resolve();st=src.stat()
        key=hashlib.sha256(json.dumps([str(src),st.st_size,st.st_mtime_ns,s,w,h,fps,'renderer-v1']).encode()).hexdigest()
        chunk=cache/(key+'.mp4')
        if chunk.exists():hits+=1
        else:
            n=round((s['out']-s['in'])*float(Fraction(fps)));dur=n/float(Fraction(fps))
            audio=any(x['codec_type']=='audio' for x in probe(src)['streams'])
            args=['ffmpeg','-v','error','-ss',s['in'],'-i',src]
            if not audio:args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
            vf=f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},setpts=PTS-STARTPTS'
            af=f'aresample=48000,asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={max(0,dur-.008)}:d=0.008'
            args+=['-t',dur,'-map','0:v:0','-map','0:a:0' if audio else '1:a:0','-vf',vf,'-af',af,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2','-y',chunk]
            run(args)
        chunks.append(chunk)
    with tempfile.TemporaryDirectory(prefix='video-render-') as td:
        td=pathlib.Path(td); listing=td/'concat.txt'
        listing.write_text(''.join("file '"+str(x).replace("'","'\\''")+"'\n" for x in chunks))
        joined=td/'joined.mp4';run(['ffmpeg','-v','error','-f','concat','-safe','0','-i',listing,'-c','copy','-y',joined])
        ass=td/'titles.ass';subtitles(plan,ass)
        vf=f'ass={ass}'
        args=['ffmpeg','-v','error','-i',joined]
        if plan.get('music'):
            args+=['-stream_loop','-1','-i',plan['music']['source'],'-filter_complex',f'[0:a]asplit=2[voice][side];[1:a]volume=0.12[m];[m][side]sidechaincompress=threshold=0.025:ratio=6:attack=20:release=350[duck];[voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]','-map','0:v','-map','[a]']
        else:args+=['-map','0:v','-map','0:a','-af','alimiter=limit=0.95']
        args+=['-vf',vf,'-t',total,'-c:v','libx264','-threads','2','-preset','fast','-crf',str(plan.get('crf',18)),'-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',output]
        run(args)
    report={'output':str(output),'duration_expected':total,'cache_hits':hits,'segments':len(chunks),'qc':qc(output)}
    write(str(output)+'.report.json',report);return report

def qc(path):
    m=probe(path);run(['ffmpeg','-v','error','-i',path,'-f','null','-'])
    audio=['-af','ebur128=peak=true'] if any(x['codec_type']=='audio' for x in m['streams']) else []
    p=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-vf','blackdetect=d=0.1:pix_th=0.1,freezedetect=n=-50dB:d=1',*audio,'-f','null','-'],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    return {'decode':'passed','metadata':m,'black_freeze_loudness_log':p.stderr,'perceptual_review':'pending: áudio integral, sentido, cortes de fonemas, legibilidade e sincronismo humano','automatic_flags_are_candidates':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['inspect','validate','render','qc','subtitles']);p.add_argument('input');p.add_argument('output',nargs='?');a=p.parse_args()
    try:
        if a.command in ('render','validate','subtitles'):
            plan=json.loads(pathlib.Path(a.input).read_text())
            if a.command=='validate':result={'duration':validate(plan),'status':'valid'}
            elif a.command=='subtitles':validate(plan);subtitles(plan,a.output);result={'ass':a.output}
            else:result=render(plan,a.output)
        else:result=inspect(a.input) if a.command=='inspect' else qc(a.input)
        if a.output and a.command in ('inspect','qc'):write(a.output,result)
        else:print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,RuntimeError,OSError,TypeError) as e:p.exit(1,f'Erro: {e}\n')
if __name__=='__main__':main()
