#!/bin/bash
set -e

echo "🔨 Building with PyInstaller..."
pyinstaller --clean --onedir Copaiba_Linux.spec

echo "📦 Creating AppDir structure..."
mkdir -p /app/Copaiba.AppDir/usr/bin
mkdir -p /app/Copaiba.AppDir/usr/lib
mkdir -p /app/Copaiba.AppDir/usr/share/applications
mkdir -p /app/Copaiba.AppDir/usr/share/icons/hicolor/256x256/apps

# Copia o conteúdo do PyInstaller para AppDir
cp -r /app/dist/Copaiba_Linux/* /app/Copaiba.AppDir/usr/bin/

# Move _internal para lib e cria links
if [ -d "/app/Copaiba.AppDir/usr/bin/_internal" ]; then
    cp -r /app/Copaiba.AppDir/usr/bin/_internal/* /app/Copaiba.AppDir/usr/lib/ 2>/dev/null || true
fi

# Cria o script de inicialização AppRun
cat > /app/Copaiba.AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Configura paths
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin/_internal:${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Qt platform plugin
export QT_PLUGIN_PATH="${HERE}/usr/bin/_internal/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/bin/_internal/PySide6/Qt/plugins/platforms"

# XDG
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"

exec "${HERE}/usr/bin/Copaiba_Linux" "$@"
APPRUN_EOF
chmod +x /app/Copaiba.AppDir/AppRun

# Copia ícone
cp /app/favicon.ico /app/Copaiba.AppDir/copaiba.png 2>/dev/null || touch /app/Copaiba.AppDir/copaiba.png
cp /app/favicon.ico /app/Copaiba.AppDir/usr/share/icons/hicolor/256x256/apps/copaiba.png 2>/dev/null || true

# Cria arquivo .desktop
cat > /app/Copaiba.AppDir/copaiba.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=Copaiba Lexikon
Exec=Copaiba_Linux
Icon=copaiba
Type=Application
Categories=AudioVideo;Audio;
Comment=OTO Editor for UTAU voicebanks
DESKTOP_EOF
cp /app/Copaiba.AppDir/copaiba.desktop /app/Copaiba.AppDir/usr/share/applications/

echo "📦 Creating AppImage with appimagetool..."

# Baixa appimagetool se não existir
if [ ! -f /tmp/appimagetool ]; then
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O /tmp/appimagetool
    chmod +x /tmp/appimagetool
    cd /tmp && ./appimagetool --appimage-extract
fi

cd /app
ARCH=x86_64 /tmp/squashfs-root/AppRun Copaiba.AppDir /app/dist/Copaiba_Lexikon-x86_64.AppImage

# Também copia o diretório regular para backup
echo "✅ Build complete!"
echo "📁 AppImage: /app/dist/Copaiba_Lexikon-x86_64.AppImage"
echo "📁 Directory: /app/dist/Copaiba_Linux/"

ls -la /app/dist/
