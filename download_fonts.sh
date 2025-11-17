#!/bin/bash
# 快速下载 Font Awesome 字体文件

set -e

BASE_DIR="static/fontawesome"
mkdir -p "$BASE_DIR/webfonts"

echo "下载 Font Awesome 字体文件..."

curl -L -o "$BASE_DIR/webfonts/fa-solid-900.woff2" https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2
curl -L -o "$BASE_DIR/webfonts/fa-regular-400.woff2" https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2
curl -L -o "$BASE_DIR/webfonts/fa-brands-400.woff2" https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2
curl -L -o "$BASE_DIR/webfonts/fa-v4compatibility.woff2" https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-v4compatibility.woff2

# 修改 Font Awesome CSS 中的字体路径（如果 CSS 文件存在）
if [ -f "$BASE_DIR/all.min.css" ]; then
    echo "修改 Font Awesome CSS 字体路径..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' 's|https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/|../webfonts/|g' "$BASE_DIR/all.min.css"
    else
        # Linux
        sed -i 's|https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/|../webfonts/|g' "$BASE_DIR/all.min.css"
    fi
    echo "✅ 字体文件下载完成，CSS 路径已更新！"
else
    echo "⚠️  CSS 文件不存在，请先运行 download_static.sh"
fi

