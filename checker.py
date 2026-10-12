import sys, json, importlib.util, copy, math
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True
from pathlib import Path
from PIL import Image, UnidentifiedImageError

ROOT=Path(__file__).resolve().parent
n=int(sys.argv[1]); directory=ROOT/'tasks'/('%02d'%n)
checks=[]
def check(name,fn):
    try: fn(); checks.append({'name':name,'ok':True,'detail':''})
    except Exception as e: checks.append({'name':name,'ok':False,'detail':type(e).__name__+': '+str(e)})
def equal(actual,expected):
    assert actual==expected, '期望 %r，实际 %r'%(expected,actual)
def raises(fn,typ):
    try: fn()
    except typ: return
    raise AssertionError('应抛出 '+typ.__name__)
filename={1:'analyze',2:'clean',3:'summary'}[n]
try:
    import types
    module=types.ModuleType('answer')
    module.__file__=str(directory/(filename+'.py'))
    sys.path.insert(0,str(directory))
    exec(compile(Path(module.__file__).read_text(encoding='utf-8'),module.__file__,'exec'),module.__dict__)
except Exception as e:
    print(json.dumps({'passed':0,'total':1,'checks':[{'name':'加载实现文件','ok':False,'detail':str(e)}]},ensure_ascii=False)); sys.exit(0)
if n==1:
    f=module.analyze_image
    def info(name,fmt,size):
        r=f(str(directory/'data'/name)); equal(r['format'],fmt); equal((r['width'],r['height']),size)
    check('PNG 实际格式和尺寸',lambda:info('sample.png','PNG',(80,60)))
    check('JPEG 实际格式和尺寸',lambda:info('sample.jpg','JPEG',(110,75)))
    check('GIF 实际格式和尺寸',lambda:info('motion.gif','GIF',(48,32)))
    def schema():
        r=f(str(directory/'data/sample.png'))
        for k,t in {'file_name':str,'format':str,'width':int,'height':int,'product_type':str,'observed_text':list,'quality_flags':list,'first_pixel':list}.items(): assert isinstance(r.get(k),t),'字段类型错误：'+k
        json.dumps(r)
    check('输出字段和 JSON 可序列化',schema)
    check('保持原始文件名',lambda:equal(f(str(directory/'data/sample.png'))['file_name'],'sample.png'))
    check('GIF 读取首帧 RGB 像素',lambda:equal(f(str(directory/'data/motion.gif'))['first_pixel'],[255,0,0]))
    check('不确定内容标记',lambda:equal('uncertain_content' in f(str(directory/'data/sample.png'))['quality_flags'],True))
    def unknown():
        r=f(str(directory/'data/radar_misleading.png')); equal(r['product_type'],'unknown'); equal(r['observed_text'],[])
    check('不按文件名猜类别或编造文字',unknown)
    check('缺失文件报错',lambda:raises(lambda:f(str(directory/'data/missing.png')),FileNotFoundError))
    check('损坏图片报错',lambda:raises(lambda:f(str(directory/'data/broken.png')),UnidentifiedImageError))
elif n==2:
    f=module.clean_records
    def test(records,valid,invalid,mean): equal(f(records),{'valid':valid,'invalid_count':invalid,'mean_temperature':mean})
    check('数字字符串与站点去空格',lambda:test([{'station':' A ','temperature':'21.5'}],[{'station':'A','temperature':21.5}],0,21.5))
    check('空输入',lambda:test([],[],0,None))
    check('缺失字段',lambda:test([{}, {'station':'A'}],[],2,None))
    check('无效温度',lambda:test([{'station':'A','temperature':x} for x in (None,'','bad',True)],[],4,None))
    check('无效站点及记录',lambda:test([None,{'station':' ','temperature':1},{'station':3,'temperature':1}],[],3,None))
    check('有效边界温度',lambda:test([{'station':'A','temperature':-80},{'station':'B','temperature':60}],[{'station':'A','temperature':-80.0},{'station':'B','temperature':60.0}],0,-10.0))
    check('排除越界',lambda:test([{'station':'A','temperature':-81},{'station':'B','temperature':61}],[],2,None))
    check('排除非有限数',lambda:test([{'station':'A','temperature':x} for x in ('nan','inf','-inf')],[],3,None))
    check('均值和顺序',lambda:test([{'station':'B','temperature':1},{'station':'A','temperature':2},{'station':'C','temperature':2}],[{'station':'B','temperature':1.0},{'station':'A','temperature':2.0},{'station':'C','temperature':2.0}],0,1.67))
    def immutable():
        r=[{'station':' A ','temperature':'1'}]; before=copy.deepcopy(r);f(r);equal(r,before)
    check('不修改输入',immutable)
else:
    f=module.summarize
    def scores(a,b,c): return [{'task':1,'score':a},{'task':2,'score':b},{'task':3,'score':c}]
    check('优秀等级',lambda:equal(f(scores(90,85,80)),{'total':255,'average':85.0,'level':'优秀'}))
    check('通过等级',lambda:equal(f(scores(60,60,60))['level'],'通过'))
    check('不通过等级',lambda:equal(f(scores(59,59,59))['level'],'不通过'))
    check('未舍入均值判级',lambda:equal(f(scores(85,85,84.99))['level'],'通过'))
    check('均值保留两位',lambda:equal(f(scores(1,2,2))['average'],1.67))
    check('不接受重复题号',lambda:raises(lambda:f([{'task':1,'score':80}]*3),ValueError))
    check('必须三题',lambda:raises(lambda:f(scores(1,2,3)[:2]),ValueError))
    def bad():
        for x in (-1,101,float('nan'),float('inf'),True,'90'): raises(lambda:f(scores(x,80,80)),ValueError)
    check('无效分数',bad)
    check('布尔题号',lambda:raises(lambda:f([{'task':True,'score':80},{'task':2,'score':80},{'task':3,'score':80}]),ValueError))
    def immutable():
        r=scores(90,90,90); before=copy.deepcopy(r);f(r);equal(r,before)
    check('不修改输入',immutable)
print(json.dumps({'passed':sum(c['ok'] for c in checks),'total':len(checks),'checks':checks},ensure_ascii=False))
