def clean_rows(rows):
    raise NotImplementedError('请实现清洗、去重与日汇总')

def load_files(paths):
    raise NotImplementedError('请实现多个 CSV 的读取')

def run(paths, output_dir):
    raise NotImplementedError('请实现交付文件')
