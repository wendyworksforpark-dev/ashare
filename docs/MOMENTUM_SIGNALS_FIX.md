# 动量信号页面更新问题修复

## 问题描述

1. **数据未更新**: 动量信号页面显示的更新时间是1月23号，当前已经是1月26号
2. **手动刷新无效**: 点击"手动刷新"按钮没有任何反应

## 问题原因

### 1. 监控进程停止更新
- 监控脚本 `monitor_no_flask.py` (PID 34682) 在运行但没有更新数据文件
- 数据文件 `/Users/park/a-share-data/docs/monitor/momentum_signals.json` 停留在1月23号
- 可能原因：
  - API调用失败（网络问题、API限流）
  - 脚本异常退出但进程仍在运行
  - 数据库连接问题

### 2. 手动刷新按钮的工作机制
- 前端的"手动刷新"按钮只是清空React Query缓存并重新请求API
- API读取的是JSON文件 `/Users/park/a-share-data/docs/monitor/momentum_signals.json`
- 如果JSON文件本身没有更新，手动刷新也不会有新数据

## 解决方案

### 临时解决方案（已执行）

1. **手动更新数据文件**:
   ```bash
   # 更新概念板块数据
   python scripts/force_update_monitor.py

   # 更新动量信号数据
   python scripts/update_momentum_signals.py
   ```

2. **验证文件已更新**:
   ```bash
   ls -lh /Users/park/a-share-data/docs/monitor/
   ```

   结果：
   - `latest.json`: Jan 26 14:43
   - `momentum_signals.json`: Jan 26 14:43

### 长期解决方案

#### 方案1: 改进监控脚本（推荐）

添加异常处理和日志记录：

```python
def run_continuous():
    """持续运行 - 添加错误恢复"""
    iteration = 0
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 5

    while True:
        try:
            iteration += 1
            print(f"\n第{iteration}轮监控 - {datetime.now()}")

            update_data()
            consecutive_errors = 0  # 重置错误计数

            print(f"\n⏰ 等待 {UPDATE_INTERVAL}秒...")
            time.sleep(UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断，停止监控")
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"\n❌ 更新失败 ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}): {e}")

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"连续失败{MAX_CONSECUTIVE_ERRORS}次，退出监控")
                break

            print(f"等待30秒后重试...")
            time.sleep(30)
```

#### 方案2: 添加API端点支持强制刷新

在 `routes_concept_monitor_v2.py` 中添加：

```python
@router.post("/momentum-signals/refresh")
async def refresh_momentum_signals():
    """强制刷新动量信号（触发后台更新）"""
    try:
        # 运行一次更新脚本
        import subprocess
        subprocess.Popen([
            "python",
            "/Users/park/a-share-data/scripts/monitor_no_flask.py",
            "--once"
        ])

        return {
            "success": True,
            "message": "已触发后台更新，请稍后刷新页面"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

前端添加调用：

```typescript
const handleForceRefresh = async () => {
  try {
    await fetch(buildApiUrl("/api/concept-monitor/momentum-signals/refresh"), {
      method: "POST"
    });

    // 等待几秒后自动刷新
    setTimeout(() => {
      refetch();
    }, 5000);

    alert("后台更新已触发，5秒后自动刷新");
  } catch (error) {
    console.error("强制刷新失败:", error);
  }
};
```

#### 方案3: 使用systemd/launchd服务监控

创建 systemd 服务（Linux）或 launchd plist（macOS）确保监控脚本持续运行并自动重启。

### 监控脚本管理命令

```bash
# 检查监控进程是否运行
ps aux | grep monitor_no_flask | grep -v grep

# 停止旧的监控进程
pkill -f monitor_no_flask.py

# 后台启动监控（推荐使用 screen 或 tmux）
screen -dmS monitor python scripts/monitor_no_flask.py

# 查看监控日志
screen -r monitor

# 单次更新（用于调试）
python scripts/monitor_no_flask.py --once
```

## 测试验证

1. 访问前端动量信号页面，确认时间已更新到1月26号
2. 点击"手动刷新"按钮，确认能正常获取数据
3. 重启监控脚本，观察是否持续更新

## 预防措施

1. **添加健康检查**: 定期检查数据文件的更新时间
2. **添加告警**: 如果数据超过2小时未更新，发送通知
3. **日志记录**: 将监控脚本的输出重定向到日志文件
4. **错误重试**: 单次失败不应该导致整个监控停止

## 相关文件

- 监控脚本: `scripts/monitor_no_flask.py`
- API路由: `src/api/routes_concept_monitor_v2.py`
- 前端组件: `frontend/src/components/MomentumSignalsView.tsx`
- 数据文件: `/Users/park/a-share-data/docs/monitor/momentum_signals.json`
- 强制更新脚本: `scripts/force_update_monitor.py`
- 信号更新脚本: `scripts/update_momentum_signals.py`
