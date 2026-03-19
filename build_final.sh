#!/bin/bash
set -e

echo "🔨 Building with PyInstaller..."
pyinstaller --clean Copaiba_Linux.spec

echo "📋 Copying Qt plugins manually..."
# Encontra o diretório de plugins do PySide6 instalado
PYSIDE_PLUGINS=$(python3 -c "import PySide6; import os; print(os.path.join(os.path.dirname(PySide6.__file__), 'Qt', 'plugins'))")
echo "PySide6 plugins dir: $PYSIDE_PLUGINS"

# Copia plugins para o dist
if [ -d "$PYSIDE_PLUGINS" ]; then
    mkdir -p /app/dist/Copaiba_Linux/_internal/PySide6/Qt/plugins
    cp -r "$PYSIDE_PLUGINS"/* /app/dist/Copaiba_Linux/_internal/PySide6/Qt/plugins/
    echo "✅ Plugins copied successfully"
    ls -la /app/dist/Copaiba_Linux/_internal/PySide6/Qt/plugins/
else
    echo "❌ Plugins dir not found at $PYSIDE_PLUGINS"
fi

echo "📦 Creating AppImage structure..."
mkdir -p /app/AppDir/usr/bin
mkdir -p /app/AppDir/usr/lib
mkdir -p /app/AppDir/usr/share/applications
mkdir -p /app/AppDir/usr/share/icons/hicolor/256x256/apps

# Copia executável e dependências
cp -r /app/dist/Copaiba_Linux/* /app/AppDir/usr/bin/

echo "📋 Bundling missing libxcb libraries..."
# O PySide 6.5+ precisa de libxcb-cursor.so.0
find /usr/lib -name "libxcb-cursor.so.0*" -exec cp -L {} /app/AppDir/usr/bin/_internal/ \;
find /usr/lib -name "libxcb-cursor.so" -exec cp -L {} /app/AppDir/usr/bin/_internal/ \;
echo "✅ bundled libxcb-cursor"

# AppRun script
cat > /app/AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
INTERNAL="${HERE}/usr/bin/_internal"

# Library paths
export LD_LIBRARY_PATH="${INTERNAL}:${INTERNAL}/PySide6:${INTERNAL}/PySide6/Qt/lib:${LD_LIBRARY_PATH}"

# Qt paths
export QT_PLUGIN_PATH="${INTERNAL}/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="${INTERNAL}/PySide6/Qt/plugins/platforms"
export QML2_IMPORT_PATH="${INTERNAL}/PySide6/Qt/qml"

# Force xcb platform if available
export QT_QPA_PLATFORM=xcb

# XDG paths
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/share}"

exec "${HERE}/usr/bin/Copaiba_Linux" "$@"
EOF
chmod +x /app/AppDir/AppRun

# Desktop file
cat > /app/AppDir/copaiba.desktop << 'EOF'
[Desktop Entry]
Name=Copaiba Lexikon
Exec=Copaiba_Linux
Icon=copaiba
Type=Application
Categories=AudioVideo;Audio;
EOF

# Icon (cria um PNG simples se favicon.ico não funcionar)
cp /app/favicon.ico /app/AppDir/copaiba.png 2>/dev/null || echo "" > /app/AppDir/copaiba.png

# Baixa appimagetool
echo "📥 Downloading appimagetool..."
wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O /tmp/appimagetool
chmod +x /tmp/appimagetool
cd /tmp && ./appimagetool --appimage-extract >/dev/null 2>&1

echo "📦 Creating AppImage..."
cd /app
ARCH=x86_64 /tmp/squashfs-root/AppRun AppDir /app/dist/Copaiba_Lexikon-x86_64.AppImage

echo ""
echo "✅ Build complete!"
ls -lh /app/dist/
