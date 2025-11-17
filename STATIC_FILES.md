# 静态资源文件说明

本项目已将所有 CDN 资源改为使用本地静态文件，以提高加载速度和离线使用能力。

## 下载静态资源

运行以下命令下载所有必需的静态资源：

```bash
./download_static.sh
```

或者手动下载：

```bash
bash download_static.sh
```

## 目录结构

下载后的静态资源将保存在以下目录结构中：

```
static/
├── bootstrap/
│   ├── bootstrap.min.css
│   └── bootstrap.bundle.min.js
├── js/
│   └── jquery-3.7.1.min.js
├── fontawesome/
│   └── all.min.css
└── codemirror/
    ├── css/
    │   ├── codemirror.min.css
    │   └── monokai.min.css
    ├── js/
    │   └── codemirror.min.js
    └── mode/
        └── yaml/
            └── yaml.min.js
```

## 注意事项

1. **Font Awesome 字体文件**：Font Awesome CSS 引用的字体文件（woff/woff2）需要单独下载。如果需要完全离线使用，请访问 [Font Awesome 官网](https://fontawesome.com/download) 下载完整包，并将字体文件放在 `static/fontawesome/webfonts/` 目录下。

2. **首次运行**：在首次运行 `download_static.sh` 之前，确保网络连接正常，以便下载所有资源。

3. **版本更新**：如果需要更新静态资源版本，请修改 `download_static.sh` 中的版本号，然后重新运行脚本。

## 快速修复图标丢失问题

如果发现图标不显示，可能是字体文件缺失。运行以下命令快速下载字体文件：

```bash
./download_fonts.sh
```

## 验证

下载完成后，启动服务并访问页面，检查浏览器开发者工具的网络面板，确认所有资源都从本地加载（路径应为 `/static/...`）。

如果图标仍然不显示，请检查：
1. `static/fontawesome/webfonts/` 目录下是否有字体文件（.woff2）
2. 浏览器控制台是否有 404 错误
3. CSS 文件中的字体路径是否正确（应为相对路径 `../webfonts/`）

