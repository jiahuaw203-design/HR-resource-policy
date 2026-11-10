#!/usr/bin/env bash
# 人力资源政策雷达 - 一键更新（macOS / Linux）
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  人力资源政策雷达 - 一键更新"
echo "========================================"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "[失败] 没有找到 Python，请先安装 Python 3.8 以上版本。"
  exit 1
fi

echo "[1/2] 检查依赖..."
$PY -m pip install -r requirements.txt --quiet || echo "[提示] 依赖安装可能没成功，继续尝试抓取。"

echo ""
echo "[2/2] 开始抓取，大约需要 1-2 分钟..."
$PY fetch_policies.py

echo ""
echo "完成。打开 index.html 检查一下，再上传到 GitHub。"
#（注：内容由AI生成）
