# 05 · 多来源观测合并与日统计（进阶，建议 40 分钟）
## 场景与交付
多个 CSV 来源存在空格、华氏温度、重复记录和坏数据。实现 observations.py 的 clean_rows(rows)、load_files(paths)、run(paths, output_dir)，交付 output/cleaned.json、output/summary.json、output/rejected.json。
输入 rows 是字典列表，每条 source(str)、row(int，从2起的 CSV 行号)、station、time、temperature、unit。source/row 是数据来源，不参与有效性判断。输出可追溯拒绝原因。
## 清洗规则（依次判断，第一项失败即拒绝）
1. station 必须字符串，strip 后非空，否则 reason='invalid_station'。
2. time 必须字符串，strip 后严格符合 YYYY-MM-DD HH:MM，且日期时间存在，否则 invalid_time；本题均为北京时间，不做时区推测。
3. temperature 接受 int/float 或数字字符串，不接受 bool/None/空串；转 float 后必须有限，否则 invalid_temperature。
4. unit 必须字符串，strip 后转大写仅 C/F，否则 invalid_unit。
5. F 转 C=(F-32)*5/9；转换后的原始值在 [-80,60]，否则 out_of_range。输出温度 round(C,2)，但范围判断使用未舍入值。
非字典记录按 invalid_station 拒绝，拒绝项 source=None,row=None；字典从 get 读取来源。
相同的 (station,time) 视为重复：保留最后一条有效记录。坏记录不能覆盖好记录。被替换的早期有效记录计入 duplicates，但不计入 rejected。记录顺序按最终保留记录在输入中的位置排列。
clean_rows 返回且仅返回：
{'records':[{'station':去空格站点,'time':去空格时间,'temperature_c':两位温度}],
 'rejected':[{'source':原来源,'row':原行号,'reason':首个失败原因}],
 'duplicates':被替换有效记录数,
 'daily':[{'station':站点,'date':'YYYY-MM-DD','count':记录数,'min_c':最低,'max_c':最高,'mean_c':平均}]}
daily 按 station,date 升序；统计基于 records 中已舍入温度，mean_c 再 round(...,2)。不修改输入。空输入返回空列表和 duplicates=0。
## 文件流程
load_files(paths) 按传入路径顺序读取 UTF-8-SIG CSV（支持 BOM）；第一行表头，必须包含 station,time,temperature,unit，可有额外列。每条增加 source=文件名,row=实际 CSV 记录序号+2，调用 clean_rows 返回结果。
不存在文件抛 FileNotFoundError；缺少必需表头抛 ValueError。不要把这些文件级错误变成某条拒绝记录。
run 创建 output_dir，写 cleaned.json=records、summary.json={'daily':daily,'duplicates':duplicates,'rejected_count':len(rejected)}、rejected.json=rejected，均 UTF-8 JSON，返回完整 clean_rows 结果。不修改原始 CSV。
## 样例核验
按 data/source_a.csv、data/source_b.csv 顺序处理：应最终保留 A(2026-10-01 08:00)=23.00°C、A(09:00)=30.00°C、B(08:00)=0.00°C。重复替换1次，拒绝3条。A 日均26.50°C，B 日均0.00°C。
完成后让 Qwen 运行 run(['data/source_a.csv','data/source_b.csv'],'output')，查看实际文件。

## 操作与验收
这是依据创智学院公开作答形式自编的进阶练习，不是正式考试题或官方评分标准。
允许让 Qwen 读取本题所有文件；只修改本题实现文件和 output/ 内生成文件。不要改 README、QWEN.md、检查程序、素材或提供的辅助模块。
右侧“运行检查”提供 10 个公开检查点；完成后用“加练边界检查”验证额外情况。这是教学验收，不等于学校的隐藏评分。
先读要求 → 跑一次检查 → 要求助手修改 → 再检查 → 查看实际输出 → 加练边界 → 最后核验。
你不必先理解代码。可先说：“请用普通中文解释我要给程序什么、应得到什么，列出交付清单，先不要修改。”
工具是否能运行命令以实际返回为准；若不能，使用工作台检查按钮。
