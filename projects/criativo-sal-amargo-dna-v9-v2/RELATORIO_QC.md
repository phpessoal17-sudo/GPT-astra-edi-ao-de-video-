# Controle de qualidade da revisão 2

Arquivo: sal-amargo-v2.mp4. Vídeo: 30,000 s, 1080×1920, 30 FPS constantes, 900 frames, H.264/BT.709 SDR. Áudio: AAC estéreo 48 kHz, duração declarada de 30,016 s; diferença de 16 ms por enquadramento do codec, inferior a um frame.

- Decodificação integral das duas mídias: passou.
- Loudness integrado após AAC: −16,47 LUFS.
- True peak após AAC: −1,57 dBTP.
- LRA após AAC: 2,0 LU.
- PTS dos 900 quadros conforme CFR 30; erro máximo de arredondamento observado: 0,000000334 s.
- Integridade dos ativos originais e avaliação aleatória dos frames: passaram.
- Voz: fonte em velocidade 1×, 28,964667 s, sem corte de palavras; preenchimento posterior até o encerramento.
- Comparação por correlação entre voz de origem e áudio codificado nas janelas 0–6 e 22–28 s: lag de 0 amostras em ambas. Mede alinhamento do áudio, não valida legendas semanticamente.
- 16 estados de cena; duração média 1,875 s, mediana 1,885 s, intervalo 1,05–2,60 s.
- Revisão visual do master corrigido: 48 amostras uniformes e 62 frames de limites. Três provas nativas de desenho e duas máscaras editoriais de UI também foram examinadas.
- O primeiro passe revelou transição sobre o texto. A ordem de composição foi corrigida e o master refeito; os frames codificados da correção foram examinados.

## Limites

Não houve escuta completa nem reprodução perceptual contínua do vídeo. O alinhamento de frases é aproximado, apoiado nas âncoras ASR anteriores e em pausas medidas; não é temporização palavra a palavra comprovada. Não há teste de retenção com público ou selo de fidelidade científica.

A nova geração ElevenLabs não iniciou e não cobrou. A voz utilizada é anterior, com provedor não comprovado. O packshot tem maior definição, mas todo microtexto do original de 240px não pode ser comprovado. A nova tentativa ImageGen que alterou a quantidade foi rejeitada.

As máscaras de interface são uma aproximação editorial conservadora; não são template oficial de todas as plataformas.

Medições detalhadas: qc/master-qc.json, qc/export_checks.json, qc/native-frames.csv, qc/source_checks.json e qc/visual_review.json.
