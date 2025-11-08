# 推送到GitHub指南

## 方式1：使用脚本（推荐）

### 步骤1：在GitHub上创建仓库

1. 访问 https://github.com/new
2. 仓库名称填写：`travel`
3. 选择 **Public** 或 **Private**
4. **不要**勾选"Initialize this repository with a README"（我们已经有了）
5. 点击 "Create repository"

### 步骤2：运行推送脚本

```bash
./push_to_github.sh <你的GitHub用户名>
```

例如：
```bash
./push_to_github.sh zhiruiwang
```

## 方式2：手动推送

### 步骤1：在GitHub上创建仓库

1. 访问 https://github.com/new
2. 仓库名称填写：`travel`
3. 选择 **Public** 或 **Private**
4. **不要**勾选"Initialize this repository with a README"
5. 点击 "Create repository"

### 步骤2：添加远程仓库并推送

```bash
# 添加远程仓库（替换YOUR_USERNAME为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/travel.git

# 推送代码
git branch -M main
git push -u origin main
```

## 方式3：使用SSH（如果已配置SSH密钥）

```bash
# 添加远程仓库（替换YOUR_USERNAME为你的GitHub用户名）
git remote add origin git@github.com:YOUR_USERNAME/travel.git

# 推送代码
git branch -M main
git push -u origin main
```

## 验证

推送成功后，访问以下地址查看您的仓库：
```
https://github.com/YOUR_USERNAME/travel
```

## 常见问题

### 1. 认证失败

如果遇到认证问题，可以：

**使用Personal Access Token：**
1. 访问 https://github.com/settings/tokens
2. 生成新的token（选择repo权限）
3. 推送时使用token作为密码

**或配置SSH密钥：**
```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 复制公钥到GitHub
cat ~/.ssh/id_ed25519.pub
# 然后访问 https://github.com/settings/keys 添加SSH密钥
```

### 2. 仓库已存在

如果远程仓库已存在，先删除再添加：
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/travel.git
```

### 3. 分支名称问题

如果当前分支不是main，可以重命名：
```bash
git branch -M main
```

