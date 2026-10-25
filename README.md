# 个人介绍与嘉宾海报 Skill

把个人资料、真人照片与已有品牌，整理成一张手机可读的个人介绍海报。交付高清 PNG、可编辑 HTML 和可继续复用的素材。

这套方法来自真实海报制作中的方案确认、照片修复、边距调整、半程回调与版本整理。公开包只保留通用流程和版式，示例头像是矢量示意图，数字与履历均为虚构示例。真实照片、公司标志、个人档案和活动材料不包含在包内。

![示例海报，非真实人物与履历](docs/demo.png)

## 安装与使用

将完整的 [`zhxbai-personal-poster`](zhxbai-personal-poster/) 目录放到支持 Agent Skills 的工具目录；Codex 可放在 `~/.codex/skills/` 下。保留 SKILL.md、scripts、references 和 assets 的相对结构。也可以把本仓库链接发给支持技能安装的 Agent。

```text
使用 $zhxbai-personal-poster，为我的线下分享制作一张 3:4 个人介绍海报。
从我提供的个人材料里核对身份和数字，使用我的照片，沿用现有品牌。
先给文案、照片选择和版式方案，等我确认后出图。
```

已经确认方案时，直接说“按确认方案出图”。可以只调整局部：

```text
布局和文案不变。把照片变得更清晰，人物右侧留出与下方信息卡一致的边距。
```

```text
刚才往左移动得有点多，向右回调上次位移的一半，照片大小不要变。
```

```text
确认这版。删除其他候选，但保留最终 PNG、可编辑 HTML、照片、Logo 和字体，方便下次复用。
```

## 包含什么

- [Skill 入口](zhxbai-personal-poster/SKILL.md)：资料核对、按需确认方案、品牌、人像、微调、检查和交付。
- [可编辑版式](zhxbai-personal-poster/assets/poster.html)与[示例数据](zhxbai-personal-poster/assets/example.json)：默认 3:4 蓝白人物介绍，可按内容和品牌调整。
- [构建与位移脚本](zhxbai-personal-poster/scripts/poster.py)：将本地素材复制到独立输出目录，记录位移并精确回调，保留手工 HTML 修改。
- [浏览器导出](zhxbai-personal-poster/scripts/render_poster.cjs)：导出默认 1800×2400 PNG 与手机预览，检查图片加载、文字溢出和越界。
- [保守清晰化](zhxbai-personal-poster/scripts/enhance_portrait.py)：可选的 Python 轻度锐化，保留原图与透明通道。
- [数据与执行说明](zhxbai-personal-poster/references/data-and-execution.md)、[照片与微调说明](zhxbai-personal-poster/references/portrait-and-adjustments.md)。

## 直接运行示例

进入 Skill 目录：

```sh
python scripts/poster.py build assets/example.json /tmp/poster-demo
node scripts/render_poster.cjs /tmp/poster-demo
python scripts/poster.py move /tmp/poster-demo /tmp/poster-right --dx 40
node scripts/render_poster.cjs /tmp/poster-right
python scripts/poster.py move /tmp/poster-right /tmp/poster-half-back --undo-fraction 0.5
node scripts/render_poster.cjs /tmp/poster-half-back
```

构建与位移仅用 Python 标准库；可选照片处理使用 Pillow，导出使用 Node.js、Playwright 和兼容 Chromium。已经在 Pillow 12.3.0、Playwright 1.62.1 环境验证。依赖路径和浏览器选择见执行说明，模板不会自动安装软件。

## 使用边界

照片清晰化需要核对面容；生成的细节不等于恢复的历史细节。模板不能证明履历、项目规模或培训效果。自动检查也不能替代实际查看海报。每次使用都依据用户本轮授权处理材料，制作海报不代表可以公开上传材料。

默认不生成 ZIP；用户确认前保留必要候选，确认后再清理。最终可编辑文件和仍被引用的素材始终一并保留。
