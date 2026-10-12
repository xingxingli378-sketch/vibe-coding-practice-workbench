from pathlib import Path
import re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
script=re.search(r'<script>(.*?)</script>',(ROOT/'index.html').read_text(encoding='utf-8'),re.S).group(1)
folder=ROOT/'.check-work';folder.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=folder) as tmp:
    p=Path(tmp)/'ui.js';p.write_text(script,encoding='utf-8')
    subprocess.run(['node','--check',str(p)],check=True)
print('Inline UI JavaScript syntax valid.')
