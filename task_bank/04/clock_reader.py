"""固定版式七段数字 OCR；只识别真实图像像素。提供的辅助模块，不可修改。"""
from PIL import Image
DIGITS={'0': 'abcdef', '1': 'bc', '2': 'abdeg', '3': 'abcdg', '4': 'bcfg', '5': 'acdfg', '6': 'acdefg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}
BOXES={'a': (2, 1, 10, 3), 'b': (10, 3, 12, 10), 'c': (10, 12, 12, 19), 'd': (2, 19, 10, 21), 'e': (0, 12, 2, 19), 'f': (0, 3, 2, 10), 'g': (2, 10, 10, 12)}
def read_clock(image):
    im=image.convert('RGB').resize((240,160),Image.Resampling.NEAREST)
    answer=[]
    for x in (20,38,68,86):
        active=''
        for segment, box in BOXES.items():
            a,b,c,d=box
            color=im.getpixel((x+(a+c)//2,8+(b+d)//2))
            if max(color)<100: active+=segment
            elif min(color)>200: pass
            else: return None
        digit=next((k for k,v in DIGITS.items() if set(v)==set(active)),None)
        if digit is None: return None
        answer.append(digit)
    value=''.join(answer[:2])+':'+''.join(answer[2:])
    return value if int(value[:2])<24 and int(value[3:])<60 else None
