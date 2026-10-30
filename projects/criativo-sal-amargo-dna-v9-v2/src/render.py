"""Reproducible Motion Studio v2. Python + Pillow/NumPy/SciPy + FFmpeg.

3D torus meshes form geometric scenery; the real product remains a frontal
photographic plane. Captions follow approximate phrase anchors, never karaoke.
"""
import argparse,hashlib,json,math,os,pathlib,subprocess,sys,time
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, gaussian_filter1d

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"brief.json").read_text());EDL=json.loads((ROOT/"edl.json").read_text())
CAP=json.loads((ROOT/"captions.json").read_text())["cues"]
DNA=json.loads((ROOT/"style/v9.json").read_text())
FPS=30;DURATION=30;SR=48000;W=1080;H=1920;S=1.
DEFAULT_WORK=pathlib.Path("/workspace/work/sal-amargo-v2") if pathlib.Path("/workspace").exists() else ROOT/"work"
SCRATCH=pathlib.Path(os.environ.get("VIDEO_DNA_WORKDIR",str(DEFAULT_WORK)));SCRATCH.mkdir(parents=True,exist_ok=True)
PAL=CFG["style"]["palette"]

def run(args):
    p=subprocess.run([str(a) for a in args],capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors="replace")[-3000:])
    return p.stdout
def save(name,data):
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def clamp(t):return min(1.,max(0.,t))
def out(t):return 1-(1-clamp(t))**3
def smooth(t):t=clamp(t);return t*t*(3-2*t)
def px(v):return round(v*S)
def color(v):return tuple(bytes.fromhex(PAL.get(v,v).lstrip("#")))
def measured(t):
    pts=DNA["execution"]["motion"]["entry_curve"]
    return float(np.interp(clamp(t),[p[0] for p in pts],[p[1] for p in pts]))

@lru_cache(maxsize=150)
def font(size,serif=False,bold=True):
    path=ROOT/"assets/fonts"/("DMSerifDisplay-Italic.ttf" if serif else "Manrope.ttf")
    f=ImageFont.truetype(str(path),max(8,px(size)))
    if not serif and hasattr(f,"set_variation_by_axes"):f.set_variation_by_axes([750 if bold else 500])
    return f

def center(im,layer,x,y,alpha=1,angle=0):
    if alpha<=0:return
    if angle:layer=layer.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    if alpha<.999:
        layer=layer.copy();layer.putalpha(layer.getchannel("A").point(lambda a:round(a*clamp(alpha))))
    im.alpha_composite(layer,(round(x-layer.width/2),round(y-layer.height/2)))

@lru_cache(maxsize=160)
def text_layer(text,size,fill,serif=False,bold=True,max_width=780,outline=False):
    face=font(size,serif,bold);limit=px(max_width);words=text.split();lines=[];line=""
    for word in words:
        trial=(line+" "+word).strip()
        if face.getlength(trial)>limit and line:lines.append(line);line=word
        else:line=trial
    if line:lines.append(line)
    if len(lines)>2 and size>44:return text_layer(text,size-2,fill,serif,bold,max_width,outline)
    pad=px(12);line_h=round(face.size*1.26);ww=min(W,max(round(face.getlength(l)) for l in lines)+2*pad)
    layer=Image.new("RGBA",(max(1,ww),line_h*len(lines)+2*pad));dr=ImageDraw.Draw(layer)
    for j,line in enumerate(lines):
        x=(layer.width-face.getlength(line))/2
        if outline:dr.text((x,pad+j*line_h),line,font=face,fill=(0,0,0,0),stroke_width=max(1,px(1.4)),stroke_fill=fill)
        else:dr.text((x,pad+j*line_h),line,font=face,fill=fill)
    return layer

def label(im,text,x,y,size=64,fill="ink",serif=False,alpha=1,angle=0,width=780):
    center(im,text_layer(text,size,color(fill),serif,True,width),x,y,alpha,angle)

