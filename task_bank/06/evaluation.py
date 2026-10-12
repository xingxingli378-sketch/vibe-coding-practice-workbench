def evaluate(forecasts, observations, threshold=35):
    raise NotImplementedError('请实现配对与指标')

def run(forecast_path, observation_path, output_dir, threshold=35):
    raise NotImplementedError('请实现 JSON 与 HTML 报告')
