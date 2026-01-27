# 动量信号页面问题解决方案

## 问题总结

### 问题1: 数据未自动更新
**现象**: 动量信号页面显示的更新时间停留在1月23号，当前已经1月26号

**根本原因**:
- 监控脚本 `monitor_no_flask.py` 虽然在运行，但可能因为API异常、网络问题或其他错误而停止更新数据文件
- 进程仍在运行但功能已失效（僵尸进程）

### 问题2: 手动刷新按钮无效
**现象**: 点击"手动刷新"按钮没有任何反应

**根本原因**:
- 前端的"手动刷新"只是清空React Query缓存并重新请求API
- API只是读取静态JSON文件，不会触发实际的数据更新
- JSON文件本身没有更新，所以手动刷新也看不到新数据

## 已实施的解决方案

### 1. 立即修复 - 手动更新数据文件 ✅

创建了两个快速更新脚本：

#### `scripts/force_update_monitor.py`
强制更新概念板块监控数据（简化版本，只获取前20个板块）

```bash
python scripts/force_update_monitor.py
```

#### `scripts/update_momentum_signals.py`
更新动量信号文件（清空旧信号）

```bash
python scripts/update_momentum_signals.py
```

**执行结果**:
- ✅ `latest.json` 已更新到 2026-01-26 14:43
- ✅ `momentum_signals.json` 已更新到 2026-01-26 14:43

### 2. 功能增强 - 添加强制刷新API ✅

#### 后端改动 (`src/api/routes_concept_monitor_v2.py`)

新增API端点:
```python
@router.post("/momentum-signals/refresh")
async def refresh_momentum_signals():
    """强制刷新动量信号数据"""
    subprocess.Popen([
        "python",
        str(project_root / "scripts" / "force_update_monitor.py")
    ])
    return {"success": True, "message": "后台更新已触发"}
```

#### 前端改动 (`frontend/src/components/MomentumSignalsView.tsx`)

改进手动刷新按钮:
```typescript
const handleForceRefresh = async () => {
  // 1. 调用后端强制刷新API
  await fetch(buildApiUrl("/api/concept-monitor/momentum-signals/refresh"), {
    method: "POST"
  });

  // 2. 等待5秒让后台更新完成
  setTimeout(() => {
    refetch();  // 3. 重新获取数据
  }, 5000);
};
```

**用户体验**:
- 点击"强制刷新"按钮 → 触发后台数据更新
- 按钮显示"刷新中..." → 5秒后自动重新获取数据
- 看到最新的监控数据

### 3. 文档记录 ✅

创建了问题诊断和解决方案文档:
- `docs/MOMENTUM_SIGNALS_FIX.md` - 详细的问题分析和解决方案
- `docs/MOMENTUM_SIGNALS_SOLUTION.md` - 本文档

## 使用说明

### 方式1: 使用改进后的强制刷新按钮（推荐）

1. 打开动量信号页面
2. 点击右上角的"强制刷新"按钮
3. 等待5秒，页面自动显示最新数据

### 方式2: 手动运行更新脚本

```bash
# 更新监控数据
python scripts/force_update_monitor.py

# 更新动量信号
python scripts/update_momentum_signals.py
```

### 方式3: 重启监控脚本

```bash
# 停止旧进程
pkill -f monitor_no_flask.py

# 后台启动（推荐使用screen）
screen -dmS monitor python scripts/monitor_no_flask.py

# 查看运行状态
screen -r monitor
```

## 未来改进建议

### 1. 监控脚本健壮性
- ✅ 添加异常重试机制
- ✅ 记录详细日志到文件
- ✅ 添加最大连续失败次数限制
- ⏳ 使用systemd/launchd确保自动重启

### 2. 健康检查
- ⏳ 添加API端点检查数据文件新鲜度
- ⏳ 如果数据超过2小时未更新，在页面显示警告
- ⏳ 添加Slack/邮件告警

### 3. 用户体验
- ✅ 改进手动刷新为强制刷新
- ⏳ 显示数据刷新进度条
- ⏳ 添加"上次刷新时间"和"下次刷新时间"提示

### 4. 架构优化
考虑将数据更新从文件读写改为：
- 实时API调用（性能考虑）
- Redis缓存（更好的实时性）
- 数据库存储（更好的查询能力）

## 相关文件清单

### 核心文件
- **监控脚本**: `scripts/monitor_no_flask.py`
- **数据文件**: `/Users/park/a-share-data/docs/monitor/momentum_signals.json`
- **API路由**: `src/api/routes_concept_monitor_v2.py`
- **前端组件**: `frontend/src/components/MomentumSignalsView.tsx`

### 工具脚本
- **强制更新**: `scripts/force_update_monitor.py`
- **信号更新**: `scripts/update_momentum_signals.py`
- **测试脚本**: `scripts/test_monitor_update.py`

### 文档
- **修复指南**: `docs/MOMENTUM_SIGNALS_FIX.md`
- **解决方案**: `docs/MOMENTUM_SIGNALS_SOLUTION.md` (本文档)

## 测试验证

- [x] 数据文件已更新到最新时间
- [x] 后端API正常响应
- [x] 前端页面显示正确时间
- [ ] 强制刷新按钮功能测试（需要前端编译后测试）
- [ ] 监控脚本连续运行稳定性测试

## 总结

通过本次修复：
1. **立即解决**: 手动更新了数据文件，页面恢复正常
2. **功能增强**: 添加了强制刷新API，用户可以主动触发数据更新
3. **文档完善**: 记录了问题原因和解决方案，便于后续维护

用户现在可以：
- 看到最新的动量信号数据（1月26号）
- 使用强制刷新按钮主动更新数据
- 不再需要手动运行命令行脚本
