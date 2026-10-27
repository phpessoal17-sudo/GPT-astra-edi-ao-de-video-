"""Masterização conservadora SDR. Não reconstrói detalhe nem separa stems.

CLI: python src/mastering.py PLAN.json OUTPUT.mp4
"""
import argparse,hashlib,json,math,pathlib,re,subprocess,tempfile
from fractions import Fraction

def execute(args):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-8000:])
    return p

def probe(path,count=False):
    args=['ffprobe','-v','error']
    if count:args+=['-count_frames']
    return json.loads(execute(args+['-show_format','-show_streams','-of','json',path]).stdout)

def measure(path):
    p=execute(['ffmpeg','-hide_banner','-i',path,'-map','0:a:0','-vn','-af','loudnorm=I=-16.5:TP=-2:LRA=11:print_format=json','-f','null','-'])
    match=re.search(r'\{\s*"input_i".*?\}',p.stderr,re.S)
    if not match:raise ValueError('Medição de loudness ausente')
    raw=json.loads(match.group());return {'integrated_lufs':float(raw['input_i']),'true_peak_dbtp':float(raw['input_tp']),'lra_lu':float(raw['input_lra']),'threshold_lufs':float(raw['input_thresh'])}

def gain_for(measurement,target=-16.5,ceiling=-2):
    i,p=measurement['integrated_lufs'],measurement['true_peak_dbtp']
    if not math.isfinite(i) or not math.isfinite(p):raise ValueError('Áudio silencioso ou medição inválida; requer decisão explícita')
    requested=target-i;gain=min(requested,ceiling-p)
    return {'requested_gain_db':requested,'applied_gain_db':gain,'predicted_lufs':i+gain,'predicted_true_peak_dbtp':p+gain,'peak_constrained':gain<requested-.001}

def validate(plan,meta):
    if plan.get('version')!=2:raise ValueError('version deve ser 2')
    if plan.get('layout','portrait') not in ['portrait','landscape']:raise ValueError('Layout inválido')
    v=next((s for s in meta['streams'] if s['codec_type']=='video'),None)
    if not v:raise ValueError('Fonte sem vídeo')
    if not any(s['codec_type']=='audio' for s in meta['streams']):raise ValueError('Este fluxo exige faixa de áudio; use o compositor para material mudo')
    if v.get('color_transfer') in ['smpte2084','arib-std-b67']:raise ValueError('HDR requer fluxo próprio; não aplicar preset SDR')
    if v.get('color_space')!='bt709' or v.get('color_range')!='tv':
        raise ValueError('Este preset exige fonte identificada como Rec.709 limited; resolva a gestão de cor antes do render')
    if Fraction(v['avg_frame_rate'])<=0:raise ValueError('FPS inválido')
    w,h=plan.get('width',1080),plan.get('height',1920)
    if any(type(x)!=int or x<64 or x>4096 or x%2 for x in [w,h]):raise ValueError('Dimensões pares entre 64 e 4096')
    if plan.get('layout','portrait')=='portrait' and abs(w/h-v['width']/v['height'])>.001:raise ValueError('A proporção deve ser preservada; use landscape para canvas horizontal')
    if plan.get('profile','gentle') not in ['gentle','fidelity']:raise ValueError('Perfil inválido')
    for key,lo,hi,default in [('target_lufs',-24,-12,-16.5),('peak_ceiling_dbtp',-6,-1,-2),('crf',12,24,16)]:
        x=plan.get(key,default)
        if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not lo<=x<=hi:raise ValueError('Parâmetro inválido: '+key)
    return v

def video_filter(plan):
    chain=[]
    if plan.get('profile','gentle')=='gentle':
        chain+=['deblock=filter=weak:block=8:alpha=0.025:beta=0.015:gamma=0.015:delta=0.015','hqdn3d=0.35:0.25:0.25:0.2']
    w,h=plan.get('width',1080),plan.get('height',1920)
    chain += [f'zscale=w={w}:h={h}:filter=spline36:dither=error_diffusion']
    if plan.get('profile','gentle')=='gentle':chain+=['unsharp=5:5:0.18:5:5:0']
    chain+=['setsar=1','format=yuv420p']
    return ','.join(chain)

