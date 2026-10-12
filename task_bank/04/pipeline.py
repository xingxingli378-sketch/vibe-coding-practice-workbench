def analyze_image(path):
    raise NotImplementedError('请实现单图读取与分类')

def analyze_directory(input_dir):
    raise NotImplementedError('请实现批量处理')

def run(input_dir, output_file):
    raise NotImplementedError('请实现 JSON 交付')
