# 🔥 VSCode 调试热重载配置说明

## 功能说明

本项目已配置支持后端代码的**自动热重载**功能。当您在调试模式下修改 Python 代码时，服务器会自动重启，无需手动停止和重新启动调试会话。

## 使用方法

### 1. 安装依赖

首先确保安装了最新的依赖：

```bash
pip install -r requirements.txt
```

### 2. 选择调试配置

在 VSCode 中，按 `F5` 或点击调试面板，您会看到以下配置：

#### 🔹 单独调试配置：

- **Python: 后端服务器** - 普通模式（无热重载）
- **Python: 后端服务器 (热重载)** ✨ - 支持热重载
- **前端: Vite Dev Server** - 前端开发服务器

#### 🔹 全栈调试配置：

- **全栈调试 (前端+后端)** - 普通模式
- **全栈调试 (热重载)** ✨ - 前端+后端都支持热重载

### 3. 开始调试

1. 选择 **"Python: 后端服务器 (热重载)"** 或 **"全栈调试 (热重载)"**
2. 按 `F5` 开始调试
3. 修改任意 `.py` 文件并保存
4. 服务器会自动检测变化并重启

## 工作原理

### 热重载实现

- 使用 `watchdog` 库监控 `backend/` 目录下的所有 `.py` 文件
- 检测到文件变化后，自动重启服务器进程
- 包含 1 秒的防抖延迟，避免频繁重启

### 不监控的目录

为了提高性能，以下目录不会触发重载：

- `data/` - 数据目录
- `frontend/` - 前端代码
- `node_modules/` - Node 依赖
- `__pycache__/` - Python 缓存
- `.git/` - Git 目录
- `dist/` - 构建产物

## 调试技巧

### 1. 断点调试

即使在热重载模式下，您依然可以：

- 设置断点
- 单步调试
- 查看变量
- 使用调试控制台

**注意：** 当代码重载时，断点会保持，但当前的调试会话会中断。

### 2. 查看重载日志

在集成终端中，您会看到类似的日志：

```
🔄 检测到文件变化: /path/to/backend/handlers.py
⏳ 正在重启服务器...
```

### 3. 禁用热重载

如果您需要在某些情况下禁用热重载（例如进行长时间的断点调试），可以选择：

- 使用 **"Python: 后端服务器"** 配置（普通模式）
- 或者临时停止调试并手动启动服务器

## 配置文件

### launch.json

位置：`.vscode/launch.json`

热重载配置的关键参数：

```json
{
  "name": "Python: 后端服务器 (热重载)",
  "type": "debugpy",
  "program": "${workspaceFolder}/backend/app_dev.py",
  "subProcess": true // 允许调试子进程
}
```

### 开发启动脚本

位置：`backend/app_dev.py`

这个脚本负责：

1. 启动后端服务器进程
2. 监控文件变化
3. 自动重启服务器

## 常见问题

### Q: 修改代码后没有自动重载？

**A:** 检查以下几点：

1. 确保使用的是 **"(热重载)"** 配置
2. 确保修改的是 `.py` 文件
3. 检查文件是否在被监控的目录中
4. 查看终端是否有错误信息

### Q: 重载太频繁怎么办？

**A:** 当前设置了 1 秒的防抖延迟。如果需要调整，修改 `backend/app_dev.py` 中的：

```python
self.debounce_seconds = 1  # 增加这个值
```

### Q: 能同时调试多个文件吗？

**A:** 可以！热重载模式支持：

- 设置多个断点
- 同时调试多个文件
- 修改任意文件都会触发重载

### Q: 前端也支持热重载吗？

**A:** 是的！Vite 开发服务器自带热模块替换（HMR）功能，修改前端代码会立即在浏览器中更新，无需刷新页面。

## 性能优化

### 减少监控范围

如果项目很大，可以编辑 `backend/app_dev.py`，在跳过的目录列表中添加更多目录：

```python
dirs[:] = [d for d in dirs if d not in [
    'data', 'frontend', 'node_modules', '__pycache__',
    '.git', 'dist', 'docker_build', 'exports', 'uploads',
    'your_large_dir'  # 添加您的目录
]]
```

### 只监控特定文件

修改 `on_modified` 方法来添加更多过滤条件：

```python
def on_modified(self, event):
    # 只监控 handlers.py 和 app.py
    if event.src_path.endswith(('handlers.py', 'app.py')):
        # ...
```

## 相关依赖

- **watchdog** (5.0.3) - 文件系统监控库
- **debugpy** - VSCode Python 调试器（随 Python 扩展自动安装）

## 参考资料

- [Watchdog 文档](https://pythonhosted.org/watchdog/)
- [VSCode Python 调试](https://code.visualstudio.com/docs/python/debugging)
- [debugpy 文档](https://github.com/microsoft/debugpy)

---

**提示：** 如果遇到任何问题，请查看集成终端的输出日志，通常会有详细的错误信息。
