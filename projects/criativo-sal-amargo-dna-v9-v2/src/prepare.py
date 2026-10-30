"""Project data and deterministic phrase clock. Run before render."""
import json, pathlib, shutil, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def save(name,data):
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    # Coarse anchors from the supplied ASR; inner divisions use measured pauses.
    rows=[
      (0,1.05,"opening","Rotina corrida.",False,"macro inclinado + tipografia grande"),
      (1.05,2.30,"choices","Escolhas demais.",False,"repetição tipográfica e três planos do mesmo frasco"),
      (2.30,3.76,"lifestyle","E na hora de cuidar de você,",False,"imagem de apoio em cartão com paralaxe"),
      (3.76,5.50,"orbit","praticidade faz diferença.",False,"cena verde-escura, órbita 3D e produto"),
      (5.50,7.90,"hero","Conheça o Sal Amargo em cápsulas, da Unilife.",False,"revelação do frasco inteiro em estúdio claro"),
      (7.90,10.12,"macro","Um suplemento alimentar em cápsulas, com",False,"aproximação frontal do rótulo"),
      (10.12,12.70,"botanical","apresentação vegana e cem por cento vegetal,",False,"folhagem de imagem de apoio e frasco em primeiro plano"),
      (12.70,14.40,"label","conforme indicado no rótulo.",False,"máscara circular revela detalhe da frente"),
      (14.40,16.65,"pedestal","Uma forma prática de acompanhar o seu dia,",False,"plinto geométrico com torus 3D"),
      (16.65,18.68,"usage","sempre seguindo o modo de uso da embalagem",False,"passagem clara, recorte do rótulo e órbita lateral"),
      (18.68,21.28,"advisory","e a orientação de um profissional de saúde.",True,"produto estável, profundidade e respiro legível"),
      (21.28,22.91,"composition","Confira a composição",False,"cartão macro frontal; sem verso inventado"),
      (22.91,24.32,"warnings","e as advertências antes de usar.",False,"fundo escuro e relevo tipográfico"),
      (24.32,25.64,"brand","Sal Amargo Unilife.",True,"retorno do hero com fita verde"),
      (25.64,27.82,"clarity","Mais clareza para uma escolha consciente.",True,"contexto em cartão e produto alinhado à frente"),
      (27.82,30.00,"cta","Clique e saiba mais.",True,"frasco nítido e CTA sustentado até o fim"),
    ]
    scenes=[];captions=[]
    for i,(a,b,kind,text,whole,visual) in enumerate(rows):
        scene=dict(id=f"scene-{i+1:02}",kind=kind,start_s=a,end_s=b,
                   start_frame=round(a*30),end_frame=round(b*30),visual=visual,
                   trigger="fala existente; âncora ASR por frase" if whole else "subdivisão aproximada apoiada em pausa/âncora ASR",
                   transition="hard" if i not in (3,4,7,8,13,15) else "motivated_green_wipe",
                   confidence=0.78 if whole else 0.55)
        scenes.append(scene)
        captions.append(dict(id=f"caption-{i+1:02}",text=text,start_s=a,end_s=b,
                             start_frame=round(a*30),end_frame=round(b*30),
                             mode="hook" if i<2 else "emphasis" if i in (3,4,6,13,15) else "subtitle",
                             timing_precision="phrase_approximate",word_highlighting=False))
    save("edl.json",dict(schema_version="1.1.0",units="seconds",fps="30/1",frame_index="zero_based",
         intervals="half_open",audio_clock="native source at 1x; resampled to 48000 Hz",
         scenes=scenes,source_mappings=[dict(asset="narration-original.wav",source_in_s=0,
             source_out_s=28.9646666667,sequence_start_s=0,speed=1.0)],
         proposed_extensions_not_reference_evidence=["dark_green_studio","3d_torus","procedural_plinth","image_motion_broll"]))
    save("captions.json",dict(units="seconds",listening_review="not_performed",cues=captions,
         note="Texto do roteiro anterior; correção editorial do ASR inicial, sem alegação de escuta palavra a palavra. Divisões internas não são alinhamento de palavra."))
    def stamp(t):
        ms=round(t*1000);return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"
    (ROOT/"captions.srt").write_text("\n\n".join(f"{i+1}\n{stamp(c['start_s'])} --> {stamp(min(c['end_s'],28.964667) if i==len(captions)-1 else c['end_s'])}\n{c['text']}" for i,c in enumerate(captions))+"\n",encoding="utf-8")
    origin="https://github.com/phpessoal17-sudo/GPT-astra-edi-ao-de-video-/tree/ccfa9a96ff3db2b19a8a51324c94c46734304d0d/projects/sal-amargo-unilife-ad"
    assets=[]
    for p in sorted((ROOT/"assets").rglob("*")):
        if p.is_file() and (p.parent.name!="audio" or p.name=="narration-original.wav"):
            assets.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    save("references/provenance.json",dict(previous_project=origin,assets=assets,
       image_hd="Previously AI-enhanced product photo, not official; no exact microtext guarantee",
       broll="Previously generated stills animated with code; not live-action clips",
       narration="Existing WAV from user's repository; provider unconfirmed; reused at 1x",
       elevenlabs_attempt=dict(flow_id="oZXG1Fyw2ofRRCXWlatq",status="not_started",charged=False,
             reason="free generations busy; no second generation requested"),
       new_imagegen=dict(path="/workspace/generated_images/exec-6b74d076-2053-4900-84f9-45ab8fd300ac.png",
             used=False,reason="quantity area changed"),
       official_product_page="https://www.unilife.com.br/product-page/sal-amargo-em-c%C3%A1psulas-850-mg-unilife",
       official_asset_download="blocked by network destination policy; no bypass"))
    (ROOT/"storyboard.md").write_text("# Storyboard e decisões\n\n"+"\n".join(
        f"- {s['start_s']:.2f}–{s['end_s']:.2f} s · frames [{s['start_frame']},{s['end_frame']}) · **{s['kind']}**: {s['visual']}. Gatilho: {s['trigger']}."
        for s in scenes)+"\n\nCada cenário tem um foco; a imagem continua sendo avaliada em todos os frames. Áudio não é quantizado por palavra.\n",encoding="utf-8")
    for rel in ["../skills/product-motion-studio/SKILL.md","../knowledge/motion-graphics-feedback-2026-10-30.md","../VIDEO_PRODUCTION_WORKFLOW.md"]:
        p=(ROOT/rel).resolve()
        target=ROOT/"references"/p.name
        if p.is_file() and p!=target:shutil.copyfile(p,target)
        elif not target.is_file():print("Optional reference unavailable:",p.name)
        if p.name=="SKILL.md" and target.is_file():
            target.write_text(target.read_text().replace("../../knowledge/motion-graphics-feedback-2026-10-30.md",
                "motion-graphics-feedback-2026-10-30.md"),encoding="utf-8")
    print(f"Prepared {len(scenes)} scenes and {len(captions)} phrase cues")
if __name__=="__main__":main()
