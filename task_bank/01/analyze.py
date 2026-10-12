from pathlib import Path
from PIL import Image

def analyze_image(path):
    with Image.open(path) as image:
        return {'file_name': Path(path).name, 'format': image.format,
                'width': image.width, 'height': image.height,
                'product_type': 'unknown', 'observed_text': [],
                'quality_flags': [], 'first_pixel': []}
