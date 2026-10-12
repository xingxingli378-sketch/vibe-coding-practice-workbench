import sys,json,copy,math,tempfile,shutil,types
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
TEMP_ROOT=ROOT/'.check-work'
TEMP_ROOT.mkdir(exist_ok=True)
tempfile.tempdir=str(TEMP_ROOT)
sys.dont_write_bytecode=True
n=int(sys.argv[1]); extra='--extra' in sys.argv
d=ROOT/'tasks'/f'{n:02d}'
checks=[]
def check(name,fn):
    try: fn();checks.append({'name':name,'ok':True,'detail':''})
    except Exception as e:checks.append({'name':name,'ok':False,'detail':type(e).__name__+': '+str(e)})
def eq(a,b):
    assert a==b,f'期望 {b!r}，实际 {a!r}'
def raises(fn,t):
    try:fn()
    except t:return
    raise AssertionError('应抛出 '+t.__name__)
def require_keys(r,keys): eq(set(r),set(keys))
def immutable(fn,inputs):
    before=copy.deepcopy(inputs);fn(*inputs);eq(inputs,before)
filename={4:'pipeline.py',5:'observations.py',6:'evaluation.py'}[n]
try:
    sys.path.insert(0,str(d));m=types.ModuleType('answer');m.__file__=str(d/filename)
    exec(compile(Path(m.__file__).read_text(encoding='utf-8'),m.__file__,'exec'),m.__dict__)
except Exception as e:
    print(json.dumps({'passed':0,'total':1,'checks':[{'name':'加载实现文件','ok':False,'detail':str(e)}]},ensure_ascii=False));sys.exit(0)
def row(s='A',t=20,time='2026-10-01 08:00',unit='C',i=2):
    return {'source':'test.csv','row':i,'station':s,'time':time,'temperature':t,'unit':unit}
def obs(s='A',t=20,time='2026-10-01 08:00'):return {'station':s,'temperature':t,'time':time}
def empty_clean():return {'records':[],'rejected':[],'duplicates':0,'daily':[]}

if n==4:
    f=m.analyze_image;batch=m.analyze_directory
    def image(name,fmt,kind,time,size):
        r=f(d/'data'/name)
        for k,v in {'file_name':name,'format':fmt,'width':size[0],'height':size[1],'product_type':kind,'visible_time':time,'quality_flags':[]}.items():eq(r[k],v)
        require_keys(r,['file_name','format','width','height','product_type','visible_time','quality_flags']);json.dumps(r,allow_nan=False)
    def uncertain(name,kind,flags):
        r=f(d/'data'/name);eq(r['product_type'],kind);eq(r['visible_time'],None);eq(r['quality_flags'],flags)
    def batches():
        r=batch(d/'data');require_keys(r,['images','errors'])
        eq([x['file_name'] for x in r['images']],['a.png','faint_time.png','motion.gif','no_time.png','radar_misleading.png','rain.JPG','unknown.png'])
        eq(r['errors'],[{'file_name':'broken.png','error':'unreadable_image'}])
    def output():
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'new/report.json';r=m.run(d/'data',target);eq(json.loads(target.read_text(encoding='utf-8')),r);eq(r,batch(d/'data'))
    def rename():
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'precipitation.png';shutil.copy2(d/'data/radar_misleading.png',p);r=f(p);eq(r['product_type'],'satellite');eq(r['visible_time'],'21:05')
    check('PNG 图像内容分类与时间',lambda:image('a.png','PNG','radar','08:15',(240,160)))
    check('JPEG 与大小写扩展名',lambda:image('rain.JPG','JPEG','precipitation','06:40',(360,240)))
    check('不同尺寸及误导名称',lambda:image('radar_misleading.png','PNG','satellite','21:05',(480,320)))
    check('GIF 首帧而非后续帧',lambda:image('motion.gif','GIF','radar','12:30',(240,160)))
    check('缺失时间不猜测',lambda:uncertain('no_time.png','precipitation',['uncertain_time']))
    check('低清晰度时间标记',lambda:uncertain('faint_time.png','radar',['uncertain_time']))
    check('未知内容的完整标记',lambda:uncertain('unknown.png','unknown',['uncertain_type','uncertain_time']))
    check('批量排序、忽略文本、坏图隔离',batches)
    check('改名不改变识别',rename)
    check('实际 JSON 输出与目录创建',output)
    if extra:
        from PIL import UnidentifiedImageError
        check('单图缺失文件',lambda:raises(lambda:f(d/'data/missing.png'),FileNotFoundError))
        check('损坏图片保留原生异常',lambda:raises(lambda:f(d/'data/broken.png'),UnidentifiedImageError))
        def blank():
            with tempfile.TemporaryDirectory() as t:
                eq(batch(t),{'images':[],'errors':[]});(Path(t)/'nested').mkdir();shutil.copy2(d/'data/a.png',Path(t)/'nested/a.png');eq(batch(t),{'images':[],'errors':[]})
        check('空目录与不递归子目录',blank)
        check('不存在输入目录',lambda:raises(lambda:batch(d/'missing_dir'),FileNotFoundError))
        def ambiguous():
            with tempfile.TemporaryDirectory() as t:
                im=Image.new('RGB',(240,160),'white')
                from PIL import ImageDraw
                draw=ImageDraw.Draw(im);draw.rectangle((0,48,119,159),fill=(30,180,80));draw.rectangle((120,48,239,159),fill=(70,90,160));p=Path(t)/'radar.png';im.save(p)
                eq(f(p)['product_type'],'unknown')
        check('两种类型占比接近不能武断分类',ambiguous)
