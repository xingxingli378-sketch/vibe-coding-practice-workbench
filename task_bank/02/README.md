# 气象观测数据清洗（自编训练题）
实现 clean.py 中 clean_records(records) -> dict。
输入是字典列表，每条记录包含 station 和 temperature。
station 必须是非空字符串，输出时去掉两端空格。
temperature 可以是数字或数字字符串，转换为 float；必须是有限数且位于 [-80,60]。
布尔值、None、空字符串、非数字、缺失字段、非字典记录为无效数据。
输出：valid（有效记录列表，保留原始顺序，每条仅包含 station 和 temperature），invalid_count（无效记录数量），mean_temperature（有效温度平均值，四舍五入到两位小数；没有有效记录时为 None）。
输入列表及其中的字典不可被修改。
不可修改任务说明或检查程序。点击运行检查验证。
