# 技术路线 SVG 输入格式

绘图工具：`scripts/render_roadmap.py`。依赖 Python 3 和 Pillow；Pillow 只读取、测量字体，输出仍是原生矢量 SVG。

## 最小示例

```json
{
  "style": {"font_size": 22, "color_scheme": "reference"},
  "diagrams": [
    {
      "id": "compact-demo",
      "inputLabel": "共同输入",
      "inputs": ["材料参数", "工程原型"],
      "stages": [
        {
          "label": "试验与结果分析",
          "groups": [
            {"label": "材料试验", "rows": ["拉伸试验", "应力应变"], "chain": true},
            {"label": "构件试验", "rows": ["分级加载", "裂缝与挠度"], "chain": true}
          ]
        },
        {
          "label": "模型与设计方法",
          "groups": [
            {"label": "本构模型", "rows": ["参数识别", "独立验证"], "chain": true},
            {"label": "构件计算", "rows": [["截面平衡", "有限元"], "计算方法"], "chain": true}
          ]
        }
      ],
      "final": "设计参数与适用范围",
      "outputs": ["设计建议", "计算方法"]
    }
  ]
}
```

## 字段

| 位置 | 字段 | 规则 |
| --- | --- | --- |
| 根对象 | `diagrams` | 非空数组，每项生成一份 SVG。 |
| 根对象 | `style` | 可选，支持下面四项设置。 |
| `style` | `font_size` | 整数 10–48，默认 22；全图统一字号，框线、间距也等比例调整。 |
| `style` | `color_scheme` | `reference`、`monochrome`、`blue`、`teal`、`purple`、`warm`，默认 `reference`。 |
| `style` | `colors` | 可选的角色色覆盖对象；只接受下方六个角色的 `#RRGGBB` 值。 |
| `style` | `layout` | `compact`（默认）或 `proposal`；只调整模块标签与边框排布，不改变逻辑连线。 |
| 图 | `id` | 唯一文件名，匹配 `[A-Za-z0-9][A-Za-z0-9_-]*`，不含扩展名。 |
| 图 | `inputLabel` | 共同输入阶段的短标签。 |
| 图 | `inputs` | 非空字符串数组；每项一个独立输入框，框间小加号，汇入各分支。 |
| 图 | `stages` | 非空阶段数组，自上而下排列。 |
| 阶段 | `label` | 阶段标签；`compact` 的最后阶段改用各组横条，不重复阶段总标签；`proposal` 保留所有阶段总标签。 |
| 阶段 | `groups` | 非空分支数组；各阶段必须保持相同分支数量和顺序。 |
| 分支 | `label` | 单行短标签；`compact` 前面阶段为竖向、最后阶段为横向；`proposal` 全部使用横向模块标签。建议 2–8 个汉字。 |
| 分支 | `rows` | 非空数组，按从上到下排列；字符串是一框，字符串数组是同排多框。 |
| 分支 | `chain` | 可选布尔值，默认 `false`。`true` 用箭头按行连接，`false` 将各行作为同组并列要点。 |
| 图 | `final` | 一个共同输出框，接收全部末阶段分支。 |
| 图 | `outputs` | 可选非空字符串数组；共同输出继续向各个成果框分流。 |

文本可用 JSON 的 `\n` 主动换行。工具不自动删字或缩小单个框的字号；框宽随文字测量、整体画布随布局扩展。不要用空行、空字符串或制表符调整位置。

## 配色和研究方案布局

`reference` 保留浅黄条、红蓝虚线；`monochrome` 保留白底黑线。其余四种使用低饱和颜色，正文和连线默认仍是黑色。

| 配色 | 标题底 | 外框 | 内框 |
| --- | --- | --- | --- |
| `blue` | `#E7EEF5` | `#4A6F91` | `#7291AD` |
| `teal` | `#E5F0ED` | `#387A78` | `#5F9390` |
| `purple` | `#EEEAF4` | `#76668F` | `#9484A8` |
| `warm` | `#F4EBDF` | `#9A7051` | `#AD8A6C` |

以下设置适合自上而下的研究内容分块：每阶段保留总标签，各分支也使用横向标签，模块保持紧凑。

```json
"style": {
  "font_size": 22,
  "layout": "proposal",
  "color_scheme": "blue",
  "colors": {
    "title_fill": "#DEEAF2",
    "outer_frame": "#375E7B",
    "inner_frame": "#617D91",
    "node_fill": "#F8FAFC",
    "text": "#172A3A",
    "line": "#31485A"
  }
}
```

`colors` 可以只覆盖其中一项，其余沿用选定配色。六个角色分别为标题底、外框、内框、节点底、文字、连线；`line` 也用于节点实线边框和箭头。小加号沿用内框色，末阶段大加号沿用外框色。整张画布保持白色，SVG 本身没有背景栅格图。

角色色只能是六位十六进制，不接受透明色、渐变、CSS 变量或色名。工具测算对比度：文字对标题底和节点底至少 4.5:1；外框、内框、连线对白底至少 3:1；连线对标题底和节点底也至少 3:1。过浅组合会明确报错，请调整颜色；不会自动改色或改成另一种字体。

两种布局都沿用同样的分支索引关系。`proposal` 不增加任意交叉边、跨层反馈或复杂网络的支持；需要这种研究逻辑时应编辑原生 SVG 的显式连线。

## 逻辑约束

- 同一组索引对应同一条研究分支，例如每个阶段第一组都对应材料研究，第二组都对应构件研究。
- 输入框在阶段外通过共同母线汇总，再分别进入第一阶段各组。共同输入应确实适用于全部分支。
- 不同阶段之间仅连接相同索引的组，避免把某一试验结果错误地分配给另一模型。
- `chain: true` 表示前后处理关系，同一行多个框分别连接到下一行。只有确实可以合并处理时才这样表达。
- 加号用于同排互补内容和最后阶段的并列方法；不能代替因果、选择、反馈或验证箭头。
- 当前工具适合固定并行分支、逐阶段分析、最终汇总的路线。任意交叉边、分支数量变化和反馈回路不在本格式中；需要保留这类关系时，应直接编辑原生 SVG，不要将其强行改成顺序关系。

## 使用

在技能目录中执行：

```sh
python scripts/render_roadmap.py assets/example_roadmaps.json --output output
python scripts/check_svg.py output --report output/inspection.json --ungrouped-dir ungrouped
```

Windows 默认读取系统字体目录里的 `simsun.ttc` 和 `times.ttf`。其他系统或字体不在该位置时，指定合法安装的对应字体文件：

```sh
python scripts/render_roadmap.py input.json --output output --chinese-font /path/to/simsun.ttc --latin-font /path/to/times.ttf
```

工具检查字体族为 SimSun（宋体）和 Times New Roman；缺失或提供错误字体会明确停止，不静默替换。字体文件不会被复制到 SVG 或技能中。

输出为 `<id>.svg`。每个文字框是一组 `rect` 加单个完整 `text`，行和中英文片段采用显式定位的 `tspan`；取消分组后仍是一个文字对象。边框、线、箭头和加号是独立矢量对象。所有对象使用显式坐标、字体和样式，不依赖父组样式或变换，不包含栅格图、`use` 或外部资源。

编辑软件仍需安装上述字体。SVG 中保留文字对象，不将文字转成不可编辑的轮廓。结构检查和取消分组检查可以验证 SVG 自身保持一致；特定软件的导入、转换为形状和再次拆分，还应在该软件中实际检查。