@lru_cache(maxsize=1)
def product():
    p=Image.open(ROOT/CFG["product_image"]["source"]).convert("RGBA")
    # Compositing matte removes stray pixels outside the photographed silhouette.
    # Source RGB, type and numbers are not repainted or programmatically replaced.
    outline=[(407,56),(448,46),(799,46),(846,61),(846,187),(816,205),(810,251),
      (854,273),(892,307),(916,355),(921,1137),(912,1180),(884,1202),(845,1215),
      (409,1214),(367,1203),(338,1184),(331,1147),(332,375),(341,329),(359,299),
      (401,270),(439,252),(439,213),(408,196)]
    m=Image.new("L",p.size);ImageDraw.Draw(m).polygon(outline,fill=255)
    m=m.filter(ImageFilter.GaussianBlur(.7));p.putalpha(ImageChops.multiply(p.getchannel("A"),m))
    return p.crop((320,35,933,1222))

@lru_cache(maxsize=36)
def sized_product(height):
    p=product();return p.resize((max(1,round(height*p.width/p.height)),height),Image.Resampling.LANCZOS)

def bottle(im,x,y,height,angle=0,alpha=1,shadow=True):
    height=max(4,round(height/4)*4);p=sized_product(height)
    if shadow:
        sh=Image.new("RGBA",p.size,(0,0,0,0));sh.putalpha(p.getchannel("A").point(lambda a:round(a*.17)))
        sh=sh.filter(ImageFilter.GaussianBlur(px(13)));center(im,sh,x+px(12),y+px(20),alpha,angle)
    center(im,p,x,y,alpha,angle)

@lru_cache(maxsize=8)
def gradient(theme):
    a,b={"cream":("cream","sage"),"sage":("sage","cream"),
         "dark":("dark","ink"),"green":("accent","dark")}[theme]
    yy,xx=np.mgrid[0:H,0:W];r=np.clip(np.sqrt(((xx/W-.43)*.8)**2+((yy/H-.43)*.74)**2),0,1)
    c1=np.array(color(a));c2=np.array(color(b))
    data=c1[None,None,:]*(1-r[:,:,None])+c2[None,None,:]*r[:,:,None]
    return Image.fromarray(np.uint8(np.clip(data,0,255))).convert("RGBA")

@lru_cache(maxsize=6)
def photo(name):
    return Image.open(ROOT/"assets/images"/name).convert("RGBA")

def photo_full(im,name,zoom=1.05,xshift=0,yshift=0):
    p=photo(name);scale=max(W/p.width,H/p.height)*zoom
    p=p.resize((round(p.width*scale),round(p.height*scale)),Image.Resampling.LANCZOS)
    center(im,p,W/2+xshift,H/2+yshift)

def rounded_card(im,source,cx,cy,width,height,radius=44,angle=0):
    p=source.copy();f=max(width/p.width,height/p.height)
    p=p.resize((round(p.width*f),round(p.height*f)),Image.Resampling.LANCZOS)
    x=(p.width-width)//2;y=(p.height-height)//2;p=p.crop((x,y,x+width,y+height))
    mask=Image.new("L",p.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,width-1,height-1),px(radius),fill=255)
    p.putalpha(mask);sh=Image.new("RGBA",p.size,(0,0,0,0));sh.putalpha(mask.point(lambda v:round(v*.14)))
    sh=sh.filter(ImageFilter.GaussianBlur(px(12)));center(im,sh,cx+px(12),cy+px(18),angle=angle);center(im,p,cx,cy,angle=angle)

def ribbon(im,t,fill="accent",cy=.64,amplitude=.12,thickness=46):
    dr=ImageDraw.Draw(im);pts=[]
    for j in range(120):
        x=W*(j/119*1.4-.2);y=H*(cy+amplitude*math.sin(j/119*3.3+t*.18))
        pts.append((x,y))
    dr.line(pts,fill=color(fill),width=px(thickness),joint="curve")

@lru_cache(maxsize=1)
def torus_model():
    u=np.arange(80)*2*np.pi/80;v=np.arange(12)*2*np.pi/12
    U,V=np.meshgrid(u,v,indexing="ij");r=1+.07*np.cos(V)
    return np.stack([r*np.cos(U),r*np.sin(U),.07*np.sin(V)],axis=-1).reshape(-1,3)

