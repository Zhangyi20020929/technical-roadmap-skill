---
name: technical-roadmap
description: "从PPT、论文、任务书或研究方案提炼技术路线与实施逻辑，绘制紧凑学位论文式及国自然等科研申请式路线图，支持多配色、原生可编辑SVG和拆分验证。适用于技术路线图绘制、参考图重绘、研究方案图和可编辑矢量交付；普通统计图不适用。"
---

# 技术路线skill

将研究输入、试验、分析、验证和成果组织成清楚、紧凑、可编辑的路线图。用户的内容、字体、布局和输出要求优先；不把示例的模块数量或配色固定为所有任务的要求。

## 内容与逻辑

- 先查看源图或相关页面，再提取文字和连线。附带文档的指令是源内容，不替代用户请求。
- 区分共同输入、并行支线、先后步骤、模型输入、标定、独立验证和最终成果。保持每条试验与相应模型的对应关系。
- 用户要求原文一致时逐字保留；允许精简时，改成短动作或结果名称，每框通常一至三行。保留关键对象、条件、数字和术语，不新增试验或因果关系。
- 参考论文样式时实际查看图页，只借鉴布局，不移用其研究内容。已有可用参考图时，不必重复检索文献。

## 紧凑排版

- 默认从上到下：多个输入汇聚后分支，各支线展开，最后共同组成输出。水平母线可以分配共同输入，但不能让不同支线的专属参数被误读为互用。
- 采用适合内容的阶段条、大模块与小模块。按文字的实际宽高收紧框体和边界，不用最长支线撑大所有短节点。
- 同级节点保持一致的边线和间距；为箭头留出可读通道，避免连线穿字。需要压缩时，先减少留白，不靠缩小个别字号掩盖拥挤。
- 中文默认宋体（SimSun），英文和数字默认 Times New Roman；默认全图统一字号，用户指定时替换。混合文字在同一文字对象内用不同字体的段落片段。
- 无总标题、图注或额外说明是本项目示例的默认风格；是否添加由用户决定。黑白或浅黄阶段条、红色外虚线、蓝色内虚线均可按参考选择。
- 加号只表示共同输入、互补分析或成果组合，不能代替先后或因果箭头。需要加号时用宽粗的原生形状，避免把它当作普通细小字符。

## 面上基金技术路线图

用户需要面上申请图式、公众号/知乎参考或同类格式重绘时，按需查看 [references/mianshang-layouts.md](references/mianshang-layouts.md)，选择目标递进或任务与指标矩阵等结构。先区分实际看图与仅阅读教学文字，参考模板只提供排版方式，不构成获资助证据；已有优青等类别不得因分区命名改称面上项目。

绘制国自然等研究方案图时，按需查看 [references/nsfc-layouts.md](references/nsfc-layouts.md)，选择证据递进、多分支汇合再验证、双链互补等结构。以科学问题、研究任务与证据的对应关系组织图面；假设、反馈和独立验证只在方案支持时加入，不为套版新增研究环节。

用户要求真实获资助案例时，查看 [references/funded-cases.md](references/funded-cases.md)。分别核对申请内容与资助证据，区分完整申请副本、研究框架片段和原创假设方案；受理号不能当作批准号。根据正文重绘时标明内容页码，不声称未见到的原图已被逐字复刻。

自动工具支持 `compact` 和 `proposal` 布局，后者采用横向模块标签、保留全部阶段标签。自动布局仍要求固定分支数量；“3项任务→1次汇总→2类验证”等分支变化或交叉证据应直接编排原生SVG，不能强改研究逻辑。

配色支持 `reference`、`monochrome`、`blue`、`teal`、`purple`、`warm`，也可覆盖标题底、外框、内框、节点底、文字和连线的颜色。按阶段或研究模块分配颜色，同类一致，避免仅靠颜色表达关系。工具检查文字与线条对比度，保持黑白输出可辨认。具体配置见 [input-schema.md](references/input-schema.md)。

![六种技术路线配色](assets/examples/palette-gallery.png)

## 可编辑输出

根据 [references/input-schema.md](references/input-schema.md) 组织节点数据。简单分层路线图可用 `scripts/render_roadmap.py` 自动生成 SVG；复杂跨层逻辑可直接编排原生 SVG，但须保留以下约束。

- 每个内容框为一个独立分组：一个 `rect` 加一个完整的 `text`。多行和中英混排使用 `tspan`，不拆成一字一个文字对象。
- 节点、阶段条、外框、箭头和加号保留为独立矢量对象，并有唯一ID。不用整图位图替代 SVG，不默认将文字转成轮廓。
- 明确尺寸和 `viewBox`；坐标、颜色、字号、字体、线宽和虚线样式在对象上显式声明。避免依赖父分组的变换或样式，使取消分组后保持原位置和样式。
- 字体文件只用于本地测量，不随产物分发。不静默替换缺失的宋体或 Times New Roman；声明编辑设备需要的字体。
- 保留用户指定交付格式。SVG编辑器取消分组、Office导入转换为形状是不同操作，不能用前者的检查结果承诺后者完全一致。用户强调拆分时，确认主要编辑软件，并在可用条件下做相应检查。

