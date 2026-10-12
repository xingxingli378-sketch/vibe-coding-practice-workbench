# 04 · 气象示意图批量结构化（进阶，建议 45 分钟）
## 场景
多个来源发来 PNG/JPEG/GIF 图片，你需要按图像实际内容分类、读取可见时间，并生成可核验 JSON。文件名可能误导。素材是可重复生成的气象示意卡，不是气象部门真实产品；本题训练读取、可见信息、分类、批处理和不确定性，不声称复刻真实气象 OCR。
## 提供文件
data/ 有雷达、卫星、降水示意卡、含误导文件名的卡、无时间卡、模糊时间卡、未知卡、损坏图和文本文件。
clock_reader.py 是已提供的离线七段数字识别辅助模块；可调用 read_clock(image) -> str|None，读取图片顶部实际像素中的 HH:MM。它不会根据文件名返回答案，不需要安装在线 OCR。不要修改它。
## 交付
只实现 pipeline.py 中 analyze_image(path)、analyze_directory(input_dir)、run(input_dir, output_file)。
analyze_image 返回且仅返回：file_name(str)、format(str)、width(int)、height(int)、product_type(str)、visible_time(str|None)、quality_flags(list[str])。
支持 PNG/JPEG/GIF 和不同尺寸，使用实际格式；GIF 仅首帧。缺失文件抛 FileNotFoundError，损坏文件抛 Pillow 的 UnidentifiedImageError。
### 内容分类规则（本题的可检验定义）
将第一帧转 RGB。只统计图片下部主体区域：y 从 floor(height*0.3) 到底部，x 为全宽。
像素若与目标 RGB 的每个通道差值均 <=35，则属于该目标色。三种类型及色：radar=(30,180,80)，satellite=(70,90,160)，precipitation=(230,100,40)。
每种色的数量除以主体像素总数得到占比。最高占比 >=0.25 且比第二高占比至少高 0.10，才认定该类型；否则 product_type='unknown'，quality_flags 包含 uncertain_type。不按文件名判断。
时间使用辅助模块从首帧实际像素读取。识别失败或不存在时 visible_time=None，quality_flags 包含 uncertain_time，禁止猜测。标记按 uncertain_type、uncertain_time 的顺序排列，没有问题为 []。
### 批量规则
仅扫描 input_dir 第一层文件；扩展名大小写不敏感，只接受 .png/.jpg/.jpeg/.gif，按文件名 Unicode 升序处理。
返回 {'images':[成功结果], 'errors':[{'file_name':名称,'error':'unreadable_image'}]}。损坏图片记入 errors 后继续。忽略子目录和其他文件，不吞掉其他程序错误。不存在的输入目录抛 FileNotFoundError。
run 调用批处理，创建输出父目录，写 UTF-8 JSON（中文可直接阅读），返回同一结果。不得改动输入素材。
## 可手工核验的样例
data/radar_misleading.png 实际为 satellite；data/motion.gif 首帧为 radar（12:30），第二帧为 precipitation（18:45）。
data/no_time.png 类型 precipitation，时间为空；data/broken.png 应记入 errors，其他图片仍成功。
完成后请让 Qwen 调用 run('data','output/report.json')，在文件预览查看结果。若无法运行，检查按钮会在临时目录验证，不会替你生成交付文件。

## 操作与验收
这是依据创智学院公开作答形式自编的进阶练习，不是正式考试题或官方评分标准。
允许让 Qwen 读取本题所有文件；只修改本题实现文件和 output/ 内生成文件。不要改 README、QWEN.md、检查程序、素材或提供的辅助模块。
右侧“运行检查”提供 10 个公开检查点；完成后用“加练边界检查”验证额外情况。这是教学验收，不等于学校的隐藏评分。
先读要求 → 跑一次检查 → 要求助手修改 → 再检查 → 查看实际输出 → 加练边界 → 最后核验。
你不必先理解代码。可先说：“请用普通中文解释我要给程序什么、应得到什么，列出交付清单，先不要修改。”
工具是否能运行命令以实际返回为准；若不能，使用工作台检查按钮。
