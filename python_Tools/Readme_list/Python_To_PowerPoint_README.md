# Python_To_PowerPoint.py - 使用说明

## 功能概述

这是一个**通用 Markdown 到 PPT 自动生成工具**，可以根据任意 Markdown 文件内容自动构建专业的幻灯片演示。

### ✨ 核心特性

- ✅ **Markdown 驱动**：从 .md 文件读取内容，自动构建 PPT
- ✅ **智能排版**：一级标题作为幻灯片标题，二级标题作为小节
- ✅ **专业样式**：Teal & Slate 配色方案，深色导航栏，内容卡片设计
- ✅ **灵活输入**：支持命令行参数、交互式输入或默认输出文件名
- ✅ **动态处理**：支持项目符号(- * +)、文本自动转换为幻灯片内容

---

## 快速开始

### 1️⃣ 安装依赖

```bash
pip install python-pptx
```

### 2️⃣ 使用方式

#### 1创建MarkDown文件
话术:

```markdown
功能概述
这是一个通用 Markdown 到 PPT 自动生成工具，可以根据任意 Markdown 文件内容自动构建专业的幻灯片演示。

✨ 核心特性
✅ Markdown 驱动：从 .md 文件读取内容，自动构建 PPT
✅ 智能排版：一级标题作为幻灯片标题，二级标题作为小节
✅ 专业样式：Teal & Slate 配色方案，深色导航栏，内容卡片设计
✅ 灵活输入：支持命令行参数、交互式输入或默认输出文件名
✅ 动态处理：支持项目符号(- * +)、文本自动转换为幻灯片内容


快速开始
1️⃣ 安装依赖
 pip install python-pptx
2️⃣ 使用方式
方式 A：命令行 (完整指定)
 python Python_To_PowerPoint.py input.md output.pptx
方式 B：命令行 (自动生成输出名)
 python Python_To_PowerPoint.py input.md
 # 会自动生成 input.pptx
方式 C：交互式输入
 python Python_To_PowerPoint.py
 # 系统会提示输入文件路径和输出名


Markdown 文件格式说明
📋 标题层级结构
 # 幻灯片标题
 这部分内容包含在标题幻灯片中
 ​
 ## 小节标题 (可选)
 - 项目符号 1
 - 项目符号 2
 ​
 # 第二张幻灯片标题
 ​
 - 直接使用项目符号 (不需要二级标题)
 - 这样格式更简洁
 ​
 ## 分节标题
 - 带有小节的内容
🎯 格式规则
元素作用示例# 标题创建新幻灯片# 研究背景## 小标题幻灯片内的分节## 核心要点- 项目项目符号- 第一个要点* 项目项目符号* 另一个要点+ 项目项目符号+ 还有一个普通文本作为项目符号任意一行文本
⚠️ 特殊约定
第一个一级标题 自动作为标题页
按顺序的一级标题 作为内容幻灯片
最后自动添加 Q&A 页 这个是我捏的一个能用MarkDown驱动的生成PPT的py代码

然后这里提要求:
eg:你给我写一个作业3的PPT,同时你要在里面用()标注要用哪些图,我去从项目的运行界面复制
```



#### 方式 A：命令行 (完整指定_____最推荐的)

```bash
python Python_To_PowerPoint.py input.md output.pptx
```

#### 方式 B：命令行 (自动生成输出名)
```bash
python Python_To_PowerPoint.py input.md
# 会自动生成 input.pptx
```

#### 方式 C：交互式输入
```bash
python Python_To_PowerPoint.py
# 系统会提示输入文件路径和输出名
```

---

## Markdown 文件格式说明

### 📋 标题层级结构

```markdown
# 幻灯片标题
这部分内容包含在标题幻灯片中

## 小节标题 (可选)
- 项目符号 1
- 项目符号 2

# 第二张幻灯片标题

- 直接使用项目符号 (不需要二级标题)
- 这样格式更简洁

## 分节标题
- 带有小节的内容
```

### 🎯 格式规则

| 元素 | 作用 | 示例 |
|-----|------|------|
| `# 标题` | 创建新幻灯片 | `# 研究背景` |
| `## 小标题` | 幻灯片内的分节 | `## 核心要点` |
| `- 项目` | 项目符号 | `- 第一个要点` |
| `* 项目` | 项目符号 | `* 另一个要点` |
| `+ 项目` | 项目符号 | `+ 还有一个` |
| 普通文本 | 作为项目符号 | 任意一行文本 |

### ⚠️ 特殊约定

- **第一个一级标题** 自动作为**标题页**
- **按顺序的一级标题** 作为**内容幻灯片**
- **最后自动添加** Q&A 页

---

## 完整示例

### 输入: `my_presentation.md`

```markdown
# 我的项目汇报

我们的研究项目简介

# 研究背景

## 政策背景
- 国家战略规划要求
- 地方发展需求
- 学术研究价值

## 技术基础
- 先进的 GIS 技术
- 大数据分析能力
- 云端计算支持

# 核心成果

- 完成度: 100%
- 用户认可度: 95%
- 行业应用潜力: 高

# 未来规划

## 短期目标 (2026)
- 完善功能模块
- 增强用户体验

## 长期目标 (2027-2028)
- 扩展应用范围
- 国际推广合作
```

### 输出: `my_presentation.pptx`

生成的 PPT 包含：
1. **标题页** - "我的项目汇报"
2. **Slide 2** - "研究背景" (含 2 个小节)
3. **Slide 3** - "核心成果"
4. **Slide 4** - "未来规划" (含 2 个小节)
5. **Q&A 页** - 自动添加

---

## 常见问题

### Q1: 如何修改 PPT 的配色方案？

编辑 `Python_To_PowerPoint.py` 文件中的配色定义：

```python
COLOR_TEAL = RGBColor(15, 118, 110)      # 修改这个
COLOR_ACCENT = RGBColor(59, 130, 246)    # 或这个
```

### Q2: 可以自定义幻灯片的字体大小吗？

可以。编辑这些函数中的 `Pt()` 参数：

```python
p.font.size = Pt(28)  # 改为你需要的数字
```

### Q3: 生成的 PPT 无法打开怎么办？

检查：
1. Markdown 文件是否是 UTF-8 编码
2. 文件中是否有特殊字符导致解析错误
3. `python-pptx` 库是否正确安装

### Q4: 如何在 PPT 中插入图片？

目前脚本不支持直接插入图片。可以：
1. 生成 PPT 后手动在 PowerPoint 中添加图片
2. 修改脚本添加 `add_picture()` 功能 (高级用法)

---

## 高级用法

### 从 Python 脚本调用

```python
from Python_To_PowerPoint import create_presentation_from_markdown

# 生成 PPT
create_presentation_from_markdown('input.md', 'output.pptx')
```

### 自定义样式

编辑 `create_styled_slide()` 或 `add_content_to_slide()` 函数来自定义外观。

---

## 技术架构

```
Markdown 文件 (.md)
    ↓
MarkdownParser (解析)
    ↓
slides_data (结构化数据)
    ↓
create_styled_slide() (构建幻灯片)
add_content_to_slide()
add_content_with_sections()
    ↓
PPT 文件 (.pptx)
```

---

## 更新日志

### v1.0 (2026-04-14)
- ✅ 核心功能完成
- ✅ 支持 Markdown 解析
- ✅ 专业幻灯片样式
- ✅ 命令行和交互式输入

---

## 许可证

MIT License

---

## 联系方式

作者: Fan Zhen  
最后更新: 2026-04-14

---

祝您使用愉快！ 🎉
