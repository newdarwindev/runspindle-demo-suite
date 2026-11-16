"""Build a portable, allowlisted presentation from actual recorded manifests."""
import argparse,hashlib,html,json,os,re,shutil,subprocess,zipfile
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'.json','.webm','.mp4','.png','.jpg','.vtt','.csv'}
def ffmpeg_binary():
 pinned=os.environ.get('DEMO_FFMPEG_PATH')
 if not pinned:return shutil.which('ffmpeg')
 expected=os.environ.get('DEMO_FFMPEG_SHA256','')
 path=Path(pinned)
 if not path.is_absolute() or not path.is_file() or path.is_symlink() or not re.fullmatch(r'[0-9a-f]{64}',expected):
  raise ValueError('Task-local FFmpeg requires an absolute regular path and SHA256 pin')
 if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Task-local FFmpeg SHA256 mismatch')
 if not os.access(path,os.X_OK):raise ValueError('Task-local FFmpeg is not executable')
 return str(path)

def safe_file(base,relative):
 original=base/relative
 if original.is_symlink():raise ValueError('Symlink evidence is not exported')
 p=original.resolve()
 if not p.is_relative_to(base.resolve()) or not p.is_file() or p.is_symlink():raise ValueError('Unsafe or missing evidence path: '+str(relative))
 if any(x in relative.lower() for x in ['storage-state','cookies','credentials','session-state']):raise ValueError('Private browser state cannot be exported')
 return p

def stamp(seconds):
 ms=max(0,round(seconds*1000));return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
def duration(p):
 if not shutil.which('ffprobe'):return None
 r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(p)],capture_output=True,text=True)
 try:return float(r.stdout.strip())
 except ValueError:return None

def validate_links(dest):
 errors=[]
 for page in dest.rglob('*.html'):
  for raw in re.findall(r'(?:href|src|poster)="([^"]+)"',page.read_text()):
   link=html.unescape(raw);u=urlsplit(link)
   if u.scheme or link.startswith('#'):continue
   target=(page.parent/unquote(u.path)).resolve()
   if target.is_dir():target=(target/'index.html').resolve()
   if not target.is_relative_to(dest.resolve()) or not target.is_file():errors.append(str(page.relative_to(dest))+': '+link)
 return errors

