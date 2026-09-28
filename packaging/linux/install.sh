#!/usr/bin/env sh
# Installs Document Converter for the current user and adds it to the app menu.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/share/document-converter"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/512x512/apps"

rm -rf "$DEST"
mkdir -p "$DEST" "$APPS" "$ICONS" "$HOME/.local/bin"
cp -R "$HERE/DocumentConverter/." "$DEST/"
cp "$HERE/document-converter.png" "$ICONS/document-converter.png"
ln -sf "$DEST/DocumentConverter" "$HOME/.local/bin/document-converter"

cat > "$APPS/document-converter.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Document Converter
Comment=Convert documents, spreadsheets, slides and eBooks
Exec="$DEST/DocumentConverter" %F
Icon=document-converter
Terminal=false
Categories=Office;Utility;
DESKTOP

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" || true
echo "Installed. Open Document Converter from your app menu."
