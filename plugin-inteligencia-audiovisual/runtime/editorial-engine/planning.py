"""Ferramentas determinísticas; a direção semântica permanece com o agente/editor."""
import json, math

def remap_words(words,segments,fps):
    result=[];offset=0
    for segment in segments:
        start,end=segment['in'],segment['out']
        for word in words:
            a,b=word['start'],word['end']
            if start<=a and b<=end:
                result.append(dict(word,start=offset+a-start,end=offset+b-start))
            elif a<end and b>start:
                raise ValueError('Corte intercepta palavra: '+word['word'])
        offset+=round((end-start)*fps)/fps
    return result

def captions(words,max_words=5,max_duration=2.5):
    if not 1<=max_words<=12:raise ValueError('max_words inválido')
    events=[];group=[]
    for word in words:
        if not 0<=word['start']<word['end']:raise ValueError('Tempos de palavra inválidos')
        if group and word['start']<group[-1]['end']-.02:raise ValueError('Palavras fora de ordem')
        if group and (len(group)>=max_words or word['end']-group[0]['start']>max_duration):
            events.append({'type':'caption','start':group[0]['start'],'end':group[-1]['end'],'text':' '.join(w['word'] for w in group)})
            group=[]
        group.append(word)
    if group:events.append({'type':'caption','start':group[0]['start'],'end':group[-1]['end'],'text':' '.join(w['word'] for w in group)})
    return events

def word_highlights(words):
    return [{'type':'caption','start':w['start'],'end':w['end'],'text':w['word']} for w in words]

def composition(boxes,protected,width,height):
    issues=[]
    def intersects(a,b):return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]
    for i,b in enumerate(boxes):
        x,y,w,h=b
        if min(x,y)<0 or min(w,h)<=0 or x+w>width or y+h>height:issues.append({'box':i,'issue':'outside_frame'})
        if any(intersects(b,p) for p in protected):issues.append({'box':i,'issue':'protected_collision'})
        if any(intersects(b,p) for p in boxes[:i]):issues.append({'box':i,'issue':'graphic_collision'})
    return issues

def load_transcript(path):
    words=json.load(open(path,encoding='utf-8'))['words']
    for w in words:
        if not isinstance(w['word'],str) or not all(math.isfinite(w[k]) for k in ('start','end')):raise ValueError('Transcrição inválida')
    return words
