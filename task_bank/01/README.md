# 图片结构化基础（自编训练题）
这不是正式考试题，也不是学校例题的完整复刻。本阶段只练习读取图片及不确定标记，不考 OCR 和真实气象产品分类。

实现 analyze.py 的 analyze_image(path) -> dict。
必须支持 PNG、JPEG、GIF，不限定图片尺寸；GIF 只处理第一帧。
输出字段：file_name(str), format(str), width(int), height(int), product_type(str), observed_text(list), quality_flags(list), first_pixel(list)。
format 使用 Pillow 实际读取的格式。first_pixel 是第一帧左上角像素转换为 RGB 后的三个整数。
本题没有可读的气象语义，product_type 固定为 unknown，observed_text 为 []，quality_flags 至少包含 uncertain_content。
不得根据文件名猜测类别。路径不存在时抛出 FileNotFoundError；图片损坏时抛出 Pillow 的 UnidentifiedImageError。
允许读取与修改 analyze.py；不可修改 README、检查程序或原始素材。
素材：data/ 下是人工生成的色块，用于验证技术操作，不是气象图片。
在工作台点击“运行检查”。也可使用 python ../../checker.py 1 查看练习检查。
