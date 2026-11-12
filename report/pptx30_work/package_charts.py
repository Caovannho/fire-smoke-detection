"""Use the bundled workbook adapter with exclusive-copy publication on Windows."""
import os,sys,runpy,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[2]
original_link=os.link
def exclusive_link(source,destination,*args,**kwargs):
 try:return original_link(source,destination,*args,**kwargs)
 except PermissionError:
  with open(source,'rb') as src,open(destination,'xb') as dst:shutil.copyfileobj(src,dst)
os.link=exclusive_link
helper=Path('C:/Users/PC/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations/container_tools/materialize_literal_chart_workbooks.py')
sys.path.insert(0,str(helper.parent))
work=root/'report/pptx30_work'
sys.argv=[str(helper),str(work/'candidate.pptx'),str(work/'candidate_with_workbooks.pptx'),'--workspace',str(root),'--receipt',str(work/'workbook_snapshot.json')]
runpy.run_path(str(helper),run_name='__main__')
