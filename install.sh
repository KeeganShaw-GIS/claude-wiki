#!/usr/bin/env bash
set -e

REPO="KeeganShaw-GIS/claude-wiki"
INSTALL_DIR="/usr/local/bin"

OS=$(uname -s)
ARCH=$(uname -m)

if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    BINARY="claude-wiki-macos-arm64"
elif [ "$OS" = "Linux" ] && [ "$ARCH" = "x86_64" ]; then
    BINARY="claude-wiki-linux-x86_64"
else
    echo "Unsupported platform: $OS $ARCH"
    exit 1
fi

URL="https://github.com/$REPO/releases/latest/download/$BINARY"

echo "Downloading $BINARY..."
curl -fsSL "$URL" -o /tmp/claude-wiki
chmod +x /tmp/claude-wiki
mv /tmp/claude-wiki "$INSTALL_DIR/claude-wiki"

echo "Installed to $INSTALL_DIR/claude-wiki"
claude-wiki --help
