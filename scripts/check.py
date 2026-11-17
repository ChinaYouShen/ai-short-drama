#!/usr/bin/env python3
"""一条命令跑完全部检查：自检、样例、招式体检、文档断链。"""
import subprocess,sys,os,glob,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(cmd):
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    out=(p.stdout+p.stderr).strip().splitlines()
    print(f"$ {' '.join(cmd)}")
    print('  '+(out[-1] if out else '(无输出)'))
    return p.returncode
bad=0
bad+=run([sys.executable,'scripts/validate.py','--self-test'])
bad+=run([sys.executable,'scripts/validate.py','samples/storyboard_sample.json'])
bad+=run([sys.executable,'scripts/audit_vfx.py','--quiet'])
links=[]
for f in glob.glob(os.path.join(ROOT,'**','*.md'),recursive=True)+glob.glob(os.path.join(ROOT,'**','*.mdc'),recursive=True):
    for m in re.finditer(r'\]\(([^)]+\.md)',open(f,encoding='utf-8').read()):
        t=os.path.normpath(os.path.join(os.path.dirname(f),m.group(1)))
        if not os.path.exists(t): links.append((os.path.relpath(f,ROOT),m.group(1)))
print(f"$ 文档断链\n  {len(links)} 处")
for l in links[:5]: print('   ',l)
print('\n结果：' + ('全部通过' if bad==0 and not links else '有项目未通过'))
sys.exit(0 if bad==0 and not links else 1)
