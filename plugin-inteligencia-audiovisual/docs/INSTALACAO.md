# Instalação, importação e uso

## Ambiente compatível com skills locais

1. Extraia o ZIP.
2. Copie `skills/masterpiece-audiovisual/` para o diretório de skills aceito pelo ambiente.
3. Preserve a pasta `references/`, `config/`, `prompts/` e `docs/` na mesma estrutura relativa.
4. Reinicie o agente para carregar a skill.
5. Invoque `masterpiece-audiovisual-intelligence` e forneça os materiais do projeto.

## Conta sem importação de plugin

1. Crie um GPT/agente personalizado.
2. Use `prompts/PROMPT_MESTRE.md` como instrução principal.
3. Envie os arquivos de `references/` e `config/` como conhecimento.
4. Adicione somente ferramentas realmente suportadas pela conta.
5. Faça um teste curto e confirme se o agente distingue capacidades verificadas de condicionais.

## Runtime local

`runtime/editorial-engine/` contém componentes Python/FFmpeg reaproveitados do motor testado no projeto. Dependências, comandos e compatibilidade devem ser verificados no ambiente de destino. O runtime não instala FFmpeg, modelos ASR, Blender ou HyperFrames.

## Atualização

Incorpore novos registros usando o schema, atualize o módulo afetado, execute testes pertinentes, incremente a versão e registre no `CHANGELOG.md`. Não substitua uma versão aprovada sem preservar histórico ou justificativa.

