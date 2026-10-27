"""Renderiza um card editorial original com easing, sombra e camadas 2D."""
import argparse,subprocess,math
from PIL import Image,ImageDraw,ImageFont,ImageFilter
p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--text',default='Clareza em movimento');p.add_argument('--seconds',type=float,default=3);a=p.parse_args()
w,h,fps=540,960,30
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',32)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
if a.seconds<=0 or a.seconds>60:p.exit(1,'Duração: 0–60 segundos\n')
cmd=['ffmpeg','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-n',a.output]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
 for n in range(round(a.seconds*fps)):
  t=n/fps;u=min(1,t/.65);ease=1-(1-u)**3;y=round(330+(1-ease)*180)
  im=Image.new('RGB',(w,h),'#eeeee8');d=ImageDraw.Draw(im)
  for x in range(0,w,54):d.line((x,0,x,h),fill='#e4e4dd')
  shadow=Image.new('RGBA',(w,h));sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((64,y+20,484,y+240),radius=28,fill=(0,0,0,55));im=Image.alpha_composite(im.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(18)))
  d=ImageDraw.Draw(im);d.rounded_rectangle((60,y,480,y+220),radius=28,fill='#183c32');d.text((90,y+36),'EDITORIAL / 01',font=small,fill='#b9cebd')
  lines=[];line=''
  for word in a.text.split():
   test=(line+' '+word).strip()
   if d.textlength(test,font=font)>350:lines.append(line);line=word
   else:line=test
  lines.append(line)
  for j,line in enumerate(lines[:3]):d.text((90,y+85+j*40),line,font=font,fill='white')
  d.line((70,760,70+round(400*min(1,t/a.seconds)),760),fill='#183c32',width=5)
  d.text((70,810),'Composição original • demonstração 2D',font=small,fill='#183c32')
  proc.stdin.write(im.convert('RGB').tobytes())
 proc.stdin.close()
 if proc.wait():raise RuntimeError('FFmpeg falhou')
except Exception:
 proc.kill();raise
