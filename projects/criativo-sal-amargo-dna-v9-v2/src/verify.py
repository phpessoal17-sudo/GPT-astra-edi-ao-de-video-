"""Observable timeline, reproducibility and voice-preservation checks."""
import hashlib,json,pathlib,subprocess,sys
import numpy as np
from scipy.io import wavfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
import render as r
def main():
    scenes=r.EDL["scenes"]
    assert scenes[0]["start_frame"]==0 and scenes[-1]["end_frame"]==900
    assert all(a["end_frame"]==b["start_frame"] for a,b in zip(scenes,scenes[1:]))
    assert all(s["start_frame"]<s["end_frame"] for s in scenes)
    assert len(scenes)==len(r.CAP)==16
    # Random-access evaluation must not depend on previous animation state.
    r.W,r.H,r.S=360,640,1/3
    a=hashlib.sha256(r.image_at(192).tobytes()).hexdigest()
    for f in [731,0,449,129]:r.image_at(f)
    assert hashlib.sha256(r.image_at(192).tobytes()).hexdigest()==a
    for s in scenes:
        for f in [s["start_frame"],s["end_frame"]-1]:
            im=np.asarray(r.image_at(f))
            assert im.shape==(640,360,3)
            assert np.mean(im)>10 and np.std(im)>10
    src=r.run(["ffmpeg","-v","error","-i",ROOT/"assets/audio/narration-original.wav",
               "-ar","48000","-ac","1","-f","f32le","-"])
    voice=np.frombuffer(src,np.float32)*.95
    sr,stem=wavfile.read(ROOT/"assets/audio/voice-stem.wav")
    assert sr==48000 and stem.shape==(1440000,2)
    assert len(voice)==1390304
    assert np.max(np.abs(stem[:len(voice),0]-voice))<1e-6
    assert np.max(np.abs(stem[len(voice):]))==0
    prov=json.loads((ROOT/"references/provenance.json").read_text())
    for item in prov["assets"]:
        assert hashlib.sha256((ROOT/item["path"]).read_bytes()).hexdigest()==item["sha256"]
    result=dict(timeline_partition="passed",random_access_determinism="passed",
       scene_boundary_frames="passed",original_assets_hashes="passed",
       speech_elapsed_time_preserved="passed",speech_speed=1,
       voice_pcm_error_max=float(np.max(np.abs(stem[:len(voice),0]-voice))),
       voice_source_duration_s=len(voice)/48000,
       phrase_alignment="approximate; not independently verified word by word",
       listening_review="not_performed")
    (ROOT/"qc/source_checks.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
