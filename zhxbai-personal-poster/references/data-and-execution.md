# 数据与执行

## 数据

`assets/example.json` 可直接运行，只有示意头像和虚构示例信息。正式任务替换内容和素材。支持字段：

| 字段 | 作用 |
| --- | --- |
| `name`、`identity` | 姓名和主身份，必填 |
| `roles` | 最多两行专业身份 |
| `statement` | 最多三行主张，第一行深墨、后续品牌色 |
| `stats` | 最多三项 `{value, label}`，不存在就不补造 |
| `credentials` | 最多三条，第一条突出 |
| `event` | 可选的本次分享文字 |
| `brand_label` | 无 Logo 时显示的品牌文字，可为空 |
| `kicker` | 角标，默认“主讲嘉宾” |
| `portrait` | 必填，本地照片路径；示例 SVG 仅用于演示 |
| `logo`、`font` | 可选本地 Logo、字体路径 |
| `colors` | `blue/ink/pale/muted`，六位十六进制颜色 |
| `portrait_box` | `x/y/width/height`，1080×1440 设计坐标 |

模板有意限制内容量；长姓名、冗长资历或不同结构需要按实际内容调整 HTML，不通过缩小所有文字挤进模板。字段内容做 HTML 转义，不作为代码执行。网络素材先通过当前宿主允许的方式取得授权文件，脚本只接受本地输入，不自动下载。

## 最小运行

在 Skill 目录运行：

```sh
python scripts/poster.py build assets/example.json /tmp/poster-demo
node scripts/render_poster.cjs /tmp/poster-demo
python scripts/poster.py move /tmp/poster-demo /tmp/poster-right --dx 40
node scripts/render_poster.cjs /tmp/poster-right
python scripts/poster.py move /tmp/poster-right /tmp/poster-half-back --undo-fraction 0.5
node scripts/render_poster.cjs /tmp/poster-half-back
```

`build`、`move` 的目标目录必须不存在，避免覆盖已确认成品。`move` 不复制旧 PNG，须重新渲染；同一目录中最新渲染覆盖的是当前源文件的导出。

Python 构建与微调只使用标准库。照片锐化依赖 Pillow；PNG 导出依赖 Node.js、Playwright 和兼容 Chromium。已验证版本为 Pillow 12.3.0、Playwright 1.62.1。使用这些库是为了成熟的像素处理和真实浏览器排版，无需另引入画布或排版引擎。不要为了使用模板去安装全部 Office 依赖。

渲染器优先使用 `require('playwright')`；可用 `NODE_PATH` 指向宿主现有包目录。浏览器有两种选择：Playwright 自带 Chromium，或设置 `PLAYWRIGHT_CHROMIUM_EXECUTABLE` 为当前机器已有的兼容 Chromium 可执行文件。缺失时明确报错，不静默跳过渲染或擅自安装软件。

```sh
NODE_PATH=/path/to/node_modules \
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chromium \
node scripts/render_poster.cjs /tmp/poster-demo
```

默认导出 1800×2400。可传 `--width 2160` 导出等比尺寸；宽度必须为 3 的倍数。照片允许局部 CSS 渐变，照片资产本身不因布局变化被重新编码。

输出目录包含自足的素材副本，整体移动时保持目录结构。`poster_state.json` 仅记录本次使用的显示内容、相对素材路径、照片坐标和移动历史；不要把未使用的个人档案或本机绝对路径写进去。状态文件仍属于用户本地资料，不自动公开。
