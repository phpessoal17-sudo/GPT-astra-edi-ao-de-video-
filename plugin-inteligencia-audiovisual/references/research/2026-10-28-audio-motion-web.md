# Pesquisa aplicada — áudio, ritmo e motion de alta retenção

Data: 2026-10-28

## Fontes consultadas

1. FFmpeg Filters Documentation — código-fonte oficial da documentação:  
   https://github.com/FFmpeg/FFmpeg/blob/master/doc/filters.texi
2. MDN Web Audio API — visão geral e arquitetura de grafos de áudio:  
   https://github.com/mdn/content/blob/main/files/en-us/web/api/web_audio_api/index.md
3. MDN — Using the Web Audio API:  
   https://github.com/mdn/content/blob/main/files/en-us/web/api/web_audio_api/using_web_audio_api/index.md
4. Web Audio API Specification — W3C Community Group:  
   https://github.com/WebAudio/web-audio-api/blob/main/index.bs
5. GSAP — repositório oficial e documentação associada:  
   https://github.com/greensock/GSAP

## Conhecimento verificado e incorporado

- O FFmpeg oferece `loudnorm` para normalização EBU R128, `sidechaincompress` para ducking, `deesser` para sibilância, `afftdn` para redução espectral e `silenceremove` para detectar/remover intervalos abaixo de limiar. Os parâmetros devem ser medidos no material; presets cegos não substituem escuta.
- Osciladores geram ondas periódicas; filtros biquad controlam espectro; convolução aplica uma resposta ao impulso; compressores reduzem picos e ajudam a evitar clipping em somas. Esses blocos permitem criar SFX e trilhas originais sem amostras externas.
- Grafos modulares favorecem stems separados de voz, música, transições e impactos. Isso facilita ducking, revisão e substituição sem degradar toda a mixagem.
- Em motion, a propriedade animada, o easing e a duração carregam significado. Mudanças de cena devem responder a mudanças de informação, mantendo continuidade por cor, direção ou objeto.

## Procedimentos novos

1. Produzir voz primeiro; remover apenas pausas que não carregam sentido.
2. Para anúncios rápidos, limitar pausas internas residuais a cerca de 20–80 ms e evitar cortes em fonemas.
3. Separar música em pulso, harmonia, textura e acentos para ducking e reorquestração.
4. Usar um SFX principal por mudança narrativa e microsons apenas em dados, gestos ou confirmações.
5. Trocar cenário ou composição a cada nova informação, preservando um elo visual para impedir sensação de colagem.
6. Medir o master após encode; alvo social sugerido próximo de −16 LUFS e true peak de até −1,5 dBTP.

## Limites

- A pesquisa foi concentrada em documentação técnica oficial e fontes abertas acessíveis. “Toda a web” não é um conjunto finito nem pode ser absorvida integralmente.
- Bibliotecas externas de música e SFX exigem verificação individual de licença. A biblioteca desta versão usa síntese procedural original.