elif n==5:
    f=m.clean_rows
    def clean(r):return {'station':r['station'].strip(),'time':r['time'].strip(),'temperature_c':round(float(r['temperature']),2)}
    def converted():
        r=f([row(' A ','86',' 2026-10-01 08:00 ',' f ')]);eq(r['records'],[{'station':'A','time':'2026-10-01 08:00','temperature_c':30.0}]);eq(r['rejected'],[])
    def reject():
        inputs=[row(' '),row(time='2026-02-30 08:00'),row(t='nan'),row(unit='K'),row(t=60.001),row(t=True)]
        r=f(inputs);eq(r['records'],[]);eq([x['reason'] for x in r['rejected']],['invalid_station','invalid_time','invalid_temperature','invalid_unit','out_of_range','invalid_temperature'])
        eq([(x['source'],x['row']) for x in r['rejected']],[('test.csv',2)]*6)
    def duplicate():
        r=f([row('A',10),row('B',20),row('A',30),row('A','bad')]);eq(r['records'],[clean(row('B',20)),clean(row('A',30))]);eq(r['duplicates'],1);eq(len(r['rejected']),1)
    def daily():
        r=f([row('B',1),row('A',2),row('A',3,'2026-10-01 09:00'),row('A',9,'2026-10-02 08:00')])
        eq(r['daily'],[{'station':'A','date':'2026-10-01','count':2,'min_c':2.0,'max_c':3.0,'mean_c':2.5},{'station':'A','date':'2026-10-02','count':1,'min_c':9.0,'max_c':9.0,'mean_c':9.0},{'station':'B','date':'2026-10-01','count':1,'min_c':1.0,'max_c':1.0,'mean_c':1.0}])
    def files():
        r=m.load_files([d/'data/source_a.csv',d/'data/source_b.csv']);eq(r['duplicates'],1);eq(len(r['rejected']),3)
        eq(r['records'],[clean(row('A',30,'2026-10-01 09:00')),clean(row('B',0)),clean(row('A',23))])
        eq(r['rejected'],[{'source':'source_a.csv','row':5,'reason':'invalid_station'},{'source':'source_b.csv','row':3,'reason':'invalid_time'},{'source':'source_b.csv','row':4,'reason':'invalid_temperature'}])
    def out():
        with tempfile.TemporaryDirectory() as t:
            r=m.run([d/'data/source_a.csv',d/'data/source_b.csv'],Path(t)/'out');p=Path(t)/'out'
            eq(json.loads((p/'cleaned.json').read_text(encoding='utf-8')),r['records']);eq(json.loads((p/'rejected.json').read_text(encoding='utf-8')),r['rejected']);eq(json.loads((p/'summary.json').read_text(encoding='utf-8')),{'daily':r['daily'],'duplicates':r['duplicates'],'rejected_count':len(r['rejected'])})
    def bounds():eq([x['temperature_c'] for x in f([row('A',-80),row('B',60)])['records']],[-80.0,60.0])
    def schema():require_keys(f([]),['records','rejected','duplicates','daily']);json.dumps(f([row()]),allow_nan=False)
    check('摄氏华氏转换与空格清理',converted)
    check('逐项验证与可追溯拒绝原因',reject)
    check('最后有效记录去重与顺序',duplicate)
    check('按站点日期统计与排序',daily)
    check('多 CSV、BOM、来源行号',files)
    check('保存三个真实交付文件',out)
    check('范围端点保留',bounds)
    check('空输入',lambda:eq(f([]),empty_clean()))
    check('输入不可被修改',lambda:immutable(f,([row(' A ','20')],)))
    check('完整输出结构与 JSON 序列化',schema)
    if extra:
        check('非字典输入的拒绝原因',lambda:eq(f([None])['rejected'],[{'source':None,'row':None,'reason':'invalid_station'}]))
        def invalid_numeric():eq(len(f([row(t=x) for x in (None,'','inf','-inf','bad',10**1000)])['rejected']),6)
        check('非有限值与超大整数',invalid_numeric)
        check('严格时间格式',lambda:eq(f([row(time='2026-1-01 08:00')])['rejected'][0]['reason'],'invalid_time'))
        check('先判断范围再舍入',lambda:eq(f([row(t=60.001)])['rejected'][0]['reason'],'out_of_range'))
        def bad_header():
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'bad.csv';p.write_text('station,temperature\nA,20\n');raises(lambda:m.load_files([p]),ValueError)
        check('文件级表头错误',bad_header)
        check('文件不存在',lambda:raises(lambda:m.load_files([d/'data/missing.csv']),FileNotFoundError))