def master(plan,output):
    source=pathlib.Path(plan['source']).resolve();output=pathlib.Path(output).resolve()
    if not source.is_file():raise ValueError('Fonte ausente')
    if output==source or output.exists():raise ValueError('Saída deve ser nova; original protegido')
    meta=probe(source);v=validate(plan,meta);duration=float(v.get('duration',meta['format']['duration']))
    input_hash=hashlib.sha256(source.read_bytes()).hexdigest();levels=measure(source);gain=gain_for(levels,plan.get('target_lufs',-16.5),plan.get('peak_ceiling_dbtp',-2))
    output.parent.mkdir(parents=True,exist_ok=True)
    report={'version':2,'source':str(source),'source_sha256':input_hash,'plan':plan,'input_audio':levels,'gain':gain,'source_video':v,'claims':{'neural_super_resolution':False,'new_detail_recovered':False,'voice_separated':False,'semantic_cuts':False,'perceptual_audio_approval':False}}
    with tempfile.TemporaryDirectory(prefix='master-',dir=output.parent) as tmp:
        target=pathlib.Path(tmp)/'encoded.mp4'
        args=['ffmpeg','-v','error','-filter_threads','2','-filter_complex_threads','2','-i',source]
        if plan.get('layout','portrait')=='landscape':
            # A subdued frame-derived background; full original is fitted, never stretched/cropped.
            w,h=plan.get('width',1920),plan.get('height',1080)
            filt=f'[0:v]split=2[bg][fg];[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},gblur=sigma=45,eq=brightness=-0.16:saturation=0.65[back];[fg]scale=-2:{h}:flags=spline[front];[back][front]overlay=(W-w)/2:0,setsar=1,format=yuv420p[v]'
            args+=['-filter_complex',filt,'-map','[v]']
            report['video_filter']=filt
        else:
            filt=video_filter(plan);args+=['-vf',filt,'-map','0:v:0'];report['video_filter']=filt
        af=f"volume={gain['applied_gain_db']:.6f}dB,aresample=48000,apad,atrim=duration={duration:.9f}"
        args+=['-map','0:a:0','-af',af,'-t',f'{duration:.9f}','-fps_mode','passthrough','-c:v','libx264','-preset','slow','-crf',str(plan.get('crf',16)),'-threads','2','-pix_fmt','yuv420p','-color_range','tv','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709','-c:a','aac','-profile:a','aac_low','-b:a','256k','-ar','48000','-movflags','+faststart','-map_metadata','0','-n',target]
        report['command']=list(map(str,args));execute(args)
        execute(['ffmpeg','-v','error','-i',target,'-f','null','-'])
        final=probe(target,True);ov=next(s for s in final['streams'] if s['codec_type']=='video');oa=next(s for s in final['streams'] if s['codec_type']=='audio');outlevel=measure(target)
        expected_frames=int(v.get('nb_frames',round(duration*float(Fraction(v['avg_frame_rate'])))))
        checks={'full_decode':True,'frame_count_preserved':int(ov['nb_read_frames'])==expected_frames,'fps_preserved':Fraction(ov['avg_frame_rate'])==Fraction(v['avg_frame_rate']),'dimensions_match':(ov['width'],ov['height'])==(plan.get('width',1080),plan.get('height',1920)),'audio_video_duration_delta_below_one_frame':abs(float(ov['duration'])-float(oa['duration']))<=1/float(Fraction(v['avg_frame_rate']))+.002,'true_peak_below_minus_1_5_dbtp':outlevel['true_peak_dbtp']<=-1.5,'loudness_within_half_lu_of_prediction':abs(outlevel['integrated_lufs']-gain['predicted_lufs'])<=.5,'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==input_hash}
        report.update({'output_audio':outlevel,'output_metadata':final,'checks':checks,'status':'technical_checks_passed' if all(checks.values()) else 'failed'})
        if not all(checks.values()):
            pathlib.Path(str(output)+'.failed.json').write_text(json.dumps(report,indent=2));raise RuntimeError('QC falhou: '+str(checks))
        target.rename(output)
    report['output']=str(output);report['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
    pathlib.Path(str(output)+'.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));return report

def main():
    p=argparse.ArgumentParser();p.add_argument('plan');p.add_argument('output');args=p.parse_args()
    try:
        r=master(json.loads(pathlib.Path(args.plan).read_text()),args.output)
        print(json.dumps({k:r[k] for k in ['output','input_audio','output_audio','checks']},indent=2))
    except (OSError,ValueError,KeyError,RuntimeError) as e:p.exit(1,f'Erro: {e}\n')
if __name__=='__main__':main()
