import unittest,json,io,tempfile,shutil,sys,subprocess,time,copy,types
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server,prepare

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        scratch=ROOT/'.check-work';scratch.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.root=Path(self.temp.name)
        self.saved={k:getattr(server,k) for k in ('ROOT','TASKS','STATE_FILE','STATE','JOBS')}
        server.ROOT=self.root;server.TASKS=self.root/'tasks';server.STATE_FILE=self.root/'practice-state.json'
        server.STATE={'started':None,'mode':'practice','tasks':{}};server.JOBS={}
        for n in range(1,7):
            shutil.copytree(ROOT/'task_bank'/f'{n:02d}',server.TASKS/f'{n:02d}')
        for name in ('checker.py','advanced_checker.py','index.html'):shutil.copy2(ROOT/name,self.root/name)
    def tearDown(self):
        for k,v in self.saved.items():setattr(server,k,v)
        self.temp.cleanup()
    def request(self,path,method='GET',body=None,authorized=True):
        h=server.Handler.__new__(server.Handler);h.path=path
        content=json.dumps(body or {}).encode();h.rfile=io.BytesIO(content)
        h.headers={'Content-Length':str(len(content))}
        if authorized:h.headers['X-Practice-Token']=server.TOKEN
        responses=[]
        h.send=lambda value,status=200,mime='application/json; charset=utf-8':responses.append((status,value,mime))
        getattr(h,'do_'+method)();return responses[0]
    def test_all_six_tasks_and_path_scope(self):
        self.assertEqual(len(server.TITLES),6)
        for n in range(1,7):self.assertTrue(server.task(n).is_dir())
        for n in (0,7,-1):
            with self.assertRaises(ValueError):server.task(n)
        status,files,_=self.request('/api/files?task=4');self.assertEqual(status,200);self.assertIn('pipeline.py',files)
        self.assertEqual(self.request('/api/file?task=4&path=../../../server.py')[0],400)
    def test_token_is_required(self):
        self.assertEqual(self.request('/api/state',authorized=False)[0],403)
        self.assertEqual(self.request('/api/chat','POST',{'task':1,'prompt':'hello'},False)[0],403)
        self.assertEqual(self.request('/api/state')[0],200)
    def test_prepare_never_overwrites_learner_work(self):
        with patch.object(prepare,'ROOT',self.root):
            shutil.copytree(ROOT/'task_bank',self.root/'task_bank')
            target=server.TASKS/'01/analyze.py';target.write_text('learner work',encoding='utf-8')
            self.assertEqual(prepare.prepare(),0);self.assertEqual(target.read_text(),'learner work')
            missing=server.TASKS/'06/evaluation.py';missing.unlink()
            self.assertEqual(prepare.prepare(),1);self.assertTrue(missing.exists())
    def test_initial_check_baselines_are_real(self):
        for n,expected in ((1,8),(2,7),(3,2),(4,0),(5,0),(6,0)):
            script='advanced_checker.py' if n>=4 else 'checker.py'
            result=subprocess.run([sys.executable,str(self.root/script),str(n)],capture_output=True,encoding='utf-8',check=True)
            report=json.loads(result.stdout);self.assertEqual(report['total'],10);self.assertEqual(report['passed'],expected)
    def test_extra_checks_use_additional_cases(self):
        for n,total in ((4,15),(5,16),(6,16)):
            result=subprocess.run([sys.executable,str(self.root/'advanced_checker.py'),str(n),'--extra'],capture_output=True,encoding='utf-8',check=True)
            report=json.loads(result.stdout);self.assertEqual(report['total'],total);self.assertEqual(report['suite'],'extra')
    def test_clear_keeps_learner_files_and_check(self):
        server.STATE['tasks']['1']={'history':[{'text':'test'}],'session':'old','check':{'passed':8}}
        target=server.TASKS/'01/analyze.py';before=target.read_bytes()
        self.assertEqual(self.request('/api/clear','POST',{'task':1})[0],200)
        self.assertEqual(server.STATE['tasks']['1']['history'],[])
        self.assertEqual(server.STATE['tasks']['1']['check'],{'passed':8})
        self.assertEqual(target.read_bytes(),before)
    def test_exam_deadline_and_switching(self):
        self.request('/api/mode','POST',{'mode':'exam'});started=server.STATE['started']
        self.request('/api/state');self.assertEqual(server.STATE['started'],started)
        server.STATE['started']=time.time()-7201;self.assertTrue(server.expired())
        with self.assertRaises(ValueError):server.run_job(1,'check')
        self.request('/api/mode','POST',{'mode':'practice'});self.assertFalse(server.expired())
    def test_local_cli_is_portable(self):
        package=self.root/'node_modules/@qwen-code/qwen-code';package.mkdir(parents=True)
        (package/'package.json').write_text(json.dumps({'bin':{'qwen':'cli-entry.js'}}))
        with patch.object(server.shutil,'which',side_effect=lambda name:'node.exe' if name=='node' else None):
            self.assertEqual(server.cli(),['node.exe',str(package/'cli-entry.js')])
    def test_final_result_releases_job_even_if_cli_lingers(self):
        events=[{'type':'system','session_id':'new-session'},{'type':'assistant','message':{'content':[{'type':'text','text':'Completed'}]}},{'type':'result','is_error':False}]
        class FakeProcess:
            def __init__(self):self.stdout=io.StringIO('\n'.join(json.dumps(e) for e in events));self.calls=0;self.terminated=False
            def wait(self,timeout=None):
                self.calls+=1
                if self.calls==1:raise subprocess.TimeoutExpired('fake',timeout)
                return -15
            def terminate(self):self.terminated=True
            def kill(self):self.terminated=True
        p=FakeProcess()
        with patch.object(server,'cli',return_value=['qwen']),patch.object(server.subprocess,'Popen',return_value=p):
            server.run_job(1,'chat','Only inspect files')
            deadline=time.time()+5
            while server.JOBS[1]['running'] and time.time()<deadline:time.sleep(.01)
            self.assertFalse(server.JOBS[1]['running']);self.assertTrue(p.terminated)
            self.assertIsNone(server.JOBS[1]['error']);self.assertEqual(server.STATE['tasks']['1']['session'],'new-session')
            self.assertIn('Completed',server.STATE['tasks']['1']['history'][-1]['text'])
    def test_checks_run_without_qwen_account(self):
        with patch.object(server,'cli',return_value=None):
            server.run_job(4,'check')
            deadline=time.time()+10
            while server.JOBS[4]['running'] and time.time()<deadline:time.sleep(.02)
            self.assertFalse(server.JOBS[4]['running']);self.assertIsNone(server.JOBS[4]['error'])
            self.assertEqual(server.STATE['tasks']['4']['check']['total'],10)

if __name__=='__main__':unittest.main()
