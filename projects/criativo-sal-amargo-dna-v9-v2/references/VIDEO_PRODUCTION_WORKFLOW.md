# Workflow audiovisual recorrente solicitado pelo usuário

## Preferência registrada

Criar peças publicitárias completas com roteiro, motion design, vídeo, edição, música e efeitos sonoros; priorizar implementação por código e habilidades/plugins realmente disponíveis. Não depender de memória da conversa: consultar este arquivo, o briefing local e os perfis salvos.

Atualização 30/10/2026: ler também `skills/product-motion-studio/SKILL.md` e `knowledge/motion-graphics-feedback-2026-10-30.md`. Narração por padrão nos criativos, ElevenLabs preferencial, pesquisa de produto autorizada, packshot com qualidade adequada e identidade conferida, cenários variados por frase e profundidade/câmera/3D/B-roll quando tiverem função narrativa. Voz real e seus clocks conduzem o vídeo. Falhas de serviço e origem alternativa precisam ser explícitas.

## Ordem de produção

1. Ingerir mídia; preservar original e hash; verificar dimensões, PTS, áudio e capacidades do ambiente.
2. Escolher o DNA principal em `video-style-dna-engine/profiles/`; ler eventos e relatório correspondente. Valores observados, inferidos e propostos devem permanecer distintos.
3. Escrever argumento publicitário verdadeiro, foco de cada beat e CTA. Sem dados de oferta/saúde/licença, restringir o texto ao que está sustentado; não inventar desconto, resultado, depoimento ou recurso.
4. Salvar storyboard e EDL com unidades, entradas/saídas e relação com áudio. Adaptar a cadência à leitura e ao conteúdo; não obrigar o mesmo número de cortes.
5. Resolver ativos. A imagem fornecida identifica o produto; não ampliá-la como packshot final se faltar qualidade. Pesquisar foto oficial equivalente ou restaurar com comparação de identidade. Rejeitar geração que altere embalagem ou microtexto. Transformações e máscaras podem compor o ativo sem falsificar conteúdo. Informação ilegível continua incerta.
6. Renderizar animação por tempo absoluto, fontes reais, parâmetros centralizados e movimentos motivados. Um foco por beat, sustentação legível e composição fiel ao perfil selecionado.
7. Música e SFX em stems separados, com fontes e licenças registradas. Pode-se compor música/SFX originais por código quando autorizado/adequado. Recursos de catálogo só entram após download e validação efetivos. Não copiar trilha das referências como se fosse licenciada.
8. Prévia → inspeção → refinamento → export. Áudio proposto não é apresentado como reconstrução perceptual do áudio não validado das referências.
9. QC de arquivo completo, timebase, frames, dimensões, áudio, loudness/true peak pós-codec, textos e quadros/transições. Escuta humana/perceptual pendente deve ser declarada quando não executada.
10. Entregar MP4 utilizável e projeto editável, com um comando de reconstrução e configurações; registrar feedback no CHANGELOG.

## Skills úteis

- Masterpiece Video Engine: inspeção, EDL, regras contextuais e QC.
- HeyGen Script Writer, Motion Graphics e Video Editing: escrita, desenho/edição em Python e revisão.
- ImageGen: tratamento assistido de imagem, apenas com comparação ao original.
- HeyGen audio catalog / ElevenLabs: ativos de áudio quando disponíveis; não presumir acesso/geração concluída.

As regras da solicitação original de engenharia reversa continuam sendo a referência para precisão, rastreabilidade e distinção entre análise e implementação. O core disponível é experimental; cada peça é verificada separadamente.

