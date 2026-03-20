#!/bin/bash
# build_linux.sh - Script para criar build Linux compatível com Ubuntu 22.04+

set -e

echo "🐳 Copaiba Linux Builder"
echo "========================"
echo ""

# Nome da imagem Docker
IMAGE_NAME="copaiba-builder"

# Verifica se Docker está disponível
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

echo "📦 Construindo imagem Docker..."
docker build -t $IMAGE_NAME .

echo ""
echo "🔨 Gerando executável..."

# Cria diretório de output se não existir
mkdir -p dist_ubuntu

# Executa o build dentro do container
docker run --rm \
    -v "$(pwd)/dist_ubuntu:/app/dist" \
    -v "$(pwd)/build:/app/build" \
    $IMAGE_NAME

echo ""
echo "✅ Build concluído!"
echo "📁 Executável em: ./dist_ubuntu/Copaiba_Linux/"
echo ""
echo "Para testar localmente (se tiver Ubuntu 22.04):"
echo "  ./dist_ubuntu/Copaiba_Linux/Copaiba_Linux"