@lru_cache(maxsize=1)
def torus_faces():
    return np.array([[u*12+v,((u+1)%80)*12+v,((u+1)%80)*12+(v+1)%12,u*12+(v+1)%12]
                     for u in range(80) for v in range(12)])

def torus(im,t,cx,cy,radius,tilt=.65,alpha=220,accent=True):
    # Genuine projected 3D geometry with depth sorting and directional lighting.
    p=torus_model();a=tilt;b=.24*math.sin(t*.55);rz=.22*math.sin(t*.29)
    Rx=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Ry=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Rz=np.array([[math.cos(rz),-math.sin(rz),0],[math.sin(rz),math.cos(rz),0],[0,0,1]])
    q=p@(Rz@Ry@Rx).T*radius;depth=px(1400);k=depth/(depth+q[:,2])
    screen=np.column_stack([cx+q[:,0]*k,cy+q[:,1]*k])
    base=np.array(color("accent" if accent else "sage"))
    light=np.array([-.4,-.6,1]);light/=np.linalg.norm(light)
    ids=torus_faces();pts=q[ids]
    normal=np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0])
    normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-8)[:,None]
    shade=.48+.46*np.abs(normal@light)
    colors=np.clip(base[None,:]*shade[:,None]+np.array([22,36,30])[None,:]*(shade[:,None]**12),0,255).astype(int)
    order=np.argsort(np.mean(pts[:,:,2],axis=1))[::-1]
    polygons=screen[ids]
    layer=Image.new("RGBA",(W,H));d=ImageDraw.Draw(layer)
    for j in order:d.polygon([tuple(x) for x in polygons[j]],fill=tuple(colors[j])+(alpha,))
    im.alpha_composite(layer)

def floor(im,cy=.79,width=.77):
    layer=Image.new("RGBA",(W,H));d=ImageDraw.Draw(layer);cx=W*.48;y=H*cy;rx=W*width/2
    d.ellipse((cx-rx,y-px(32),cx+rx,y+px(48)),fill=(0,0,0,28))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(px(13))))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((cx-rx,y,cx+rx,y+px(125)),px(32),fill=(199,215,200,255))
    d.ellipse((cx-rx,y-px(37),cx+rx,y+px(37)),fill=(243,247,235,255))

def macro(im,cx,cy,width,height,area="name",angle=0):
    p=photo("product-hd-reference.png")
    crop={"name":(355,510,900,930),"brand":(351,337,902,1017),
          "bottom":(345,820,904,1118)}[area]
    rounded_card(im,p.crop(crop),cx,cy,width,height,44,angle)

def caption(im,index,local,dark=False):
    c=CAP[index];kind=EDL["scenes"][index]["kind"]
    size=102 if index<2 else 87 if kind in ("brand","cta") else 68
    serif=kind in ("opening","orbit","hero","brand","clarity")
    if kind=="cta":
        # Single caption owner; the button itself carries the spoken CTA.
        y=H*.60;w=px(750);h=px(126);layer=Image.new("RGBA",(w,h))
        dr=ImageDraw.Draw(layer);dr.rounded_rectangle((0,0,w-1,h-1),px(63),fill=color("accent"))
        center(im,layer,W*.44,y+px(18)*(1-out(local/.22)))
        label(im,c["text"],W*.44,y,60,"light",False,width=720)
        return
    fill="light" if dark else "ink";y=H*.235
    a=out(local/.12);layer=text_layer(c["text"],size,color(fill),serif,True,770)
    # A stable bounded phrase replaces the previous one; no per-word karaoke.
    center(im,layer,W*.44,y+px(15)*(1-a),.72+.28*a)