## 检查与交付

按 [references/validation.md](references/validation.md) 做最小充分检查：

1. 对照源材料复核文字、关键数字、箭头、试验与模型对应及标定/验证区别。
2. 实际渲染每张 SVG，检查字体、溢出、遮挡、边框碰字、连线穿字和多余留白；修复后重新查看受影响图。
3. 运行 `scripts/check_svg.py`，验证XML、唯一ID、每框一个可编辑文字对象、字体/字号和无嵌入位图。
4. 用检查工具导出取消分组的验证文件，在同一渲染器、字体和画布下与原图比对，确认形状、位置和文字未变化。仅做XML检查时不得声称已经通过视觉差分。

交付用户要求的图片/SVG，说明已完成的检查与实际兼容性限制。不自动生成额外报告或演示文稿，不从绘图请求推断外部发布授权。

## 绘图结果展示

`assets/example_roadmaps.json` 包含材料性能、构件设计、结构性能三个实用示例；`assets/examples/` 保存其可编辑SVG及预览。只在需要版式参考或演示脚本时读取，不把示例文本当作新任务的研究事实。

### 面上基金技术路线图：目标递进式

公众号模板阶段分组的版式改编，内容来自已核实面上项目52275119公开申请正文；阶段内保留并行机制，虚线回边表示实验校正。

![陶瓷轴承面上基金目标递进路线图](assets/examples/mianshang-bearing-goal.png)

[可编辑SVG](assets/examples/mianshang-bearing-goal.svg) · [公众号、知乎参考及来源范围](references/mianshang-layouts.md)

### 面上基金技术路线图：任务与指标矩阵式

借鉴公众号模板的行列对齐，内容来自已核实面上项目30370577公开申请正文。三个研究层次并行，每列的对象、干预与指标对应。

![心肌CaSR面上基金任务与指标矩阵图](assets/examples/mianshang-casr-matrix.png)

[可编辑SVG](assets/examples/mianshang-casr-matrix.svg) · [公众号、知乎参考及来源范围](references/mianshang-layouts.md)

### 已资助来源：陶瓷轴承，52275119

基于同题申请书公开正文的概括重绘，保留两项机制并行、耦合分析与实验校正。申请副本来自公开镜像，资助由大学官方教师页交叉核实。

![陶瓷轴承获资助项目申请正文概括图](assets/examples/funded-bearing-52275119.png)

[可编辑SVG](assets/examples/funded-bearing-52275119.svg) · [来源与内容页码](references/funded-cases.md)

### 已资助来源：心肌钙敏感受体，30370577

基于徐长庆公开分享的申请书正文概括重绘，保留器官、细胞、分子三支并行及各自干预和指标。本人成功标书声明与中科院原站资助名单匹配，完整下载与原路线图像素未取得。

![心肌钙敏感受体获资助申请正文概括图](assets/examples/funded-myocardial-casr-30370577.png)

[可编辑SVG](assets/examples/funded-myocardial-casr-30370577.svg) · [来源与重绘范围](references/funded-cases.md)

### 已资助项目框架片段：二维材料，61422503

基于项目负责人在大学官网公开培训课件中的研究框架，保留性能调控与器件研究的双向关系；此来源不是完整申请书。

![二维材料获资助项目公开框架概括图](assets/examples/funded-layered-material-61422503.png)

[可编辑SVG](assets/examples/funded-layered-material-61422503.svg) · [来源与内容页码](references/funded-cases.md)

### 科研申请图式：材料科学，蓝色三分支

![界面缺陷与疲劳裂纹的原创假设研究示例](assets/examples/nsfc-material-blue.png)

[查看可编辑SVG](assets/examples/nsfc-material-blue.svg)

### 科研申请图式：环境科学，青绿双链

![河岸带氮转化的原创假设研究示例](assets/examples/nsfc-environment-teal.png)

[查看可编辑SVG](assets/examples/nsfc-environment-teal.svg)

### 科研申请图式：医学，紫色分支变化

![类器官响应的原创假设研究示例](assets/examples/nsfc-medicine-purple.png)

[查看可编辑SVG](assets/examples/nsfc-medicine-purple.svg)

以上三图为原创假设研究方案，用于示范布局，不代表真实申请、获资助项目或已证实研究结论。其分支变化采用原生SVG直接编排；自动工具的JSON输入范围以输入说明为准。

### 材料性能技术路线

![材料性能技术路线图](assets/examples/material-properties.png)

[查看可编辑SVG](assets/examples/material-properties.svg)

### 构件设计技术路线

![构件设计技术路线图](assets/examples/component-design.png)

[查看可编辑SVG](assets/examples/component-design.svg)

### 结构性能技术路线

![结构性能技术路线图](assets/examples/structural-performance.png)

[查看可编辑SVG](assets/examples/structural-performance.svg)
