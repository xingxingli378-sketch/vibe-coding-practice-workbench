"""Private author QA: reference implementations never copied to learner tasks."""
from pathlib import Path
import shutil,subprocess,sys,json
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'work'/'author-qa';QA.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'advanced_checker.py',QA/'advanced_checker.py')
for n in (4,5,6):shutil.copytree(ROOT/'task_bank'/f'{n:02d}',QA/'tasks'/f'{n:02d}',dirs_exist_ok=True)
common=r'''import re,math,json
from pathlib import Path
from datetime import datetime
def time_ok(value):
    if not isinstance(value,str): return False
    value=value.strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}',value):return False
    try:datetime.strptime(value,'%Y-%m-%d %H:%M');return True
    except ValueError:return False
def temp(value):
    if isinstance(value,bool) or not isinstance(value,(int,float,str)):raise ValueError()
    value=float(value)
    if not math.isfinite(value):raise ValueError()
    return value
'''
(QA/'tasks/04/pipeline.py').write_text('''from pathlib import Path
from PIL import Image,UnidentifiedImageError
from clock_reader import read_clock
import json
def analyze_image(path):
    with Image.open(path) as im:
        fmt=im.format;w,h=im.size;rgb=im.convert('RGB');counts=[]
        pixels=list(rgb.crop((0,int(h*.3),w,h)).getdata())
        for kind,color in [('radar',(30,180,80)),('satellite',(70,90,160)),('precipitation',(230,100,40))]:
            counts.append((sum(all(abs(a-b)<=35 for a,b in zip(p,color)) for p in pixels)/len(pixels),kind))
        counts.sort(reverse=True);kind=counts[0][1] if counts[0][0]>=.25 and counts[0][0]-counts[1][0]>=.1 else 'unknown'
        time=read_clock(rgb);flags=[]
        if kind=='unknown':flags.append('uncertain_type')
        if time is None:flags.append('uncertain_time')
        return dict(file_name=Path(path).name,format=fmt,width=w,height=h,product_type=kind,visible_time=time,quality_flags=flags)
def analyze_directory(input_dir):
    p=Path(input_dir)
    if not p.exists():raise FileNotFoundError(p)
    images=[];errors=[]
    for file in sorted(p.iterdir(),key=lambda x:x.name):
        if not file.is_file() or file.suffix.lower() not in ('.png','.jpg','.jpeg','.gif'):continue
        try:images.append(analyze_image(file))
        except UnidentifiedImageError:errors.append(dict(file_name=file.name,error='unreadable_image'))
    return dict(images=images,errors=errors)
def run(input_dir,output_file):
    r=analyze_directory(input_dir);p=Path(output_file);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8');return r
''',encoding='utf-8')
(QA/'tasks/05/observations.py').write_text(common+'''
import csv
def clean_rows(rows):
    kept={};rejected=[];duplicates=0
    for i,r in enumerate(rows):
        reason=None
        if not isinstance(r,dict) or not isinstance(r.get('station'),str) or not r['station'].strip():reason='invalid_station'
        elif not time_ok(r.get('time')):reason='invalid_time'
        else:
            try:t=temp(r.get('temperature'))
            except (ValueError,TypeError,OverflowError):reason='invalid_temperature'
            if reason is None:
                unit=r.get('unit');unit=unit.strip().upper() if isinstance(unit,str) else None
                if unit not in ('C','F'):reason='invalid_unit'
                else:
                    if unit=='F':t=(t-32)*5/9
                    if not -80<=t<=60:reason='out_of_range'
        if reason:
            rejected.append(dict(source=r.get('source') if isinstance(r,dict) else None,row=r.get('row') if isinstance(r,dict) else None,reason=reason));continue
        s=r['station'].strip();tm=r['time'].strip();key=(s,tm)
        if key in kept:duplicates+=1
        kept[key]=(i,dict(station=s,time=tm,temperature_c=round(t,2)))
    records=[v[1] for v in sorted(kept.values())];groups={}
    for r in records:groups.setdefault((r['station'],r['time'][:10]),[]).append(r['temperature_c'])
    daily=[dict(station=s,date=day,count=len(v),min_c=min(v),max_c=max(v),mean_c=round(sum(v)/len(v),2)) for (s,day),v in sorted(groups.items())]
    return dict(records=records,rejected=rejected,duplicates=duplicates,daily=daily)
def load_files(paths):
    rows=[]
    for path in paths:
        with open(path,encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream)
            if not set(('station','time','temperature','unit'))<=set(reader.fieldnames or []):raise ValueError()
            for i,r in enumerate(reader,2):r.update(source=Path(path).name,row=i);rows.append(r)
    return clean_rows(rows)
def run(paths,output_dir):
    r=load_files(paths);p=Path(output_dir);p.mkdir(parents=True,exist_ok=True)
    for name,value in [('cleaned',r['records']),('rejected',r['rejected']),('summary',dict(daily=r['daily'],duplicates=r['duplicates'],rejected_count=len(r['rejected'])))]:
        (p/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    return r
''',encoding='utf-8')
(QA/'tasks/06/evaluation.py').write_text(common+'''
import html
def normalized(rows):
    kept={};invalid=0
    for r in rows:
        try:
            if not isinstance(r,dict) or not isinstance(r.get('station'),str) or not r['station'].strip() or not time_ok(r.get('time')):raise ValueError()
            t=temp(r.get('temperature'))
            if not -80<=t<=60:raise ValueError()
            kept[(r['station'].strip(),r['time'].strip())]=t
        except (ValueError,TypeError,OverflowError):invalid+=1
    return kept,invalid
def evaluate(forecasts,observations,threshold=35):
    if isinstance(threshold,bool) or not isinstance(threshold,(int,float)) or not -80<=threshold<=60 or not math.isfinite(threshold):raise ValueError()
    f,fi=normalized(forecasts);o,oi=normalized(observations);keys=sorted(f.keys()&o.keys());errors=[f[k]-o[k] for k in keys]
    hits=misses=false=correct=0
    for k in keys:
        a=f[k]>=threshold;b=o[k]>=threshold
        if a and b:hits+=1
        elif b:misses+=1
        elif a:false+=1
        else:correct+=1
    return dict(matched_count=len(keys),invalid_forecasts=fi,invalid_observations=oi,unmatched_forecasts=len(f)-len(keys),unmatched_observations=len(o)-len(keys),mae=round(sum(abs(e) for e in errors)/len(errors),2) if errors else None,rmse=round(math.sqrt(sum(e*e for e in errors)/len(errors)),2) if errors else None,bias=round(sum(errors)/len(errors),2) if errors else None,events=dict(hits=hits,misses=misses,false_alarms=false,correct_negatives=correct,precision=round(hits/(hits+false),4) if hits+false else None,recall=round(hits/(hits+misses),4) if hits+misses else None),details=[dict(station=k[0],time=k[1],forecast=f[k],observed=o[k],error=round(f[k]-o[k],2)) for k in keys])
def run(forecast_path,observation_path,output_dir,threshold=35):
    f=json.loads(Path(forecast_path).read_text(encoding='utf-8'));o=json.loads(Path(observation_path).read_text(encoding='utf-8'))
    if not isinstance(f,list) or not isinstance(o,list):raise ValueError()
    r=evaluate(f,o,threshold);p=Path(output_dir);p.mkdir(parents=True,exist_ok=True);(p/'report.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
    display=lambda v:'无数据' if v is None else html.escape(str(v))
    text='<h1>预报核验报告</h1>'+''.join('<p>'+label+': '+display(r[k])+'</p>' for k,label in [('matched_count','配对数'),('mae','MAE'),('rmse','RMSE'),('bias','偏差')])+''.join('<p>'+label+': '+display(r['events'][k])+'</p>' for k,label in [('hits','命中'),('misses','漏报'),('false_alarms','空报'),('correct_negatives','正确无事件'),('precision','精确率'),('recall','召回率')])+'<table>'+''.join('<tr>'+''.join('<td>'+display(v)+'</td>' for v in item.values())+'</tr>' for item in r['details'])+'</table>'
    (p/'report.html').write_text(text,encoding='utf-8');return r
''',encoding='utf-8')
failed=False
for n in (4,5,6):
    for extra in (False,True):
        command=[sys.executable,str(QA/'advanced_checker.py'),str(n)]+(['--extra'] if extra else [])
        result=subprocess.run(command,capture_output=True,encoding='utf-8');r=json.loads(result.stdout)
        print(n,'extra' if extra else 'public',f"{r['passed']}/{r['total']}")
        for c in r['checks']:
            if not c['ok']:print(c);failed=True
if failed:sys.exit(1)
print('题面、素材、检查与参考验证一致；学习者实现仍保持空白。')
