#!/bin/bash
set -e

echo "🔨 Building with PyInstaller..."
pyinstaller --clean Copaiba_Linux.spec

echo "📦 Creating AppDir structure..."
mkdir -p /app/Copaiba.AppDir/usr/bin
mkdir -p /app/Copaiba.AppDir/usr/lib
mkdir -p /app/Copaiba.AppDir/usr/share/applications
mkdir -p /app/Copaiba.AppDir/usr/share/icons/hicolor/256x256/apps

# Copia o conteúdo do PyInstaller para AppDir
cp -r /app/dist/Copaiba_Linux/* /app/Copaiba.AppDir/usr/bin/

# Cria o script de inicialização AppRun
cat > /app/Copaiba.AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin/_internal:${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/Copaiba_Linux" "$@"
EOF
chmod +x /app/Copaiba.AppDir/AppRun

# Copia ícone
cp /app/favicon.ico /app/Copaiba.AppDir/usr/share/icons/hicolor/256x256/apps/copaiba.ico
cp /app/favicon.ico /app/Copaiba.AppDir/copaiba.ico

# Cria arquivo .desktop
cat > /app/Copaiba.AppDir/copaiba.desktop << EOF
[Desktop Entry]
Name=Copaiba Lexikon
Exec=Copaiba_Linux
Icon=copaiba
Type=Application
Categories=AudioVideo;Audio;
Comment=OTO Editor for UTAU voicebanks
EOF
cp /app/Copaiba.AppDir/copaiba.desktop /app/Copaiba.AppDir/usr/share/applications/

# Cria link simbólico para o .desktop na raiz
ln -sf usr/share/applications/copaiba.desktop /app/Copaiba.AppDir/

echo "📦 Creating AppImage..."
cd /app
/usr/local/bin/appimagetool-run Copaiba.AppDir /app/dist/Copaiba_Lexikon-x86_64.AppImage

echo "✅ AppImage created: /app/dist/Copaiba_Lexikon-x86_64.AppImage"