def scene_image(index,frame):
    info=EDL["scenes"][index];t=frame/FPS;local=t-info["start_s"]
    dur=info["end_s"]-info["start_s"];u=clamp(local/max(dur,.001));kind=info["kind"]
    dark=kind in ("choices","orbit","advisory","warnings");im=gradient("dark" if dark else "cream").copy()
    e=out(local/.38);bob=px(3)*math.sin(local*1.3)
    if kind=="opening":
        torus(im,t,W*.48,H*.60,px(465),.5,alpha=110)
        bottle(im,W*.53+px(30)*(1-e),H*.69,px(1450)*(1+.035*u),angle=-7+3*u)
        # Crop is purposeful; the subsequent scene resolves to the whole pack.
    elif kind=="choices":
        label(im,"escolhas",W*.54,H*.48,154,"accent",True,alpha=.48,angle=-6,width=1200)
        label(im,"escolhas",W*.48,H*.82,145,"accent",True,alpha=.40,angle=-6,width=1200)
        bottle(im,W*.10,H*.73,px(650),angle=-15,alpha=.45)
        bottle(im,W*.83,H*.64,px(680),angle=13,alpha=.5)
        bottle(im,W*.47,H*.63+px(150)*(1-measured(local/.5)),px(1000),angle=-2)
        ribbon(im,t,cy=.80,amplitude=.07,thickness=23)
    elif kind in ("lifestyle","clarity"):
        # Existing generated still, animated as image B-roll, not claimed footage.
        photo_full(im,"lifestyle-bg.png",1.045+.025*u,xshift=-px(12)*u)
        bottle(im,W*.60,H*.66,px(900+22*u),angle=1.2-.8*u)
    elif kind=="orbit":
        torus(im,t,W*.51,H*.61,px(420),.83,accent=False)
        ribbon(im,t,"accent",cy=.75,amplitude=.10,thickness=68)
        bottle(im,W*.47,H*.62+bob+px(140)*(1-e),px(1040),angle=-3+4*u)
    elif kind in ("hero","brand"):
        ribbon(im,t,cy=.64,amplitude=.20,thickness=60)
        torus(im,t,W*.50,H*.62,px(420),1.1,alpha=95)
        yy=H*.625+px(380)*(1-measured(local/.65))
        bottle(im,W*.47,yy+bob,px(1050)*(1+.025*u),angle=-3*(1-e))
    elif kind in ("macro","composition"):
        if kind=="macro":
            # Illustrative mineral texture from the previous generated asset;
            # it is scenery, not a laboratory image or physical-product proof.
            photo_full(im,"mineral-bg.png",1.03+.035*u)
            back=Image.new("RGBA",(W,round(H*.37)),color("cream")+(255,))
            im.alpha_composite(back,(0,0))
        ribbon(im,t,cy=.67,amplitude=.15,thickness=32)
        macro(im,W*.47,H*.62+px(90)*(1-e),px(875),px(870),"brand",angle=-4+3*u)
        # A large conventional focus bracket marks the supplied image, not data.
        d=ImageDraw.Draw(im);cx=W*.47;cy=H*.62;r=px(425)
        for a in (10,100,190,280):d.arc((cx-r,cy-r,cx+r,cy+r),a,a+22,fill=color("accent"),width=px(5))
    elif kind=="botanical":
        # A crop of foliage; no fictional customer testimonial or product demo.
        p=photo("lifestyle-bg.png").crop((0,0,420,1060))
        rounded_card(im,p,W*.15,H*.63,px(420),px(1190),55,angle=-7)
        torus(im,t,W*.54,H*.66,px(430),.82,alpha=130)
        bottle(im,W*.53,H*.64+bob,px(1000),angle=2)
    elif kind=="label":
        torus(im,t,W*.48,H*.62,px(415),.35,alpha=110)
        macro(im,W*.47,H*.62,px(850),px(780),"name",angle=2.2-2*u)
        # One moving arc motivates the detail reveal without painting the label.
        d=ImageDraw.Draw(im);r=px(463);cx=W*.47;cy=H*.62
        d.arc((cx-r,cy-r,cx+r,cy+r),-115,-115+310*out(local/.7),fill=color("accent"),width=px(10))
    elif kind=="pedestal":
        torus(im,t,W*.48,H*.64,px(440),.85,alpha=150)
        floor(im,.80)
        bottle(im,W*.47,H*.595+px(90)*(1-e),px(930),angle=-2+2*u)
    elif kind=="usage":
        macro(im,W*.07,H*.65,px(650),px(1000),"brand",angle=-8)
        torus(im,t,W*.69,H*.63,px(270),.65,alpha=150)
        bottle(im,W*.65,H*.65,px(840),angle=4)
    elif kind=="advisory":
        torus(im,t,W*.48,H*.62,px(425),.7,accent=False,alpha=80)
        bottle(im,W*.47,H*.63+bob,px(930))
        # Calm, legible hold within a busy visual progression.
    elif kind=="warnings":
        ribbon(im,t,"accent",cy=.58,amplitude=.24,thickness=px(42)/S)
        bottle(im,W*.22,H*.65,px(1090),angle=-9)
        macro(im,W*.75,H*.69,px(560),px(630),"name",angle=9)
    elif kind=="cta":
        ribbon(im,t,cy=.54,amplitude=.17,thickness=50)
        torus(im,t,W*.48,H*.45,px(350),.95,alpha=85)
        bottle(im,W*.47,H*.37+bob,px(770),angle=0)
    return im

