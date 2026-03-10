#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/felipemoz/lakeventory.git"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/share/lakeventory}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Erro: comando obrigatório não encontrado: $1" >&2
    exit 1
  fi
}

require_cmd git
require_cmd make
require_cmd python3
require_cmd pip3

mkdir -p "$(dirname "$INSTALL_DIR")"

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Atualizando Lakeventory em: $INSTALL_DIR"
  git -C "$INSTALL_DIR" fetch --all --prune
  git -C "$INSTALL_DIR" checkout main
  git -C "$INSTALL_DIR" pull --ff-only origin main
else
  echo "Clonando Lakeventory em: $INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
echo "Instalando dependências..."
make install

echo ""
echo "✅ Lakeventory instalado em: $INSTALL_DIR"
echo "Próximos passos:"
echo "  cd $INSTALL_DIR"
echo "  make setup"
echo "  make check"
echo "  make inventory"