else:
    f=m.evaluate
    F=[obs('A',36),obs('B',35),obs('C',34),obs('D',20)];O=[obs('A',35),obs('B',34),obs('C',36),obs('E',20)]
    def core():
        r=f(F,O)
        for k,v in {'matched_count':3,'invalid_forecasts':0,'invalid_observations':0,'unmatched_forecasts':1,'unmatched_observations':1,'mae':1.33,'rmse':1.41,'bias':0.0}.items():eq(r[k],v)
    def events():eq(f(F,O)['events'],{'hits':1,'misses':1,'false_alarms':1,'correct_negatives':0,'precision':0.5,'recall':0.5})
    def precise():
        r=f([obs('A',34.999)],[obs('A',35)]);eq(r['events']['misses'],1);eq(r['events']['hits'],0)
    def duplicates():
        r=f([obs(' A ',30),obs('B',40),obs('A',36),obs('A','bad')],[obs('A',35)]);eq(r['matched_count'],1);eq(r['invalid_forecasts'],1);eq(r['unmatched_forecasts'],1);eq(r['details'][0]['forecast'],36.0)
    def pair():
        r=f([obs('A',10),obs('A',20,'2026-10-01 09:00')],[obs('A',12,'2026-10-01 09:00')]);eq(r['matched_count'],1);eq(r['details'][0]['forecast'],20.0)
    def missing():
        r=f([],[]);eq(r['mae'],None);eq(r['rmse'],None);eq(r['bias'],None);eq(r['events']['precision'],None);eq(r['events']['recall'],None)
    def details():eq([(x['station'],x['error']) for x in f(list(reversed(F)),O)['details']],[('A',1.0),('B',1.0),('C',-2.0)])
    def report():
        with tempfile.TemporaryDirectory() as t:
            r=m.run(d/'data/forecasts.json',d/'data/observations.json',Path(t)/'out');p=Path(t)/'out'
            eq(json.loads((p/'report.json').read_text(encoding='utf-8')),r);text=(p/'report.html').read_text(encoding='utf-8')
            for word in ('预报核验报告','MAE','RMSE','1.33','1.41','命中','漏报','空报','精确率','召回率','<table'):assert word in text,'HTML 缺少 '+word
    def invalids():
        r=f([None,obs(' ',20),obs(t=True),obs(time='2026-02-30 08:00')],[]);eq(r['invalid_forecasts'],4);eq(r['matched_count'],0)
    check('配对数量与误差三指标',core)
    check('事件混淆计数及比例',events)
    check('按未舍入温度判断事件',precise)
    check('重复记录及无效记录不覆盖',duplicates)
    check('按完整站点时间键配对',pair)
    check('无配对与零分母不编造数字',missing)
    check('逐条结果排序与误差方向',details)
    check('输入不被修改',lambda:immutable(f,(F,O)))
    check('JSON 与可读 HTML 文件',report)
    check('无效输入计数',invalids)
    if extra:
        def threshold():
            for value in (True,'35',None,float('nan'),float('inf'),10**1000):raises(lambda:f([],[],value),ValueError)
        check('阈值类型、有限性与范围',threshold)
        def strict_time():eq(f([obs(time='2026-1-01 08:00')],[])['invalid_forecasts'],1)
        check('时间必须严格格式',strict_time)
        def numerics():eq(f([obs(t=x) for x in ('nan','inf',10**1000,'',None)],[])['invalid_forecasts'],5)
        check('特殊数值不崩溃',numerics)
        def escaping():
            with tempfile.TemporaryDirectory() as t:
                p=Path(t);a=p/'f.json';b=p/'o.json';a.write_text(json.dumps([obs('<script>&',36)]));b.write_text(json.dumps([obs('<script>&',35)]));m.run(a,b,p/'out');h=(p/'out/report.html').read_text(encoding='utf-8');assert '&lt;script&gt;&amp;' in h;assert '<script>&' not in h
        check('HTML 正确转义站点文本',escaping)
        def top():
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'bad.json';p.write_text('{}');raises(lambda:m.run(p,d/'data/observations.json',Path(t)/'out'),ValueError)
        check('文件顶层结构错误',top)
        check('完整返回字段',lambda:require_keys(f([],[]),['matched_count','invalid_forecasts','invalid_observations','unmatched_forecasts','unmatched_observations','mae','rmse','bias','events','details']))
print(json.dumps({'passed':sum(c['ok'] for c in checks),'total':len(checks),'suite':'extra' if extra else 'public','checks':checks},ensure_ascii=False))
