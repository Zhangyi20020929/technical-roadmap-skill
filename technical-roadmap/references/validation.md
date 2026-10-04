# SVG 检查与拆分验证

## 结构检查

```sh
python scripts/check_svg.py output --report checks.json --ungrouped-dir ungrouped
```

`check_svg.py` 使用 Python 标准库，支持单个SVG或只包含本次交付文件的目录。每个内容框要求一个 `g[data-object-type="text-box"]`，其中一个矩形和一个完整 `text`；换行或中英混排仍属于同一文字对象。字体和样式必须在对象上显式声明。检测失败时返回非零退出码。

导出的取消分组验证文件保留原始画布和绘制顺序。它们用于检查，不自动作为额外交付给用户。

## 实际渲染

选择当前环境已提供的 SVG 渲染工具，如浏览器、Inkscape 或已安装的 Sharp。渲染前确认宋体和 Times New Roman 可用；字体被替换时，不能把该预览视为字体验证通过。不要为此安装系统字体或把商业字体上传到公开仓库。

PNG预览合成到白底，避免透明背景在深色查看器中使黑色连线难以辨认；拆分前后的比对使用相同背景。

例如在已安装 Inkscape 的环境：

```sh
inkscape output/diagram.svg --export-type=png --export-filename=before.png
inkscape ungrouped/diagram.svg --export-type=png --export-filename=after.png
python scripts/check_svg.py --compare before.png after.png
```

相同画布、渲染器和字体的取消分组渲染应一致。若存在差异，检查遗漏、重复、样式继承、变换和字体替换；对差异原因给出证据后再判断，不能自动把所有差异归为抗锯齿。

## 人工图面与语义检查

- 文字与源材料/经用户同意的精简版本一致，尤其数字和模型术语。
- 标定与独立验证、模型输入与模型输出没有混淆。
- 箭头连接正确分支，并在节点边界终止，未穿过文字。
- 所有文字统一字号（用户另有要求除外），中英文使用所需字体。
- 框线、箭头头部和加号未遮挡文字，也未被画布裁切。
- 每框一个文字对象，取消分组后仍可作为整段修改。

## 编辑软件边界

原生SVG保存可编辑文本和矢量形状。编辑设备仍需安装对应字体。SVG编辑器取消分组测试，不能证明PowerPoint/WPS“转换为形状”的处理一定相同；后者可能把文字转成轮廓或改变对象组织。若用户使用Office，检查实际转换结果；需要原生文字框时，根据用户授权生成原生PPTX，保留SVG交付，不无声替换格式。
