"""Native-frame and encoded-audio verification of the actual delivery."""
import csv,hashlib,json,pathlib,re,subprocess,sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate,correlation_lags
from PIL import Image,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[1]
WORK=pathlib.Path("/workspace/work/sal-amargo-v2")
def command(a):return subprocess.check_output([str(x) for x in a],stderr=subprocess.STDOUT)
def main():
    video=ROOT/"sal-amargo-v2.mp4";qc=ROOT/"qc";WORK.mkdir(parents=True,exist_ok=True)
    probe=json.loads(command(["ffprobe","-v","error","-show_streams","-show_format","-of","json",video]))
    v=next(s for s in probe["streams"] if s["codec_type"]=="video")
    a=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    assert (v["width"],v["height"],v["r_frame_rate"],int(v["nb_frames"]))==(1080,1920,"30/1",900)
    assert abs(float(v["duration"])-30)<1/30
    assert abs(float(a["duration"])-30)<1/30
    times=json.loads(command(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","frame=best_effort_timestamp_time","-of","json",video]))["frames"]
    pts=np.array([float(f["best_effort_timestamp_time"]) for f in times])
    assert len(pts)==900 and np.max(np.abs(pts-np.arange(900)/30))<1e-5
    command(["ffmpeg","-v","error","-i",video,"-f","null","-"])
    signal=WORK/"native-signalstats.txt"
    command(["ffmpeg","-v","error","-i",video,"-vf",
       "signalstats,metadata=print:file="+str(signal),"-an","-f","null","-"])
    rows=[];current=None
    for line in signal.read_text().splitlines():
        if line.startswith("frame:"):
            if current:rows.append(current)
            m=re.search(r"frame:(\d+).*pts_time:([\d.]+)",line)
            current={"frame":int(m[1]),"time_s":float(m[2])}
        elif current is not None and line.startswith("lavfi.signalstats."):
            k,x=line.split("=",1)
            if k.rsplit(".",1)[-1] in ("YAVG","YDIF","SATAVG"):current[k.rsplit(".",1)[-1]]=float(x)
    if current:rows.append(current)
    assert len(rows)==900
    with (qc/"native-frames.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    sr,source=wavfile.read(ROOT/"assets/audio/voice-stem.wav")
    final=np.frombuffer(command(["ffmpeg","-v","error","-i",video,"-vn","-ar","48000",
          "-ac","1","-f","f32le","-"]),np.float32)
    lags=[]
    for lo,hi in [(0,6),(22,28)]:
        xx=final[round(lo*sr):round(hi*sr)].astype(float)
        yy=source[round(lo*sr):round(hi*sr),0].astype(float)
        corr=correlate(xx,yy,mode="full",method="fft");lag=correlation_lags(len(xx),len(yy))
        mask=np.abs(lag)<=2400;best=int(lag[mask][np.argmax(corr[mask])])
        lags.append(dict(window_s=[lo,hi],lag_samples=best,lag_ms=best/sr*1000))
    assert max(abs(x["lag_samples"]) for x in lags)<=48
    dest=qc/"encoded-samples";dest.mkdir(exist_ok=True)
    command(["ffmpeg","-v","error","-i",video,"-vf","fps=3,scale=270:480","-q:v","3","-y",dest/"sample-%03d.jpg"])
    ims=sorted(dest.glob("sample-*.jpg"))
    for start in range(0,len(ims),12):
        sheet=Image.new("RGB",(1080,3*505),"#e7ece3");d=ImageDraw.Draw(sheet)
        for i,p in enumerate(ims[start:start+12]):
            x=i%4*270;y=i//4*505;sheet.paste(Image.open(p),(x,y))
            d.text((x+5,y+482),f"{(start+i+.5)/3:.2f}s",fill="#122e27")
        sheet.save(qc/f"encoded-contact-{start//12:02}.jpg",quality=94)
    scenes=json.loads((ROOT/"edl.json").read_text())["scenes"]
    cuts=[s["start_frame"] for s in scenes[1:]]
    frames=sorted(set([0,899]+[x for c in cuts for x in [c-1,c,c+1,c+5]]))
    expr="+".join("eq(n,"+str(x)+")" for x in frames)
    native=qc/"boundary-frames";native.mkdir(exist_ok=True)
    command(["ffmpeg","-v","error","-i",video,"-vf","select='"+expr+"'","-fps_mode","vfr",
             "-q:v","2","-y",native/"frame-%03d.jpg"])
    for i,p in enumerate(sorted(native.glob("frame-*.jpg"))):p.rename(native/f"native-{frames[i]:04}.jpg")
    for start in range(0,len(frames),8):
        sheet=Image.new("RGB",(1080,2*505),"#e7ece3");d=ImageDraw.Draw(sheet)
        for i,f in enumerate(frames[start:start+8]):
            x=i%4*270;y=i//4*505;im=Image.open(native/f"native-{f:04}.jpg").resize((270,480))
            sheet.paste(im,(x,y));d.text((x+5,y+482),f"frame {f} / {f/30:.3f}s",fill="#122e27")
        sheet.save(qc/f"boundary-contact-{start//8:02}.jpg",quality=94)
    command(["ffmpeg","-v","error","-ss","6.1","-i",video,"-frames:v","1","-q:v","2","-y",ROOT/"poster.jpg"])
    source_checks=json.loads((qc/"source_checks.json").read_text())
    result=dict(native_decoded_frames=900,cfr_30="passed",duration_video_s=float(v["duration"]),
       duration_audio_s=float(a["duration"]),max_frame_pts_error_s=float(np.max(np.abs(pts-np.arange(900)/30))),
       full_decode="passed",encoded_audio_voice_correlation=lags,
       audio_lag_difference_samples=lags[1]["lag_samples"]-lags[0]["lag_samples"],
       min_native_luma_mean=min(x["YAVG"] for x in rows),sampled_encoded_frames=len(ims),
       extracted_boundary_frames=len(frames),listening_review="not_performed",
       motion_playback_review="not_performed",phrase_sync="approximate; no word-level approval",
       product_microtext="unverified where unreadable in original",
       actual_video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
       technical_note="Correlation measures audio-bus alignment; it does not validate semantic caption timing.",
       source_checks=source_checks)
    (qc/"export_checks.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="source_checks"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
