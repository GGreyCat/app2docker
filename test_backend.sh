#!/bin/bash

echo "🧪 测试后端 API"
echo "================================"

# 测试模板列表
echo ""
echo "1️⃣ 测试模板列表 API..."
TEMPLATES=$(curl -s http://localhost:8000/templates)
COUNT=$(echo $TEMPLATES | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('items', [])))")
echo "   找到 $COUNT 个模板"

if [ "$COUNT" -gt "0" ]; then
    echo "   ✅ 模板列表正常"
    echo $TEMPLATES | python3 -m json.tool | head -30
else
    echo "   ❌ 模板列表为空（需要重启后端）"
fi

# 测试单个模板
echo ""
echo "2️⃣ 测试获取单个模板..."
TEMPLATE=$(curl -s "http://localhost:8000/templates?name=dragonwell8")
if echo $TEMPLATE | grep -q '"name"'; then
    echo "   ✅ 模板获取成功"
    echo $TEMPLATE | python3 -m json.tool | head -20
else
    echo "   ❌ 模板获取失败"
    echo "   错误: $TEMPLATE"
    echo ""
    echo "   🔧 请重启后端服务："
    echo "      python backend/app.py"
fi

echo ""
echo "================================"

