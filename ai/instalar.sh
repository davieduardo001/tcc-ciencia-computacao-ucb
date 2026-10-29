#!/usr/bin/env bash
# Cria na raiz do repositório as pastas que cada ferramenta de IA espera
# (.claude, .opencode, .gemini e opencode.json) como links para ai/.
# A fonte de verdade é ai/; os links ficam no .gitignore.
#
# Uso:
#   ./ai/instalar.sh             cria os links
#   ./ai/instalar.sh --remover   remove só os links criados por este script
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$raiz"

# destino na raiz | alvo do link (relativo à pasta do destino)
LINKS=(
  ".claude/skills|../ai/skills"
  ".claude/launch.json|../ai/claude/launch.json"
  ".opencode/skills|../ai/skills"
  ".opencode/agents|../ai/agents"
  ".gemini/skills|../ai/skills"
  ".gemini/settings.json.example|../ai/gemini/settings.json.example"
  "opencode.json|ai/opencode/opencode.json"
)

modo="${1:-criar}"

for par in "${LINKS[@]}"; do
  destino="${par%%|*}"
  alvo="${par##*|}"
  if [ "$modo" = "--remover" ]; then
    if [ -L "$destino" ]; then
      rm "$destino"
      echo "removido: $destino"
    fi
    continue
  fi
  mkdir -p "$(dirname "$destino")"
  if [ -e "$destino" ] && [ ! -L "$destino" ]; then
    echo "AVISO: $destino já existe e não é um link; não foi alterado." >&2
    continue
  fi
  ln -sfn "$alvo" "$destino"
  echo "ok: $destino -> $alvo"
done

if [ "$modo" != "--remover" ]; then
  echo
  echo "Pronto. Para o Gemini CLI, copie ai/gemini/settings.json.example para"
  echo ".gemini/settings.json e coloque o seu token (esse arquivo não vai para o Git)."
fi