def image_at(frame):
    index=next(i for i,s in enumerate(EDL["scenes"]) if s["start_frame"]<=frame<s["end_frame"])
    im=scene_image(index,frame)
    info=EDL["scenes"][index];local=frame/FPS-info["start_s"]
    if index and info["transition"]=="motivated_green_wipe" and local<.20:
        # The moving field clears fully; no flash frame or lingering root transform.
        u=out(local/.20);layer=Image.new("RGBA",(W,H));d=ImageDraw.Draw(layer)
        x=round(W*(1.35*u-.35));width=round(W*.24*(1-u))
        if width>0:d.polygon([(x-width,0),(x,0),(x+px(120),H),(x-width+px(120),H)],fill=color("accent"))
        im.alpha_composite(layer)
    # The text owner stays above the transition field throughout the phrase.
    caption(im,index,local,info["kind"] in ("choices","orbit","advisory","warnings"))
    return im.convert("RGB")

def measure(path):
    p=subprocess.run(["ffmpeg","-hide_banner","-i",str(path),"-vn","-af",
      "loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json","-f","null","-"],capture_output=True,check=True)
    s=p.stderr.decode();return json.loads(s[s.rfind("{"):s.rfind("}")+1])

def synth_audio():
    count=SR*DURATION;rng=np.random.default_rng(CFG["audio"]["seed"])
    music=np.zeros((count,2));fx=np.zeros_like(music);beat=60/CFG["audio"]["bpm"]
    def place(bus,a,at,gain=1,pan=0):
        start=round(at*SR)
        if start<0:a=a[-start:];start=0
        n=min(len(a),count-start)
        if n<=0:return
        if a.ndim==1:a=np.column_stack([a*math.sqrt((1-pan)/2),a*math.sqrt((1+pan)/2)])
        bus[start:start+n]+=a[:n]*gain
    def tone(midi,d=.8):
        f=440*2**((midi-69)/12);tt=np.arange(round(d*SR))/SR
        attack=1-np.exp(-tt*350)
        return (np.sin(2*np.pi*f*tt+.7*np.exp(-tt*17)*np.sin(2*np.pi*f*2*tt))
             +.19*np.sin(2*np.pi*f*3*tt)*np.exp(-tt*10))*np.exp(-tt*5)*attack
    chords=[(0,12,[60,64,67,71]),(12,24,[57,60,64,67]),(24,36,[53,57,60,64]),
            (36,48,[55,59,62,69]),(48,56,[60,64,67,74])]
    for lo,hi,notes in chords:
        for b in range(lo,hi):
            if b%2==0:place(music,tone(notes[0]-24,.9),b*beat,.17)
            if b%2==0:
                for j,o in enumerate([0,.75,1.5]):
                    if b+o<hi:place(music,tone(notes[(b//2+j)%4]+12,1.1),(b+o)*beat,.10 if j else .13,(-.3,.3,0)[j])
        tt=np.arange(round((hi-lo)*beat*SR))/SR;pad=np.zeros_like(tt)
        for n in notes:
            freq=440*2**((n-69)/12);pad+=np.sin(2*np.pi*freq*tt+.04*np.sin(tt*2))/4
        env=np.minimum(1,tt/.35)*np.minimum(1,(len(tt)/SR-tt)/.6)
        place(music,pad*np.maximum(env,0),lo*beat,.035)
    for b in range(56):
        tt=np.arange(round(.24*SR))/SR
        kick=np.sin(2*np.pi*(46*tt+42*.018*(1-np.exp(-tt/.018))))*np.exp(-tt*25)
        if b%2==0:place(music,kick,b*beat,.075)
        n=round(.07*SR);no=rng.normal(size=n);no=np.r_[0,np.diff(no)];tt=np.arange(n)/SR
        place(music,no*np.exp(-tt*90),(b+.5)*beat,.0045,(-1)**b*.25)
    cues=[]
    for i,s in enumerate(EDL["scenes"]):
        if i in (0,2,6,10,14):continue
        at=s["start_s"];length=.30 if s["transition"]!="hard" else .18
        tt=np.arange(round(length*SR))/SR;no=rng.normal(size=len(tt))
        low=np.convolve(no,np.ones(31)/31,"same")
        env=np.sin(np.pi*np.arange(len(tt))/max(1,len(tt)-1))**2
        sweep=(low*.9+no*.13)*env
        place(fx,sweep,at-length*.62,.09,-.2 if i%2 else .2)
        place(fx,tone(47 if i%3 else 54,.24),at,.06)
        cues.append(dict(time_s=at,type="motivated_swipe",scene=s["id"]))
    place(fx,tone(84,1.7),27.94,.05,-.2);place(fx,tone(88,1.5),28.08,.035,.2)
    # Voice is kept at 1x. Conversion changes sample rate, never its elapsed time.
    voice_raw=run(["ffmpeg","-v","error","-i",ROOT/CFG["voice"]["source"],"-ar",str(SR),
                   "-ac","1","-f","f32le","-"])
    voice=np.frombuffer(voice_raw,np.float32).astype(float)
    padded=np.zeros(count);padded[:min(count,len(voice))]=voice[:count]
    # Smooth phrase-driven ducking with 100ms lookahead and ~300ms recovery.
    hop=480;env=np.sqrt(np.mean(padded.reshape(-1,hop)**2,axis=1))
    active=(env>.018).astype(float);active=maximum_filter1d(active,size=31)
    active=gaussian_filter1d(active,4)
    duck=10**(CFG["audio"]["music_duck_db"]*np.interp(np.arange(count)/SR,np.arange(len(active))*.01,active)/20)
    fade=np.minimum(1,np.arange(count)/SR/.06)*np.minimum(1,(count-1-np.arange(count))/SR/.72)
    music*=fade[:,None];fx*=fade[:,None]
    # Do not force an SFX transient onto a strong consonant.
    protect=1-.42*np.interp(np.arange(count)/SR,np.arange(len(active))*.01,active)
    fx*=protect[:,None]
    voice_stereo=np.column_stack([padded,padded])*.95
    mix=voice_stereo+music*duck[:,None]*.60+fx*.72
    paths={"voice":"voice-stem.wav","music":"music-stem.wav","sfx":"sfx-stem.wav","mix":"mix-raw.wav"}
    for kind,data in [("voice",voice_stereo),("music",music),("sfx",fx),("mix",mix)]:
        wavfile.write(ROOT/"assets/audio"/paths[kind],SR,np.float32(data))
    raw=ROOT/"assets/audio/mix-raw.wav";m=measure(raw)
    filt=("loudnorm=I=-16:TP=-1.5:LRA=7:"
       f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
       f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
    master=ROOT/"assets/audio/mix-master.wav"
    run(["ffmpeg","-v","error","-y","-i",raw,"-af",filt,"-ar",str(SR),"-c:a","pcm_f32le",master])
    save("assets/audio/audio_manifest.json",dict(sample_rate_hz=SR,duration_s=30,bpm=112,
        seed=CFG["audio"]["seed"],voice_origin=CFG["voice"]["origin"],voice_provider="unconfirmed",
        speech_speed=1,original_voice_samples=len(voice),music_sfx="original deterministic synthesis",
        duck_min_db=-9,lookahead_ms=100,release_approx_ms=300,sfx_events=cues,
        listening_review="not_performed",raw_measurements=m))

def video_only(dest):
    args=["ffmpeg","-v","error","-nostdin","-n","-f","rawvideo","-pix_fmt","rgb24",
       "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-vf","scale=out_color_matrix=bt709:out_range=tv",
       "-c:v","libx264","-preset","medium","-crf","17","-threads","2","-pix_fmt","yuv420p",
       "-color_range","tv","-colorspace","bt709","-color_trc","bt709","-color_primaries","bt709",str(dest)]
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for f in range(FPS*DURATION):
            p.stdin.write(image_at(f).tobytes())
            if f%90==0:print(f"frame {f}/900",flush=True)
        p.stdin.close();err=p.stderr.read().decode();code=p.wait()
        if code:raise RuntimeError(err[-2500:])
    finally:
        if p.poll() is None:p.kill()

def main():
    global W,H,S
    ap=argparse.ArgumentParser();ap.add_argument("--preview",action="store_true")
    ap.add_argument("--frames",action="store_true");ap.add_argument("--audio-only",action="store_true")
    ap.add_argument("--output");args=ap.parse_args()
    if args.preview:W,H,S=360,640,1/3
    if args.frames:
        target=ROOT/"qc"/("preview-frames" if args.preview else "design-frames");target.mkdir(exist_ok=True)
        for s in EDL["scenes"]:
            for off in [.1,.55]:
                f=min(s["end_frame"]-1,s["start_frame"]+round(off*FPS))
                image_at(f).save(target/f"{s['id']}-{f:04}.jpg",quality=95)
        print("Saved design frames");return
    if args.audio_only:synth_audio();return
    if not (ROOT/"assets/audio/mix-master.wav").exists():synth_audio()
    dest=ROOT/(args.output or ("sal-amargo-v2-previa.mp4" if args.preview else "sal-amargo-v2.mp4"))
    if dest.exists():raise FileExistsError(f"Preserve export; select another --output: {dest}")
    silent=SCRATCH/("silent-preview.mp4" if args.preview else "silent-master.mp4")
    if silent.exists():silent.unlink()
    video_only(silent)
    run(["ffmpeg","-v","error","-n","-i",silent,"-i",ROOT/"assets/audio/mix-master.wav",
       "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-ar",str(SR),
       "-movflags","+faststart",dest])
    m=measure(dest)
    if float(m["input_tp"])>-1.5:
        corrected=SCRATCH/"corrected-audio.mp4"
        gain=-1.55-float(m["input_tp"])
        run(["ffmpeg","-v","error","-y","-i",dest,"-map","0:v:0","-map","0:a:0",
             "-c:v","copy","-af",f"volume={gain:.4f}dB","-c:a","aac","-b:a","192k","-movflags","+faststart",corrected])
        corrected.replace(dest);m=measure(dest)
    probe=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",dest]))
    run(["ffmpeg","-v","error","-i",dest,"-f","null","-"])
    report=dict(file=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),probe=probe,
       post_codec_loudness_lufs=float(m["input_i"]),post_codec_true_peak_dbtp=float(m["input_tp"]),
       post_codec_lra_lu=float(m["input_lra"]),loudnorm_raw_analysis=m,decode_full="passed",
       voice_new_elevenlabs=False,listening_review="not_performed",
       fidelity="v9 inspired; user-requested extensions, not a validated perceptual fidelity score")
    save("qc/"+("preview-qc.json" if args.preview else "master-qc.json"),report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("probe","loudnorm_raw_analysis")},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
