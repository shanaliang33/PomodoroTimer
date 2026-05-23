# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 运行

```bash
cd PomodoroTimer
python pomodoro.py           # 带控制台窗口
pythonw pomodoro.py          # 后台运行（无控制台）
```

或双击 `启动番茄钟.bat`（使用 pythonw 静默启动）。

## 项目结构

单一文件应用，所有 GUI 和逻辑在 `pomodoro.py` 中。

- `settings.json` — 持久化配置（分钟值存储为秒数，如 25 分 = 1500）
- `history.json` — 每日番茄完成数（.gitignore 排除）
- `__pycache__/` — Python 缓存（.gitignore 排除）

## 架构

`PomodoroApp` 类管理三种状态和三种模式的状态机：

- **模式 (mode)**: `work` -> `short_break` / `long_break`（每 4 个番茄一次长休息）-> `work`
- **状态 (state)**: `idle` -> `running` -> `paused`（通过空格键循环）
- 计时器基于 `time.time()` 差值而非 `after()` 累加，避免漂移

核心方法链：`toggle_timer()` -> `start_timer()` / `pause_timer()` -> `tick()`（每秒更新） -> `on_timer_complete()`（自动切换模式）

## 配置字段

| 字段 | 说明 |
|------|------|
| work_time | 专注时长（秒） |
| short_break_time | 短休时长（秒） |
| long_break_time | 长休时长（秒） |
| long_break_interval | 几个番茄后长休 |
| daily_goal | 每日目标番茄数 |
| auto_start_break/work | 自动进入下一阶段 |
| always_on_top | 窗口置顶 |
| theme_color | 主题色 hex |

## 快捷键

| 按键 | 功能 |
|------|------|
| 空格 | 开始/暂停 |
| ESC | 重置 |
| Ctrl+S | 设置 |
| Ctrl+Q | 退出 |
