import json, os, sys, time, threading, subprocess, secrets, mimetypes, shutil
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / 'tasks'
TOKEN = secrets.token_urlsafe(24)
LOCK = threading.Lock()
STATE_FILE = ROOT / 'practice-state.json'
try:
    STATE = json.loads(STATE_FILE.read_text(encoding='utf-8'))
except (OSError, ValueError):
    STATE = {'started': None, 'mode': 'practice', 'tasks': {}}
JOBS = {}
TITLES = ['图片结构化基础', '气象观测数据清洗', '实训成绩汇总', '气象示意图批量结构化', '多来源观测合并与日统计', '预报核验与可读报告']

def save():
    temp = STATE_FILE.with_suffix('.tmp')
    temp.write_text(json.dumps(STATE, ensure_ascii=False), encoding='utf-8')
    temp.replace(STATE_FILE)

def task(n):
    if n not in range(1, 7): raise ValueError('题号无效')
    return TASKS / ('%02d' % n)

def expired():
    return STATE['mode'] == 'exam' and STATE['started'] and time.time() >= STATE['started'] + 7200

def cli():
    node = shutil.which('node')
    package = ROOT / 'node_modules/@qwen-code/qwen-code'
    if node and (package / 'package.json').exists():
        info = json.loads((package / 'package.json').read_text(encoding='utf-8'))
        binary = info['bin']
        if isinstance(binary, dict): binary = binary.get('qwen', next(iter(binary.values())))
        return [node, str(package / binary)]
    found = shutil.which('qwen')
    return [found] if found and not found.lower().endswith(('.cmd','.bat','.ps1')) else None

def settings_env():
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    system_proxy = urllib.request.getproxies().get('https')
    if system_proxy:
        env.setdefault('HTTPS_PROXY', system_proxy)
        env.setdefault('HTTP_PROXY', system_proxy)
        env.setdefault('NODE_USE_ENV_PROXY', '1')
    # Private per-launch settings; no keys are accepted by this web server.
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH','')
    return env

