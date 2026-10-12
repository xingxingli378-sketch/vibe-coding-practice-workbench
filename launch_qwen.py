import subprocess
from server import cli, settings_env, ROOT
from prepare import prepare
if __name__=='__main__':
    prepare(); command=cli()
    if not command:raise SystemExit('Qwen Code not installed. Run npm install in project root.')
    raise SystemExit(subprocess.call(command,cwd=ROOT/'tasks/01',env=settings_env()))
