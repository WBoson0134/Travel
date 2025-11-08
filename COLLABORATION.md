# 团队协作指南

## 给项目所有者（您）

### 添加协作者

有两种方式让同事参与协作：

#### 方式1：添加协作者（推荐用于私有仓库）

1. 访问仓库设置页面：https://github.com/WBoson0134/Travel/settings/access
2. 点击左侧菜单的 "Collaborators"
3. 点击 "Add people"
4. 输入同事的 GitHub 用户名或邮箱
5. 选择权限级别：
   - **Read**: 只能查看代码
   - **Write**: 可以推送代码（推荐）
   - **Admin**: 完全管理权限
6. 发送邀请，等待同事接受

#### 方式2：公开仓库（最简单）

如果仓库是公开的，任何人都可以克隆和提交 Pull Request。

检查仓库是否公开：
- 访问：https://github.com/WBoson0134/Travel/settings
- 在 "Danger Zone" 部分可以看到仓库可见性

---

## 给协作者（您的同事）

### 第一步：克隆仓库到本地

```bash
# 使用HTTPS（推荐）
git clone https://github.com/WBoson0134/Travel.git

# 或使用SSH（如果已配置SSH密钥）
git clone git@github.com:WBoson0134/Travel.git

# 进入项目目录
cd Travel
```

### 第二步：设置开发环境

#### 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件填入API密钥（可选）

# 初始化数据库
export FLASK_APP=backend/app.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 运行后端
python backend/app.py
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

### 第三步：创建新分支进行开发

```bash
# 确保在main分支并获取最新代码
git checkout main
git pull origin main

# 创建新分支（使用描述性的分支名）
git checkout -b feature/your-feature-name

# 例如：
# git checkout -b feature/add-user-authentication
# git checkout -b fix/map-display-bug
# git checkout -b docs/update-readme
```

### 第四步：进行开发和提交

```bash
# 进行代码修改...

# 查看更改
git status
git diff

# 添加更改
git add .

# 提交更改（使用清晰的提交信息）
git commit -m "描述你的更改：例如 '添加用户登录功能'"

# 推送到远程仓库
git push origin feature/your-feature-name
```

### 第五步：创建 Pull Request

1. 访问仓库：https://github.com/WBoson0134/Travel
2. 点击 "Pull requests" 标签
3. 点击 "New pull request"
4. 选择你的分支（feature/your-feature-name）
5. 填写 Pull Request 描述：
   - 说明你做了什么更改
   - 为什么做这些更改
   - 如何测试
6. 点击 "Create pull request"
7. 等待代码审查和合并

---

## 协作工作流程

### 推荐的工作流程

```
1. 从main分支创建新分支
   ↓
2. 在新分支上开发功能
   ↓
3. 提交并推送到远程
   ↓
4. 创建Pull Request
   ↓
5. 代码审查和讨论
   ↓
6. 合并到main分支
   ↓
7. 删除已合并的分支
```

### 保持代码同步

```bash
# 定期从main分支拉取最新代码
git checkout main
git pull origin main

# 如果有冲突，解决冲突后：
git add .
git commit -m "解决合并冲突"
git push
```

### 处理合并冲突

如果遇到冲突：

```bash
# 1. 拉取最新代码
git checkout main
git pull origin main

# 2. 回到你的分支
git checkout feature/your-feature-name

# 3. 合并main分支
git merge main

# 4. 如果有冲突，编辑冲突文件
# Git会用 <<<<<<< ======= >>>>>>> 标记冲突

# 5. 解决冲突后
git add .
git commit -m "解决合并冲突"
git push
```

---

## 分支命名规范

建议使用以下命名规范：

- `feature/功能名称` - 新功能
  - 例如：`feature/user-authentication`
- `fix/问题描述` - 修复bug
  - 例如：`fix/map-display-error`
- `docs/文档更新` - 文档相关
  - 例如：`docs/update-api-docs`
- `refactor/重构内容` - 代码重构
  - 例如：`refactor/optimize-database-queries`
- `test/测试内容` - 测试相关
  - 例如：`test/add-unit-tests`

---

## 提交信息规范

使用清晰的提交信息：

✅ **好的提交信息：**
```
feat: 添加用户登录功能
fix: 修复地图显示错误
docs: 更新API文档
refactor: 优化数据库查询性能
```

❌ **不好的提交信息：**
```
更新
修复
改了一下
```

---

## 代码审查清单

在创建 Pull Request 前，检查：

- [ ] 代码可以正常运行
- [ ] 没有破坏现有功能
- [ ] 添加了必要的注释
- [ ] 遵循了项目的代码风格
- [ ] 更新了相关文档（如果需要）
- [ ] 提交信息清晰明确

---

## 常用 Git 命令

```bash
# 查看状态
git status

# 查看更改
git diff

# 查看提交历史
git log --oneline

# 查看分支
git branch -a

# 切换分支
git checkout branch-name

# 创建并切换分支
git checkout -b new-branch

# 删除本地分支
git branch -d branch-name

# 删除远程分支
git push origin --delete branch-name

# 撤销未提交的更改
git checkout -- filename

# 查看远程仓库
git remote -v
```

---

## 需要帮助？

如果遇到问题：

1. 查看项目文档：README.md, SETUP.md
2. 检查 GitHub Issues
3. 联系项目维护者
4. 参考 Git 官方文档：https://git-scm.com/doc

---

## 快速参考

### 第一次设置（协作者）

```bash
git clone https://github.com/WBoson0134/Travel.git
cd Travel
# 设置开发环境（见上方）
```

### 日常开发流程

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
# 进行开发...
git add .
git commit -m "描述更改"
git push origin feature/my-feature
# 然后在GitHub上创建Pull Request
```

### 更新本地代码

```bash
git checkout main
git pull origin main
```