def make_reel(dest,entries):
 ffmpeg=ffmpeg_binary()
 if not ffmpeg:return {'status':'unavailable','reason':'ffmpeg not installed'}
 import tempfile
 with tempfile.TemporaryDirectory(prefix='runspindle-reel-') as temp:
  tmp=Path(temp);segments=[]
  for entry in entries:
   if not entry['media']:continue
   label=tmp/'title.txt';label.write_text(entry['case']+' · '+entry['outcome']+'\nFICTIONAL DEMO · CONCEPTUAL INTERFACE')
   title=tmp/f'{len(segments):04}-title.mp4'
   cmd=[ffmpeg,'-v','error','-y','-f','lavfi','-i','color=c=0x102234:s=1280x720:d=2','-vf',f'drawtext=textfile={label}:fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2','-an','-r','25','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',str(title)]
   result=subprocess.run(cmd,capture_output=True)
   if result.returncode:return {'status':'failed','reason':'Title card rendering failed'}
   segments.append(title)
   for media in entry['media']:
    clip=dest/entry['runId']/media['clip'];output=tmp/f'{len(segments):04}-clip.mp4'
    result=subprocess.run([ffmpeg,'-v','error','-y','-i',str(clip),'-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2','-an','-r','25','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',str(output)],capture_output=True)
    if result.returncode:return {'status':'failed','reason':'Actual clip transcoding failed'}
    segments.append(output)
  if not segments:return {'status':'unavailable','reason':'No actual clips available'}
  listing=tmp/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in segments))
  result=subprocess.run([ffmpeg,'-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(dest/'combined-reel.mp4')],capture_output=True)
  if result.returncode:return {'status':'failed','reason':'Clip concatenation failed'}
  # Chromium builds without proprietary H.264 decoding need an open-codec reel.
  result=subprocess.run([ffmpeg,'-v','error','-y','-i',str(dest/'combined-reel.mp4'),'-an','-c:v','libvpx','-deadline','realtime','-cpu-used','8','-b:v','1500k',str(dest/'combined-reel.webm')],capture_output=True)
  if result.returncode:return {'status':'failed','reason':'Portable WebM reel transcoding failed'}
  return {'status':'rendered','portablePath':'combined-reel.webm','portableCodec':'vp8','path':'combined-reel.mp4','durationSeconds':duration(dest/'combined-reel.mp4'),'includes':'Actual clips with case/outcome title cards; individual clips retained.'}

def export_fault_matrix(artifacts,dest,entries):
 source=artifacts/'fault-matrix.json'
 if not source.exists():
  return {'status':'unavailable','reason':'No executed fault matrix was supplied; individual run evidence is retained.'}
 rows=json.loads(safe_file(artifacts,'fault-matrix.json').read_text())
 if not isinstance(rows,list):raise ValueError('Fault matrix must be a list')
 runs={e['runId']:e for e in entries};seen=set();clean=[]
 for row in rows:
  run=row.get('runId');entry=runs.get(run)
  if not entry or entry['case']!=row.get('case') or run in seen:raise ValueError('Fault matrix run identity mismatch')
  manifest=json.loads((dest/run/'manifest.json').read_text())
  if manifest.get('fault')!=row.get('fault'):raise ValueError('Fault matrix fault mismatch')
  for key in ['resumed','verifiedCompletion','expectedBehaviorVerified']:
   if not isinstance(row.get(key),bool):raise ValueError('Fault matrix verdict must be boolean')
  if row['verifiedCompletion']!=(entry['outcome']=='verified'):raise ValueError('Fault matrix outcome mismatch')
  seen.add(run)
  clean.append({key:row[key] for key in ['case','fault','runId','initialOutcome','resumed','verifiedCompletion','expectedBehaviorVerified']})
 (dest/'fault-matrix.json').write_text(json.dumps(clean,indent=2))
 lines=['# Executed fault coverage','Fixture-only observations. Expected blocked/unknown behavior is not business-task completion.','',
 '| Case | Fault | Initial → final | Resumed | Completed | Expected behavior verified | Evidence |',
 '| --- | --- | --- | --- | --- | --- | --- |']
 for r in clean:
  end=runs[r['runId']]['outcome'];values=[r['case'],r['fault'],r['initialOutcome']+' → '+end,str(r['resumed']),str(r['verifiedCompletion']),str(r['expectedBehaviorVerified'])]
  lines.append('| '+' | '.join(str(v).replace('|',r'\|').replace('\n',' ') for v in values)+' | ['+r['runId']+']('+r['runId']+'/manifest.json) |')
 (dest/'fault-matrix.md').write_text('\n'.join(lines)+'\n')
 return {'status':'verified' if clean and all(r['expectedBehaviorVerified'] for r in clean) else 'incomplete','scenarios':len(clean),'json':'fault-matrix.json','table':'fault-matrix.md','rows':clean}

def assemble(root=ROOT,media_tools=True,reel=False):
 ffmpeg=ffmpeg_binary() if media_tools or reel else None
 artifacts=root/'artifacts';dest=artifacts/'presentation-package';dest.mkdir(parents=True,exist_ok=True)
 # Only delete files generated by this assembler, never source run evidence.
 for p in dest.iterdir():
  if p.is_dir():shutil.rmtree(p)
  else:p.unlink()
 entries=[];cards=[];notes=['# Presenter cue sheet','Fictional demo. Conceptual interface. Fixture measurements only.','Timecodes below are **run-relative event times**, not claimed frame-accurate clip offsets. Individual clips remain usable.'];missing=[]
 for mp in sorted(artifacts.glob('*/manifest.json')):
  if mp.parent==dest or mp.parent.name=='package':continue
  m=json.loads(mp.read_text());run=m['runId'];case=m['case']
  if Path(run).name!=run:raise ValueError('Invalid run ID')
  out=dest/run;out.mkdir();cues_path=root/'workflows'/case/'cues.json';cues=json.loads(cues_path.read_text()) if cues_path.exists() else {'headline':'Bakery evaluation: approve a measured change','speakerNotes':'Compare locked versions on the same held-out cases. Fixture operator approves exact revision; activation and rollback are separately visible.'}
  requested=['manifest.json']+m.get('evidence',[])+m.get('media',{}).get('clips',[])+m.get('media',{}).get('screenshots',[])
  for extra in ['events.json','artifact.json','accepted.csv','delivered.csv','comparison.json','evaluation-verification.json']:
   if (mp.parent/extra).is_file():requested.append(extra)
  copied=[];run_missing=[]
  for rel in dict.fromkeys(requested):
   try:
    src=safe_file(mp.parent,rel)
    if src.suffix not in ALLOWED:raise ValueError('Unsupported evidence type')
    target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target);copied.append(rel)
   except ValueError as e:run_missing.append(str(e))
  videos=[]
  for i,clip in enumerate(m.get('media',{}).get('clips',[])):
   if clip not in copied:continue
   seconds=duration(out/clip) if media_tools else None
   caption=f'FICTIONAL DEMO • CONCEPTUAL INTERFACE\n{case} • {run}\n{m.get("outcome","unknown")} • fixture execution only'
   vtt=Path(clip).stem+'.vtt';(out/vtt).write_text('WEBVTT\n\n00:00:00.000 --> '+stamp(seconds or 3600)+'\n'+caption+'\n');poster=None
   if media_tools and ffmpeg:
    poster=f'poster-{i}.jpg';r=subprocess.run([ffmpeg,'-v','error','-y','-ss','0','-i',str(out/clip),'-frames:v','1',str(out/poster)],capture_output=True)
    if r.returncode:poster=None
   if not poster and m.get('media',{}).get('screenshots'):
    poster=next((x for x in m['media']['screenshots'] if x in copied),None)
   videos.append({'clip':clip,'captions':vtt,'poster':poster,'durationSeconds':seconds})
  if not videos:run_missing.append('No actual browser clip available')
  events=json.loads((out/'events.json').read_text()) if (out/'events.json').exists() else []
  notes+=['','## '+cues['headline'],f'Run `{run}` · outcome **{m.get("outcome","unknown")}**',cues.get('speakerNotes','')]
  start=m.get('startedAt',0)
  for ev in events:
   t=ev.get('time',start)
   if isinstance(t,str):
    from datetime import datetime
    try:t=datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
    except ValueError:t=start
   notes.append(f'- {stamp(t-start)}: {ev.get("kind","event")}')
  if not events:notes.append('- Event timing unavailable; no invented timecodes.')
  checks=m.get('checks',{});entry={'runId':run,'case':case,'outcome':m.get('outcome','unknown'),'checks':checks,'media':videos,'missing':run_missing,'metrics':m.get('metrics',{}),'parentCommit':m.get('parentCommit'),'childCommits':m.get('childCommits',{}),'evidence':copied};entries.append(entry);missing.extend([run+': '+x for x in run_missing])
  esc=html.escape
  card=f'<section><h2>{esc(cues["headline"])}</h2><p class="badge">{esc(entry["outcome"])} · {esc(case)}</p><p>{esc(cues.get("speakerNotes",""))}</p><p>Run {esc(run)}</p>'
  for v in videos:
   poster=f' poster="{run}/{esc(v["poster"])}"' if v['poster'] else ''
   card+=f'<video controls preload="metadata"{poster}><source src="{run}/{esc(v["clip"])}"><track kind="captions" label="Fixture labels" srclang="en" src="{run}/{esc(v["captions"])}" default></video>'
  card+='<ul>'+''.join(f'<li>{esc(x)}</li>' for x in run_missing)+'</ul><details><summary>Verification and provenance</summary><pre>'+esc(json.dumps(checks,indent=2))+'</pre><ul>'+''.join(f'<li><a href="{run}/{esc(x)}">{esc(x)}</a></li>' for x in copied if Path(x).suffix=='.json')+'</ul></details></section>';cards.append(card)
 if (root/'docs').exists():shutil.copytree(root/'docs',dest/'docs',dirs_exist_ok=True,ignore=lambda source,names: {'tools'} if Path(source)==root/'docs/portfolio' else set())
 matrix=export_fault_matrix(artifacts,dest,entries)
 reel_result=make_reel(dest,entries) if reel else {'status':'not-requested','reason':'Individual clips retained; use --reel to render combined title-card reel.'}
 (dest/'cue-sheet.md').write_text('\n'.join(notes)+'\n');(dest/'evidence-index.json').write_text(json.dumps({'fixtureOnly':True,'upstreamExecuted':False,'runs':entries,'missing':missing,'reel':reel_result,'faultMatrix':matrix},indent=2))
 (dest/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Runspindle demo suite</title><style>body{font:18px system-ui;max-width:1120px;margin:auto;padding:24px;background:#102234;color:#eef7ff}section{padding:25px;margin:20px 0;background:#203c50;border-radius:15px}a{color:#a1f0d5}video{width:100%;max-width:960px}.badge{color:#a1f0d5}pre{white-space:pre-wrap}</style><header><p class="badge">FICTIONAL DEMO · CONCEPTUAL INTERFACE</p><h1>Teach it a real job. Run it again. Measure the difference.</h1><p>Actual fixture recordings, independent verdicts, and visible limits. Comparative savings remain a hypothesis.</p><nav><a href="cue-sheet.md">Presenter cues</a> · <a href="evidence-index.json">Evidence index</a> · <a href="docs/SOURCES.md">Pinned source references</a></nav></header>'+(('<section><h2>Combined reel</h2><video controls><source src="combined-reel.webm" type="video/webm"><source src="combined-reel.mp4" type="video/mp4"></video><p><a href="combined-reel.webm">WebM reel</a> · <a href="combined-reel.mp4">MP4 reel</a></p></section>') if reel_result['status']=='rendered' else '')+'<section><h2>Executed fault coverage</h2>'+('<p><a href="fault-matrix.md">Coverage table</a> · <a href="fault-matrix.json">Machine-readable matrix</a></p><p>'+str(matrix['scenarios'])+' scenarios · '+matrix['status']+'. Expected safety blocks are not completed jobs.</p>' if 'rows' in matrix else '<p>'+html.escape(matrix['reason'])+'</p>')+'</section>'+''.join(cards)+'</html>')
 errors=validate_links(dest)
 if errors:raise ValueError('Broken package links: '+json.dumps(errors))
 checksums={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()};(dest/'checksums.json').write_text(json.dumps(checksums,indent=2))
 archive=artifacts/'presentation.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in dest.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(dest))
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise ValueError('Archive integrity failure')
  for name,digest in checksums.items():
   if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError('Archive byte mismatch')
 return {'gallery':str(dest/'index.html'),'archive':str(archive),'runs':len(entries),'brokenLinks':errors,'missingMedia':missing,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'reel':reel_result}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--no-media-tools',action='store_true');p.add_argument('--reel',action='store_true');a=p.parse_args();print(json.dumps(assemble(a.root,not a.no_media_tools,a.reel),indent=2))
