# Sal Amargo v2 — Motion Studio

Criativo vertical de 30 segundos, 1080×1920, 30 FPS, com voz, música, SFX e 16 estados de cena. Projeto reproduzível em Python e FFmpeg. A v1 continua preservada.

Abra index.html para assistir ou use sal-amargo-v2.mp4. O texto completo da fala está em roteiro.md e captions.srt; as legendas já estão incorporadas ao vídeo, portanto não ative o SRT por cima delas.

## O que mudou

- Narração existente usada como relógio mestre, em velocidade 1×.
- Packshot aprimorado anterior de 1254×1254, em lugar da ampliação direta da foto de 240px.
- Macro, frasco inteiro, cenários claros/escuros, contexto, tipografia, detalhes e CTA.
- Geometria 3D projetada com iluminação e ordenação por profundidade; o frasco continua uma fotografia frontal em camadas.
- Imagens de apoio animadas por código; não são B-roll filmado.
- Trilha e SFX originais sintetizados, com ducking suave para preservar a fala.
- Preferências, pesquisa e skill portátil salvas em references/.

## Origem e limites

A ElevenLabs foi consultada e uma tentativa de voz retornou fila gratuita ocupada, sem início e sem cobrança. Não houve nova geração. A voz entregue vem do áudio que já existia no repositório do usuário; seu provedor não está comprovado.

A tentativa ImageGen desta revisão alterou a área de quantidade e foi rejeitada. O packshot usado é o aprimoramento já existente do mesmo projeto, com marca/nome/frasco comparados; microtexto ilegível na foto original não permite afirmar fidelidade integral. Não foi usada uma fotografia oficial baixada do fabricante, pois o download da CDN foi bloqueado.

As âncoras de frase vêm da transcrição anterior. Subdivisões internas usam pausas medidas e continuam aproximadas; não há alinhamento palavra a palavra nem karaoke. A fala fica em velocidade original. Não foi realizada escuta perceptual completa ou aprovação humana de sincronização.

A pesquisa textual oficial confirmou a formulação vegana e as variantes; não foram acrescentadas promessas clínicas, preço, desconto ou dosagem. Fontes e limitações estão em references/provenance.json e no registro de conhecimento.

## Reconstrução

Requisitos: Python 3.12 compatível, FFmpeg/ffprobe com libx264/AAC e as dependências de requirements.txt. As fontes Manrope e DM Serif Display, com licenças OFL, estão incluídas. Os assets usados estão locais; nenhuma conta externa é necessária para reconstruir a montagem aceita.

    python -m pip install -r requirements.txt
    python src/prepare.py
    python src/render.py --audio-only
    python src/verify.py
    python src/render.py --output sal-amargo-v2-rebuild.mp4

O nome alternativo preserva a exportação anterior. A avaliação das animações usa tempo absoluto; ordem aleatória de frames foi verificada. Igualdade de bitstream entre versões diferentes de FFmpeg não é garantida.

    python src/render.py --preview --output minha-previa.mp4
    python src/render.py --frames

O scratch padrão é /workspace/work/sal-amargo-v2 para este workspace. Em outra máquina, execute com VIDEO_DNA_WORKDIR apontando para uma pasta gravável, ou deixe o fallback local work/.

## Estrutura

- src/prepare.py: EDL, legendas, storyboard e proveniência.
- src/render.py: composição, projeção 3D, animação, síntese/mix e export.
- src/verify.py: clocks, determinismo, limites de cenas, integridade e preservação da fala.
- assets/images/: originais e referências utilizadas.
- assets/fonts/: tipografia real e licenças.
- assets/audio/: voz original, stems, mix e parâmetros.
- style/: DNA doador.
- qc/: medições e evidências de revisão.
- references/: pesquisa, origem e instruções reutilizáveis.

O pacote de download pode excluir MP4s duplicados, caches, imagens de QC derivadas e mixagens regeneráveis. O manifesto do pacote declara seu conteúdo. Stems em FLAC de 24 bits servem ao intercâmbio; os intermediários float32 são regenerados pelo código.
