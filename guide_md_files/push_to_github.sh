#!/bin/bash

# 推送项目到GitHub的脚本
# 使用方法: ./push_to_github.sh <your-github-username>

if [ -z "$1" ]; then
    echo "使用方法: ./push_to_github.sh <your-github-username>"
    echo "例如: ./push_to_github.sh zhiruiwang"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="travel"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo "准备推送到 GitHub..."
echo "仓库地址: ${REPO_URL}"
echo ""

# 检查是否已经添加了远程仓库
if git remote | grep -q "origin"; then
    echo "远程仓库已存在，更新中..."
    git remote set-url origin ${REPO_URL}
else
    echo "添加远程仓库..."
    git remote add origin ${REPO_URL}
fi

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ]; then
    CURRENT_BRANCH="main"
fi

echo "当前分支: ${CURRENT_BRANCH}"
echo ""
echo "⚠️  请确保您已经在GitHub上创建了名为 'travel' 的仓库"
echo "   如果没有，请访问: https://github.com/new"
echo "   仓库名称填写: travel"
echo ""
read -p "按回车键继续推送，或按Ctrl+C取消..."

echo ""
echo "推送代码到GitHub..."
git push -u origin ${CURRENT_BRANCH}

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功推送到GitHub!"
    echo "   查看仓库: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "   1. 是否已在GitHub上创建了 'travel' 仓库"
    echo "   2. 是否已配置GitHub认证"
    echo "   3. 网络连接是否正常"
fi