def run_job(n, kind, prompt='', extra=False):
    directory = task(n)
    with LOCK:
        if expired(): raise ValueError('模拟考试时间已到。可切回练习模式继续学习。')
        if n in JOBS and JOBS[n]['running']: raise ValueError('本题正在运行，请等待完成')
        if kind == 'chat' and not cli(): raise ValueError('Qwen Code 尚未安装，请先完成助手安装。')
        job = {'running': True, 'events': [], 'kind': kind, 'error': None}
        JOBS[n] = job
        item = STATE['tasks'].setdefault(str(n), {'history': [], 'session': None, 'check': None})
        if kind == 'chat': item['history'].append({'role':'user','text':prompt})
        save()
    def worker():
        try:
            if kind == 'check':
                command = [sys.executable, str(ROOT / ('advanced_checker.py' if n >= 4 else 'checker.py')), str(n)]
                if extra and n >= 4: command.append('--extra')
                result = subprocess.run(command, cwd=str(directory), env=settings_env(), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
                try: report = json.loads(result.stdout)
                except ValueError: raise RuntimeError(result.stderr or result.stdout or '检查未返回有效结果')
                with LOCK:
                    item['check'] = report
                    job['events'].append({'type':'check', 'report':report})
                    save()
            else:
                cmd = cli() + ['-p', prompt, '--output-format', 'stream-json', '--approval-mode', 'auto-edit']
                if item.get('session'): cmd += ['--resume', item['session']]
                # auto-edit permits project edits; unapproved shell actions may be denied.
                process = subprocess.Popen(cmd, cwd=str(directory), env=settings_env(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
                job['process'] = process
                job['stopped'] = False
                watchdog = threading.Timer(600, process.kill)
                watchdog.start()
                text_parts = []
                candidate_session = None
                final_result = False
                missing_session = False
                try:
                    for line in process.stdout:
                        try: event = json.loads(line)
                        except ValueError: event = {'type':'log', 'text':line.rstrip()}
                        with LOCK:
                            job['events'].append(event)
                            if len(job['events']) > 3000: job['events'] = job['events'][-3000:]
                            if event.get('session_id') and event.get('type') in ('system', 'assistant'):
                                candidate_session = event['session_id']
                        if event.get('type') == 'log' and 'No saved session found with ID' in event.get('text', ''):
                            missing_session = True
                        if event.get('type') == 'assistant':
                            for block in event.get('message',{}).get('content',[]):
                                if block.get('type') == 'text': text_parts.append(block.get('text',''))
                        if event.get('type') == 'result':
                            final_result = True
                            if event.get('is_error'):
                                job['error'] = str(event.get('error') or event.get('result') or '助手调用失败')
                            break
                    try:
                        code = process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try: process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill(); process.wait()
                        code = 0 if final_result else 1
                    if code and not job.get('stopped'): job['error'] = job['error'] or 'Qwen Code 退出码 %s；请查看运行记录定位原因（不一定是账号问题）。' % code
                    if missing_session:
                        job['error'] = '旧会话不存在，已清除失效编号。请重新发送这条要求；无需重新配置账号。'
                finally: watchdog.cancel()
                with LOCK:
                    if missing_session:
                        item['session'] = None
                    elif code == 0 and not job['error'] and not job.get('stopped') and candidate_session:
                        item['session'] = candidate_session
                    item['history'].append({'role':'assistant','text':'\n'.join(text_parts) or job['error'] or '已结束，请查看工具运行记录。'})
                    save()
        except Exception as exc:
            job['error'] = str(exc)
        finally:
            job['running'] = False
    threading.Thread(target=worker, daemon=True).start()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, value, status=200, mime='application/json; charset=utf-8'):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8') if mime.startswith('application/json') else value
        self.send_response(status)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        try:
            url = urlparse(self.path); q = parse_qs(url.query)
            if url.path == '/':
                html = (ROOT/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN)
                return self.send(html.encode('utf-8'),mime='text/html; charset=utf-8')
            if self.headers.get('X-Practice-Token') != TOKEN and q.get('token',[''])[0] != TOKEN:
                return self.send({'error':'请刷新本地工作台'},403)
            if url.path == '/api/state':
                with LOCK: return self.send({'state': STATE, 'titles':TITLES, 'cli': bool(cli()), 'expired':bool(expired()), 'now':time.time()})
            n = int(q.get('task',['1'])[0]); directory = task(n)
            if url.path == '/api/files':
                files = [p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and not any(x in p.parts for x in ('__pycache__','.qwen','.git','node_modules'))]
                return self.send(sorted(files))
            if url.path == '/api/file':
                p = (directory / q.get('path',['README.md'])[0]).resolve()
                p.relative_to(directory.resolve())
                if p.stat().st_size > 2_000_000: raise ValueError('文件过大，无法预览')
                if p.suffix.lower() in ('.png','.jpg','.jpeg','.gif'):
                    return self.send(p.read_bytes(),mime=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
                return self.send({'text':p.read_text(encoding='utf-8',errors='replace')})
            if url.path == '/api/job':
                job = JOBS.get(n, {'running':False,'events':[],'error':None})
                return self.send({k:v for k,v in job.items() if k != 'process'})
            self.send({'error':'页面不存在'},404)
        except Exception as exc: self.send({'error':str(exc)},400)
    def do_POST(self):
        try:
            if self.headers.get('X-Practice-Token') != TOKEN: return self.send({'error':'请求未授权'},403)
            length = int(self.headers.get('Content-Length','0'))
            if length > 20000: raise ValueError('输入过长')
            body = json.loads(self.rfile.read(length))
            n = int(body.get('task',1)); task(n)
            if self.path in ('/api/chat','/api/check'):
                prompt = str(body.get('prompt','')).strip()
                if self.path.endswith('chat') and not prompt: raise ValueError('请先输入要求')
                run_job(n, 'chat' if self.path.endswith('chat') else 'check',prompt, bool(body.get('extra',False)))
            elif self.path == '/api/mode':
                with LOCK:
                    mode = body.get('mode')
                    if mode not in ('practice','exam'): raise ValueError('模式无效')
                    STATE['mode'] = mode
                    if mode == 'exam': STATE['started'] = time.time()
                    save()
            elif self.path == '/api/clear':
                with LOCK:
                    if JOBS.get(n,{}).get('running'): raise ValueError('运行时不能清空对话')
                    item = STATE['tasks'].setdefault(str(n),{})
                    item['history'] = []; item['session'] = None
                    JOBS.pop(n,None); save()
            elif self.path == '/api/stop':
                job = JOBS.get(n,{})
                if job.get('process') and job['running']:
                    job['stopped'] = True
                    job['process'].terminate()
            else: return self.send({'error':'接口不存在'},404)
            self.send({'ok':True})
        except Exception as exc: self.send({'error':str(exc)},400)

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1',8765),Handler)
    print('Local practice: http://127.0.0.1:8765',flush=True)
    if '--open' in sys.argv:
        import webbrowser
        threading.Timer(1,lambda:webbrowser.open('http://127.0.0.1:8765')).start()
    server.serve_forever()
