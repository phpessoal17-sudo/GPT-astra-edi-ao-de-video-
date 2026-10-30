"""Compact source distribution; preserves original inputs, code and audio stems."""
import hashlib,json,pathlib,re,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    note=ROOT/"PACOTE_DOWNLOAD.md"
    note.write_text("""# Pacote editavel\n+
O MP4 final e baixado separadamente. Coloque sal-amargo-v2.mp4 na pasta extraida para usar index.html.

Este ZIP preserva a foto original, o packshot HD usado, as duas imagens de apoio, fontes/licencas, perfil de DNA, roteiro, EDL, legendas, codigo, relatorios e instrucoes reutilizaveis.

Audio separado: narration-original.wav e a voz original (mono, 24 kHz); music-stem.flac e sfx-stem.flac sao os stems de intercambio em PCM de 24 bits. O codec FLAC preserva esses 24 bits; nao se afirma identidade bit a bit com os intermediarios float32. O codigo regenera voz/musica/SFX/mix em float32 a 48 kHz.

Foram omitidos somente videos duplicados, imagens derivadas de QC/caches e intermediarios de audio regeneraveis. O arquivo original de voz e mantido sem alteracao. Os resultados de QC se referem ao MP4 final, nao a uma renderizacao futura em outro ambiente.

Veja README.md para reconstruir e references/ para origem, preferencias e limites.
""".replace("\n+","\n"),encoding="utf-8")
    selected=[];omitted=[]
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if ("__pycache__" in rel.parts or p.suffix==".mp4" or
            p.suffix==".wav" and p.name!="narration-original.wav" or
            p.name=="voice-stem.flac" or
            rel.parts[0]=="qc" and p.suffix.lower() in (".jpg",".png") or
            p.name in ("PACKAGE_MANIFEST.json","FILE_MANIFEST.json")):
            omitted.append(str(rel));continue
        selected.append(p)
    patterns=[r"X-Amz-(?:Credential|Signature|Security-Token)",r"gh[pousr]_[A-Za-z0-9_]{20,}",
       r"github_pat_[A-Za-z0-9_]{20,}",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    for p in selected:
        if p.suffix in (".md",".json",".py",".txt",".html",".csv"):
            text=p.read_text(encoding="utf-8")
            assert not any(re.search(x,text) for x in patterns),p.name
    manifest=dict(schema_version="1.0.0",distribution="editable compact",videos="download separately",
       files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in selected],
       excluded_derived_or_redundant=omitted,
       original_voice_preserved=True,music_sfx_delivery_format="FLAC PCM 24-bit",
       regeneration="python src/prepare.py; python src/render.py --audio-only; python src/verify.py; python src/render.py --output sal-amargo-v2-rebuild.mp4")
    m=ROOT/"PACKAGE_MANIFEST.json";m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    selected.append(m)
    dest=ROOT.parent/"criativo-sal-amargo-v2-editavel.zip"
    if dest.exists():raise FileExistsError(dest)
    with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(selected):
            info=zipfile.ZipInfo("criativo-sal-amargo-v2/"+str(p.relative_to(ROOT)),date_time=(2026,10,30,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes(),compresslevel=7)
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    size=dest.stat().st_size
    assert 4*((size+2)//3)+3000<16*1024*1024,"Connector payload exceeds limit"
    def git_sha(p):
        data=p.read_bytes();return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    video=ROOT/"sal-amargo-v2.mp4"
    result=dict(zip_path=str(dest),zip_bytes=size,zip_sha256=sha(dest),zip_git_blob_sha1=git_sha(dest),
       video_path=str(video),video_bytes=video.stat().st_size,video_sha256=sha(video),
       video_git_blob_sha1=git_sha(video),zip_entries=len(selected),zip_crc_check="passed")
    (ROOT.parent/"criativo-sal-amargo-v2-entrega.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
