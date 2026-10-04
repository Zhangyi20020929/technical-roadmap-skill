# 技术路线skill

从任务书、PPT、论文或研究方案中提炼逻辑，绘制紧凑的学位论文式技术路线图，并交付可拆分、可编辑的 SVG。

标准技能名称为 `technical-roadmap`，界面显示名称为 **技术路线skill**。核心工作流：源内容核对 → 短节点与分支设计 → 紧凑排版 → 原生 SVG → 渲染和拆分检查。

## 安装与调用

将本仓库的 `technical-roadmap/` 目录复制到 `~/.codex/skills/`。在 Codex 中使用：

> 请使用 $technical-roadmap，根据这份任务书绘制技术路线图，中文宋体、英文和数字 Times New Roman，统一字号，输出可编辑 SVG，并检查取消分组后的文字和形状。

用户指定的内容、颜色、字体和布局优先。自动发现默认启用；原生SVG导出工具无需GitHub凭据或API密钥。

## 文件结构

```text
technical-roadmap/
  SKILL.md
  agents/openai.yaml
  scripts/render_roadmap.py
  scripts/check_svg.py
  references/input-schema.md
  references/validation.md
  assets/example_roadmaps.json
  assets/examples/
```

## 绘图工具

Python 3 和 Pillow 用于字体尺寸测量。先使用现有环境；缺少 Pillow 时可在项目虚拟环境安装 `pip install Pillow`。不安装或分发字体；Windows 可使用系统已有字体，其他系统需要提供合法的字体文件路径。

```sh
python technical-roadmap/scripts/render_roadmap.py technical-roadmap/assets/example_roadmaps.json --output output
python technical-roadmap/scripts/check_svg.py output --report checks.json --ungrouped-dir ungrouped
```

其他系统通过 `--chinese-font` 和 `--latin-font` 指定宋体与 Times New Roman 字体文件。输入结构见 [input-schema.md](technical-roadmap/references/input-schema.md)，渲染与拆分检查见 [validation.md](technical-roadmap/references/validation.md)。

每个文字框保存为一个矩形加一个完整文字对象，多行及中英混排使用 `tspan`。边框、箭头和粗加号为独立矢量对象。字体、颜色、字号和位置显式记录在对象上，取消分组后不依赖父分组样式。

## 示例

三个示例展示多输入、并行试验、模型分析和综合成果。它们是版式参考，不能替代新任务的原始研究内容。

| 材料性能 | 构件设计 | 结构性能 |
|---|---|---|
| ![材料性能路线图](technical-roadmap/assets/examples/material-properties.png) | ![构件设计路线图](technical-roadmap/assets/examples/component-design.png) | ![结构性能路线图](technical-roadmap/assets/examples/structural-performance.png) |
| [可编辑 SVG](technical-roadmap/assets/examples/material-properties.svg) | [可编辑 SVG](technical-roadmap/assets/examples/component-design.svg) | [可编辑 SVG](technical-roadmap/assets/examples/structural-performance.svg) |

已有示例已核对文字和分支，并通过同一渲染器的取消分组差分检查。新产物仍需逐图检查。跨软件导入可能受字体及SVG支持差异影响，尤其Office“转换为形状”与SVG取消分组不是同一操作。

仓库不包含原始任务书、第三方论文PDF、商业字体、账号凭据或电脑上的绝对路径。
