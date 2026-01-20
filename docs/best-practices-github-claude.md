# GitHub + Claude Code 最佳实践指南

本文档介绍如何结合使用GitHub和Claude Code来高效管理A股数据监控项目。

---

## 📋 目录

1. [Claude Code工作流程](#claude-code工作流程)
2. [提交策略](#提交策略)
3. [分支管理](#分支管理)
4. [代码审查](#代码审查)
5. [文档维护](#文档维护)
6. [问题追踪](#问题追踪)
7. [安全实践](#安全实践)
8. [性能优化](#性能优化)

---

## Claude Code工作流程

### 1. 开始新任务前

**✅ 推荐做法**：
```bash
# 1. 确保在main分支且是最新的
git checkout main
git pull origin main

# 2. 检查当前状态
git status

# 3. 创建新的功能分支
git checkout -b feature/任务描述

# 4. 告诉Claude你在新分支上工作
```

**与Claude对话示例**：
```
我现在在 feature/market-aware-polling 分支上，
需要实现Market On/Off自动切换机制。
请帮我：
1. 先诊断现有代码
2. 制定实施计划
3. 逐步实现
4. 验证功能
```

### 2. 开发过程中

**✅ 小步提交**：
```bash
# Claude修改了代码后，立即提交
git add src/hooks/useRealtimePrice.ts
git commit -m "feat(frontend): 导出isMarketOpen函数供其他组件使用"

# 不要等所有修改完成才提交
```

**✅ 使用描述性提交信息**：
```bash
# ❌ 不好的提交
git commit -m "修复bug"

# ✅ 好的提交
git commit -m "fix(scheduler): 添加await关键字修复指数日线更新bug

- 位置: src/services/kline_scheduler.py:103
- 问题: 异步函数缺少await导致未执行
- 影响: 所有指数日线现可正常更新"
```

**✅ 定期推送到GitHub**：
```bash
# 每完成一个小功能就推送
git push origin feature/market-aware-polling

# 好处：
# 1. 备份代码
# 2. 团队可见进度
# 3. 可在其他机器继续工作
```

### 3. 完成任务后

**✅ 创建Pull Request前检查**：
```bash
# 1. 确保所有测试通过
pytest tests/

# 2. 检查代码质量
flake8 src/

# 3. 更新文档
# 编辑 README.md 或相关文档

# 4. 推送最终版本
git push origin feature/market-aware-polling
```

**✅ 在GitHub创建PR**：
1. 访问 https://github.com/zinan92/ashare
2. 点击 "Compare & pull request"
3. 填写PR描述：
```markdown
## 修改内容
实现Market On/Off自动切换机制

## 修改文件
- frontend/src/hooks/useRealtimePrice.ts
- frontend/src/components/IndexChart.tsx
- frontend/src/components/ConceptKlineCard.tsx

## 测试
- [x] 手动测试Market On行为
- [x] 手动测试Market Off行为
- [x] 前端构建成功

## 关联Issue
Closes #1
```

---

## 提交策略

### Atomic Commits（原子提交）

**原则**：每个提交只做一件事

**✅ 推荐**：
```bash
# Commit 1: 只添加函数
git commit -m "feat(hooks): 导出isMarketOpen函数"

# Commit 2: 只修改IndexChart
git commit -m "feat(IndexChart): 添加Market Off停止轮询逻辑"

# Commit 3: 只修改ConceptKlineCard
git commit -m "feat(ConceptKlineCard): 添加Market Off停止轮询逻辑"
```

**❌ 避免**：
```bash
# 一次提交做太多事
git commit -m "添加Market On/Off功能并修复bug还更新了文档"
```

### 提交频率

**与Claude协作时**：
- ✅ Claude每修改1-3个文件就提交一次
- ✅ 每个独立功能提交一次
- ❌ 不要等Claude完成所有任务才提交

**好处**：
- 清晰的提交历史
- 容易回滚特定修改
- 方便代码审查

### Commit Message模板

```bash
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建/工具

**示例**：
```bash
git commit -m "fix(scheduler): 修复指数日线未更新bug

问题描述:
- update_index_daily()是async函数但缺少await
- 导致函数未执行，指数日线数据未更新

解决方案:
- 在kline_scheduler.py:103添加await关键字

验证:
- 手动触发更新任务，日线数据正常更新
- 查看日志确认\"开始更新指数日线数据\"出现

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 分支管理

### 分支命名规范

```
feature/功能描述    # 新功能
fix/bug描述         # Bug修复
refactor/重构描述   # 代码重构
docs/文档更新       # 文档修改
perf/性能优化描述   # 性能优化
```

**示例**：
```bash
feature/market-aware-polling
fix/concept-monitor-stale-data
refactor/kline-service-cleanup
docs/update-api-reference
perf/reduce-api-calls
```

### 与Claude协作的分支策略

**场景1：新功能开发**
```bash
# 1. 创建功能分支
git checkout -b feature/data-consistency-validator

# 2. 告诉Claude
"我在 feature/data-consistency-validator 分支上，
需要创建数据一致性验证系统"

# 3. Claude开发过程中多次提交
# 4. 完成后创建PR合并到main
```

**场景2：紧急Bug修复**
```bash
# 1. 从main创建hotfix分支
git checkout main
git checkout -b hotfix/monitor-script-hanging

# 2. 快速修复
# 3. 直接合并回main
git checkout main
git merge hotfix/monitor-script-hanging
git push origin main
```

**场景3：实验性功能**
```bash
# 1. 创建实验分支
git checkout -b experiment/new-chart-library

# 2. 让Claude尝试新方案
# 3. 如果不满意，直接删除分支
git checkout main
git branch -D experiment/new-chart-library
```

### 分支保护

**在GitHub设置**：
1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. 勾选：
   - ✅ Require a pull request before merging
   - ✅ Require approvals (如果是团队项目)
   - ✅ Dismiss stale pull request approvals when new commits are pushed

---

## 代码审查

### 与Claude的协作审查

**✅ 让Claude先审查自己的代码**：
```
Claude，请审查你刚才写的代码，检查：
1. 是否有潜在的bug
2. 性能是否可优化
3. 代码是否符合项目规范
4. 是否需要添加注释
```

**✅ 在PR中请求具体反馈**：
```markdown
## 需要重点审查的部分

1. **src/services/data_consistency_validator.py**
   - 容忍度0.01%是否合理？
   - 验证逻辑是否有遗漏？

2. **frontend/src/hooks/useConceptMonitor.ts**
   - Market Off时的轮询停止逻辑是否正确？
```

### Self-Review清单

在创建PR前，让Claude帮你检查：

```
请帮我审查这次PR，确认：

□ 所有修改的文件都有明确目的
□ 没有遗留的console.log或调试代码
□ 没有注释掉的代码
□ 错误处理充分
□ 没有硬编码的值（应该用配置）
□ 文档已更新
□ 测试覆盖关键逻辑
```

---

## 文档维护

### 与代码同步更新

**原则**：代码改了，文档必须同步更新

**✅ 推荐做法**：
```bash
# 修改代码
git add src/services/kline_scheduler.py

# 立即更新相关文档
git add docs/deployment-verification.md
git add README.md

# 一起提交
git commit -m "feat: 添加数据一致性验证任务

- 新增15:45自动验证任务
- 更新部署文档说明新任务
- README添加验证方法"
```

### 文档类型

**1. README.md** - 项目首页
- 功能特性
- 快速开始
- 项目结构
- 常见问题

**2. docs/api-reference.md** - API文档
```markdown
## GET /api/concept-monitor/top

获取涨幅前N的概念板块

**参数**:
- n: 返回数量 (默认20)

**响应**:
{
  "success": true,
  "timestamp": "2026-01-20 09:56:09",
  "data": [...]
}
```

**3. docs/troubleshooting.md** - 故障排除
```markdown
## 问题：概念监控数据不更新

**症状**: API返回昨天的时间戳

**原因**: monitor_no_flask.py脚本停止运行

**解决**:
```bash
# 重启脚本
kill $(ps aux | grep monitor_no_flask | awk '{print $2}')
nohup python3 scripts/monitor_no_flask.py > logs/monitor.log 2>&1 &
```
```

**4. 代码注释**
```python
# ✅ 好的注释 - 解释"为什么"
# Market Off时不再轮询，因为：
# 1. 数据不会变化（收盘后）
# 2. 节省服务器资源
# 3. 减少API调用成本
if not isMarketOpen():
    return

# ❌ 不必要的注释 - 只是重复代码
# 检查市场是否开放
if not isMarketOpen():
    return
```

---

## 问题追踪

### 使用GitHub Issues

**何时创建Issue**：
1. 发现Bug
2. 有新功能想法
3. 需要改进现有功能
4. 文档需要更新
5. 有疑问需要讨论

### Issue模板

**Bug Report**：
```markdown
### Bug描述
概念监控数据在开盘时间未更新

### 复现步骤
1. 访问首页
2. 查看"涨幅 top20"
3. 时间戳显示昨天

### 预期行为
开盘时间应显示今天的数据并实时更新

### 实际行为
显示昨天17:47的数据

### 环境
- 时间: 2026-01-20 09:45
- 浏览器: Chrome
- 服务器: macOS

### 可能原因
监控脚本未运行

### 解决方案
重启monitor_no_flask.py
```

**Feature Request**：
```markdown
### 功能描述
添加概念板块的5日/10日涨幅趋势图

### 动机
- 更好地判断板块强度
- 识别持续上涨的板块
- 辅助投资决策

### 建议实现
1. 在概念卡片下方添加迷你趋势图
2. 使用Lightweight Charts
3. 显示最近10日收盘价

### 优先级
Medium
```

### 与Claude协作处理Issue

```
Claude，我刚创建了Issue #5："添加概念板块趋势图"
请帮我：
1. 评估实现难度
2. 列出需要修改的文件
3. 制定实施步骤
4. 预估开发时间
```

---

## 安全实践

### 1. 敏感信息管理

**❌ 绝对不要提交**：
```python
# 不要这样做
API_KEY = "your-actual-api-key-here"
DATABASE_URL = "postgresql://user:password@host/db"
SECRET_KEY = "super-secret-key-123"
```

**✅ 使用环境变量**：
```python
# .env (已在.gitignore中)
API_KEY=your-actual-api-key
DATABASE_URL=postgresql://user:password@host/db

# 代码中
import os
API_KEY = os.getenv("API_KEY")
```

**✅ 提供示例文件**：
```bash
# .env.example (可以提交)
API_KEY=your_api_key_here
DATABASE_URL=postgresql://localhost/db_name
SECRET_KEY=your_secret_key
```

### 2. 检查提交内容

**在提交前**：
```bash
# 查看将要提交的内容
git diff --cached

# 确保没有敏感信息
grep -r "password" .
grep -r "secret" .
grep -r "token" .
```

### 3. 如果不慎提交了敏感信息

```bash
# 1. 立即从Git历史中删除
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive/file" \
  --prune-empty --tag-name-filter cat -- --all

# 2. 强制推送（危险操作！）
git push origin --force --all

# 3. 立即更换泄露的密钥/密码
```

### 4. 让Claude帮忙检查

```
Claude，请检查我即将提交的文件，
确保没有包含：
- API密钥
- 密码
- 数据库连接字符串
- 个人信息
```

---

## 性能优化

### 1. 大文件处理

**✅ 使用Git LFS**（大文件存储）：
```bash
# 安装Git LFS
git lfs install

# 追踪大文件
git lfs track "*.db"
git lfs track "*.csv"
git lfs track "docs/monitor/*.json"

# 提交.gitattributes
git add .gitattributes
git commit -m "chore: 使用Git LFS追踪大文件"
```

**✅ 排除不必要的文件**：
```bash
# .gitignore
logs/
data/
*.sqlite
frontend/node_modules/
frontend/dist/
.venv/
__pycache__/
```

### 2. 提交优化

**合并小提交**（在推送前）：
```bash
# 交互式rebase最近3个提交
git rebase -i HEAD~3

# 在编辑器中将pick改为squash
pick abc1234 feat: 添加功能A
squash def5678 fix: 修复功能A的bug
squash ghi9012 refactor: 优化功能A
```

**结果**：
```bash
# 3个提交合并成1个
feat: 添加功能A并优化
```

### 3. 分支清理

**定期清理已合并的分支**：
```bash
# 查看已合并的分支
git branch --merged

# 删除本地分支
git branch -d feature/old-feature

# 删除远程分支
git push origin --delete feature/old-feature

# 清理远程分支引用
git fetch --prune
```

---

## Claude Code特定最佳实践

### 1. 会话管理

**✅ 在会话开始时说明背景**：
```
我正在开发A股数据监控系统，使用FastAPI + React。
当前在feature/market-aware-polling分支。
需要实现Market On/Off自动切换功能。
相关文档在docs/market-hours-logic.md。
```

**✅ 明确任务范围**：
```
请只修改前端的Market Off逻辑，
不要改动后端代码。
完成后提交代码并构建。
```

**❌ 避免模糊指令**：
```
# 不好
"帮我优化代码"

# 好  
"优化src/services/kline_updater.py的数据库查询性能，
减少N+1查询问题"
```

### 2. 代码审查提示

**让Claude说明修改原因**：
```
Claude，在修改代码前，请先：
1. 说明为什么需要这样修改
2. 列出将要修改的文件
3. 解释可能的影响
4. 等我确认后再执行
```

### 3. 测试验证

**要求Claude提供测试步骤**：
```
Claude，修改完成后请提供：
1. 如何手动测试这个功能
2. 预期看到的结果
3. 如何验证修改成功
```

### 4. 增量开发

**✅ 分阶段让Claude工作**：
```
# 阶段1
"先帮我诊断问题，不要修改代码"

# 阶段2  
"诊断结果确认后，制定修复计划"

# 阶段3
"按计划修复第一个问题"

# 阶段4
"验证修复效果，如果OK继续下一个"
```

**❌ 避免一次给太多任务**：
```
"帮我修复所有bug、添加新功能、优化性能、更新文档..."
```

---

## 团队协作最佳实践

### 1. PR Review流程

**作为PR作者**：
```markdown
## Self-Review完成
- [x] 所有测试通过
- [x] 代码符合规范
- [x] 文档已更新
- [x] 无敏感信息

## 需要Reviewer关注
1. kline_scheduler.py:103 的await添加
2. 容忍度0.01%是否合理

## 测试方法
1. 启动后端: `python -m uvicorn web.app:app`
2. 等待15:45自动验证
3. 查看logs/service.log确认"数据一致性验证"
```

**作为Reviewer**：
```markdown
## Code Review Comments

**src/services/data_consistency_validator.py:45**
```python
# 建议添加错误处理
try:
    is_healthy = await self.validator.validate_all()
except Exception as e:
    logger.error(f"验证失败: {e}")
    return False
```

**批准条件**：
- [ ] 作者解决所有comments
- [ ] CI/CD通过
- [ ] 文档完整
```

### 2. 冲突解决

**当有冲突时**：
```bash
# 1. 拉取最新main
git checkout main
git pull origin main

# 2. 切换到你的分支
git checkout feature/your-feature

# 3. 合并main（会显示冲突）
git merge main

# 4. 让Claude帮助解决冲突
```

**与Claude对话**：
```
Git显示以下文件有冲突：
- src/services/kline_updater.py

请帮我：
1. 查看冲突内容
2. 理解两边的修改
3. 建议如何合并
4. 解决冲突
```

---

## 快速参考

### 每日工作流

```bash
# 早上开始工作
git checkout main
git pull origin main
git checkout -b feature/today-task

# 与Claude协作开发
# ... Claude修改代码 ...
git add .
git commit -m "feat: 描述"

# 定期推送
git push origin feature/today-task

# 完成后
# 在GitHub创建PR → Code Review → 合并
```

### 提交检查清单

在执行`git commit`前：
- [ ] 代码可运行
- [ ] 测试通过
- [ ] 无console.log/调试代码
- [ ] 无敏感信息
- [ ] 提交信息清晰
- [ ] 文档已更新

### 紧急情况

**回滚最后一次提交**：
```bash
git reset --soft HEAD~1  # 保留修改
git reset --hard HEAD~1  # 丢弃修改
```

**撤销已推送的提交**：
```bash
git revert <commit-hash>
git push origin main
```

---

## 总结

### 核心原则

1. **小步提交** - 每次只改一件事
2. **清晰命名** - 分支、提交信息都要描述性强
3. **及时推送** - 完成一个功能就推送到GitHub
4. **文档同步** - 代码改了文档必须跟着改
5. **安全第一** - 绝不提交敏感信息
6. **增量开发** - 与Claude分阶段协作

### 与Claude协作的黄金法则

1. **明确任务** - 清楚说明要做什么
2. **提供上下文** - 告诉Claude项目背景
3. **分步执行** - 不要一次给太多任务
4. **验证结果** - 每步完成后验证
5. **保持沟通** - 有疑问立即询问Claude

---

**最后更新**: 2026-01-20
**适用版本**: Claude Sonnet 4.5
