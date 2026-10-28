# Módulo 05 — Áudio e sonorização

- Voz vem primeiro: inteligibilidade, ruído, EQ corretivo leve, de-essing quando necessário, compressão moderada e automação.
- Música acompanha o arco e recua sob fala; sidechain/ducking deve soar natural.
- SFX marcam ações relevantes, transições e revelações; evitar camadas sem função.
- Um arquivo mixado não fornece stems. Não prometer isolamento perfeito de voz, música e efeitos.
- Meta social sugerida: cerca de -16 LUFS integrados, true peak até -1,5 dBTP; adaptar à plataforma e medir após o encode.
- Sintetizar trilha e SFX localmente é uma opção econômica e licenciável, mas exige revisão perceptiva.

## Fluxo de fala rápida

- Reescrever antes de acelerar: frases curtas preservam compreensão melhor que `atempo` agressivo.
- Cortar pausas internas com limiar medido, preservando 20–80 ms entre ideias para evitar fonemas colados.
- Aceleração moderada sugerida: 1,05–1,18× depois da remoção de silêncios; valores maiores exigem revisão humana.
- Tratar nomes de marca e números como pontos de QC obrigatório.

## Biblioteca local 1.1

- 15 SFX originais: whooshes, riser, downlifter, impactos, sub drop, clicks, chimes, sparkle e transições.
- Três trilhas originais de 30 s: wellness premium, editorial e cinematic clarity.
- Os masters de música são deliberadamente conservadores para mix sob locução; normalizar somente no mix final.
- Metadados e usos recomendados ficam em `../../library/audio-catalog.json`.

