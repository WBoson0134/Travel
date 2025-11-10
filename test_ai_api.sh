#!/bin/bash

# AI API测试脚本
# 确保后端服务已启动: bash run_backend.sh

echo "=========================================="
echo "AI API 测试脚本"
echo "=========================================="
echo ""

# 测试1：查看配置状态
echo "【测试1】查看AI提供商配置状态"
echo "----------------------------------------"
curl -s http://localhost:8000/api/ai/providers | python3 -m json.tool
echo ""
echo ""

# 测试2：对话（OpenAI兼容类 - 阿里云）
echo "【测试2】AI对话测试（阿里云百炼）"
echo "----------------------------------------"
echo "请求："
echo '{
  "provider": "aliyun",
  "model": "qwen2.5-7b-instruct",
  "messages": [
    {"role":"system","content":"You are TripApp assistant."},
    {"role":"user","content":"用一句话介绍你自己"}
  ]
}'
echo ""
echo "响应："
curl -s http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aliyun",
    "model": "qwen2.5-7b-instruct",
    "messages": [
      {"role":"system","content":"You are TripApp assistant."},
      {"role":"user","content":"用一句话介绍你自己"}
    ]
  }' | python3 -m json.tool
echo ""
echo ""

# 测试3：对话（Dify原生）
echo "【测试3】AI对话测试（Dify）"
echo "----------------------------------------"
echo "请求："
echo '{
  "provider": "dify",
  "messages": [
    {"role":"system","content":"你是TripApp助手"},
    {"role":"user","content":"简要介绍一下京都两日游"}
  ]
}'
echo ""
echo "响应："
curl -s http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "dify",
    "messages": [
      {"role":"system","content":"你是TripApp助手"},
      {"role":"user","content":"简要介绍一下京都两日游"}
    ]
  }' | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "注意："
echo "- 如果看到 'No LLM providers configured'，请在 .env 文件中配置API密钥"
echo "- 确保 OPENAI_BASE_URL 和 OPENAI_API_KEY 已正确配置"
echo "- 对于阿里云百炼，BASE_URL 应该是: https://dashscope.aliyun.com/api/v1"
echo "- 对于Dify，DIFY_API_BASE 应该是: https://api.dify.ai/v1"

