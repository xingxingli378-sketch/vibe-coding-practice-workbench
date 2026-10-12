"""Copy missing starter files. Existing work is never overwritten."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
def prepare():
    source=ROOT/'task_bank';target=ROOT/'tasks';copied=0
    for p in source.rglob('*'):
        if not p.is_file():continue
        dest=target/p.relative_to(source)
        if dest.exists():continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest);copied+=1
    return copied
if __name__=='__main__':print('Practice tasks ready; copied',prepare(),'missing files. Existing work retained.')
