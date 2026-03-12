#!/bin/bash
set -e

DIST_DIR="$HOME/copaiba_dist_arch"
APP_DIR="$DIST_DIR/AppDir"
OUTPUT_DIR="$DIST_DIR/Output"

echo "🧹 Limpando builds anteriores..."
rm -rf build/ dist/ "$DIST_DIR"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/lib"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$OUTPUT_DIR"

echo "🔨 Executando PyInstaller (Nativo)..."
pyinstaller --clean --distpath "$DIST_DIR/dist" --workpath "$DIST_DIR/build" Copaiba_Linux.spec

echo "📦 Preparando AppDir..."
cp -r "$DIST_DIR/dist/Copaiba_Linux/"* "$APP_DIR/usr/bin/"

# Copia ícone
cp favicon.ico "$APP_DIR/copaiba.png"
cp favicon.ico "$APP_DIR/usr/share/icons/hicolor/256x256/apps/copaiba.png"

# Cria AppRun
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
INTERNAL="${HERE}/usr/bin/_internal"

# Caminhos de bibliotecas
export LD_LIBRARY_PATH="${INTERNAL}:${INTERNAL}/PySide6:${INTERNAL}/PySide6/Qt/lib:${LD_LIBRARY_PATH}"

# Caminhos Qt
export QT_PLUGIN_PATH="${INTERNAL}/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="${INTERNAL}/PySide6/Qt/plugins/platforms"
export QML2_IMPORT_PATH="${INTERNAL}/PySide6/Qt/qml"

# Força plataforma xcb (se disponível)
export QT_QPA_PLATFORM=xcb

exec "${HERE}/usr/bin/Copaiba_Linux" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Cria .desktop
cat > "$APP_DIR/copaiba.desktop" << 'EOF'
[Desktop Entry]
Name=Copaiba Lexikon
Exec=Copaiba_Linux
Icon=copaiba
Type=Application
Categories=AudioVideo;Audio;
EOF
cp "$APP_DIR/copaiba.desktop" "$APP_DIR/usr/share/applications/"

echo "📋 Verificando plugins Qt..."
# No Arch, PySide6 geralmente instala plugins corretamente em site-packages/PySide6/Qt/plugins
# O PyInstaller deve ter copiado. Se não, copiamos manualmente.
if [ ! -d "$APP_DIR/usr/bin/_internal/PySide6/Qt/plugins/platforms" ]; then
    echo "⚠️  Plugins não encontrados no bundle. Tentando copiar do sistema..."
    PYSIDE_PLUGINS=$(python -c "import PySide6; import os; print(os.path.join(os.path.dirname(PySide6.__file__), 'Qt', 'plugins'))")
    if [ -d "$PYSIDE_PLUGINS" ]; then
        mkdir -p "$APP_DIR/usr/bin/_internal/PySide6/Qt/plugins"
        cp -r "$PYSIDE_PLUGINS"/* "$APP_DIR/usr/bin/_internal/PySide6/Qt/plugins/"
        echo "✅ Plugins copiados manualmente."
    else
        echo "❌ Plugins não encontrados em $PYSIDE_PLUGINS"
    fi
fi

echo "🔍 Empacotando dependências sensíveis (libxcb-cursor)..."
# Tenta encontrar libxcb-cursor no sistema
for lib in libxcb-cursor.so.0 libxcb-cursor.so; do
    found=$(find /usr/lib -name "$lib*" | head -n 1)
    if [ -n "$found" ]; then
        echo "   Bundling $found"
        cp -L "$found" "$APP_DIR/usr/bin/_internal/"
    fi
done

echo "📥 Baixando appimagetool..."
APPIMAGETOOL="$DIST_DIR/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

echo "🚀 Gerando AppImage..."
# Extrai appimagetool se necessário (caso FUSE falhe) ou roda direto
# Vamos tentar rodar direto, se falhar user precisa de FUSE.
# Arch geralmente tem FUSE.
ARCH=x86_64 "$APPIMAGETOOL" "$APP_DIR" "$OUTPUT_DIR/Copaiba_Lexikon-Arch-x86_64.AppImage"

echo ""
echo "✅ Build concluído!"
echo "📁 Executável AppImage: $OUTPUT_DIR/Copaiba_Lexikon-Arch-x86_64.AppImage"
