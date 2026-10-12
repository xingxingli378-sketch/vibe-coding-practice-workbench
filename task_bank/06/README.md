# 06 · 预报核验与可读报告（综合，建议 35 分钟）
## 场景
按站点和时刻配对预报与实测，评价温度误差和高温事件，并生成给非技术人员看的 HTML 报告。不能把缺失实测当作零。
## 交付与输入
实现 evaluation.py 的 evaluate(forecasts,observations,threshold=35)、run(forecast_path,observation_path,output_dir,threshold=35)。
forecasts/observations 均为字典列表，每条包含 station,time,temperature（数值可为数字字符串）。站点 strip 后非空；time strip 后严格 YYYY-MM-DD HH:MM 且日期存在；温度非 bool、有限且 [-80,60]。忽略无效记录，分别计入 invalid_forecasts/invalid_observations。不修改输入。
同一来源相同 (station,time) 只保留最后一条有效记录。配对用完整 station/time；不能只按站点或输入位置配对。有效的未配对记录分别计入 unmatched_forecasts/unmatched_observations，重复被替换的不计入这些数量。
threshold 必须是非布尔 int/float，有限且在 [-80,60]，不接受字符串；不合法抛 ValueError。
## 输出约定
返回且仅返回以下字段：
matched_count、invalid_forecasts、invalid_observations、unmatched_forecasts、unmatched_observations（整数）；
mae、rmse、bias（误差绝对值平均、均方误差开根号、预报减实测的平均；保留两位，无配对为 None）；
events={'hits':命中,'misses':漏报,'false_alarms':空报,'correct_negatives':正确无事件,'precision':精确率,'recall':召回率}；
details=[{'station':站点,'time':时间,'forecast':预报float,'observed':实测float,'error':round(预报-实测,2)}]，按 station,time 排序。
温度原始值 >= threshold 为事件（包括等于，不先舍入）。hits=两者有事件；misses=实测有而预报无；false_alarms=预报有而实测无；correct_negatives=两者均无。
precision=hits/(hits+false_alarms)，recall=hits/(hits+misses)，保留4位；分母0为 None。误差统计用未舍入差值，不用 details 的舍入误差。
## 文件与报告
run 读取两个 UTF-8 JSON 文件，调用 evaluate。JSON 顶层不是列表抛 ValueError；缺失文件自然抛 FileNotFoundError，损坏 JSON 自然抛 JSONDecodeError。
创建 output_dir，写 UTF-8 report.json=完整返回结果；写 report.html（不能是空页面），包括中文标题“预报核验报告”、配对数、MAE、RMSE、偏差、命中/漏报/空报/正确无事件、精确率、召回率，以及逐条配对表格。None 显示“无数据”，数值指标要与 JSON 一致，不编造结论。站点文本中 <、>、& 等必须正确转义，不能当 HTML 执行。表格顺序与 details 一致。run 返回完整结果。
## 样例核验
data/ 中配对3条：A误差+1，B误差+1，C误差-2。MAE=1.33，RMSE=1.41，bias=0；hits=1,misses=1,false_alarms=1,correct_negatives=0；precision=recall=0.5。预报多出D，实测多出E，两侧未配对各1。
完成后运行 run('data/forecasts.json','data/observations.json','output')，从文件预览核对 JSON 与 HTML。

## 操作与验收
这是依据创智学院公开作答形式自编的进阶练习，不是正式考试题或官方评分标准。
允许让 Qwen 读取本题所有文件；只修改本题实现文件和 output/ 内生成文件。不要改 README、QWEN.md、检查程序、素材或提供的辅助模块。
右侧“运行检查”提供 10 个公开检查点；完成后用“加练边界检查”验证额外情况。这是教学验收，不等于学校的隐藏评分。
先读要求 → 跑一次检查 → 要求助手修改 → 再检查 → 查看实际输出 → 加练边界 → 最后核验。
你不必先理解代码。可先说：“请用普通中文解释我要给程序什么、应得到什么，列出交付清单，先不要修改。”
工具是否能运行命令以实际返回为准；若不能，使用工作台检查按钮。
