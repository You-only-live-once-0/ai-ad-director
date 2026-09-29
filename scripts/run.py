"""Thin CLI dispatcher. All production operations remain in the linked ad.py."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from healthcheck import HOME, check, discover, read, write

def intent(text):
    if any(x in text for x in ['不要生成','先规划','先给我看分镜']): return 'plan',False
    routes = [('status',['做到哪','状态']),('redo',['重做','重生成']),('copy',['只改文案']),('reedit',['只重新剪辑']),('check',['重新检查','检查广告']),('export',['导出']),('resume',['继续']),('generate',['直接生成','正式生成'])]
    action = next((a for a, words in routes if any(w in text for w in words)), 'new')
    paid = any(x in text for x in ['可以生成','直接做','允许AI视频生成','正式生成','直接生成'])
    return action,paid

def snapshot(p, root):
    # Hash planning inputs, references and code; runtime outputs/status are NOT a second queue.
    digest = hashlib.sha256()
    paths = [p/'strategy.json',root/'ad.py'] + list((root/'director').glob('*.py')) + list((root/'providers').glob('*.py')) + list((root/'config').glob('*.json'))
    for folder in ['references','continuity','previs']:
        paths += [f for f in (p/folder).rglob('*') if f.is_file() and (f.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.wav','.mp3'} or 'review' in f.name or 'bible' in f.name)]
    for path in sorted(set(paths)):
        if path.is_file(): digest.update(str(path).encode()); digest.update(path.read_bytes())
    m = read(p/'shots.json',{})
    runtime = {'status','task_id','api_response','idempotency_key','retry_count','output_path','qc','error','transcript','audio_qc','h3'}
    def clean(v):
        if isinstance(v,dict): return {k:clean(x) for k,x in v.items() if k not in runtime}
        if isinstance(v,list): return [clean(x) for x in v]
        return v
    digest.update(json.dumps(clean(m),sort_keys=True,ensure_ascii=False).encode())
    return digest.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action',choices=['new','plan','resume','status','generate','redo','copy','reedit','check','export','interpret'])
    ap.add_argument('--project'); ap.add_argument('--session',default='default'); ap.add_argument('--text',default='')
    ap.add_argument('--request',type=Path,help='Codex-prepared strategy and asset roles; not a second manifest')
    ap.add_argument('--shot'); ap.add_argument('--allow-paid',action='store_true')
    args = ap.parse_args()
    action,paid = intent(args.text) if args.text else (args.action,False)
    if args.action == 'interpret':
        seconds = re.search(r'(\d+)\s*秒',args.text)
        print(json.dumps({'intent':action,'duration':int(seconds[1]) if seconds else 60,'platform':'douyin' if '抖音' in args.text else ('xiaohongshu' if '小红书' in args.text else 'short_video'),'paid_generation':paid},ensure_ascii=False)); return
    health = check(); config,root = discover()
    if not health['passed']: raise RuntimeError('Healthcheck failed; inspect config/health.json')
    sessions = read(HOME/'config/sessions.json',{})
    project = args.project or sessions.get(args.session)
    if args.action == 'new' or (action in {'new','plan'} and not project):
        if not args.request: raise ValueError('Codex must prepare --request from chat product facts and existing materials')
        req = read(args.request)
        strategy = req['strategy']
        slug = re.sub(r'[^a-z0-9-]','-',req.get('product_slug','product').lower()).strip('-') or 'product'
        project = slug + '-' + datetime.now().strftime('%Y%m%d-%H%M%S')
        p = root/'projects'/project
        p.mkdir(parents=True,exist_ok=False)
        strategy = dict(strategy,project=project)
        strategy.setdefault('duration',60); strategy.setdefault('reference_images',[])
        strategy.setdefault('style_bible',{}).setdefault('aspect_ratio','9:16')
        copied = []
        roles = {'product','character','location','voice','reference_ad','logo','brand','product_info'}
        for asset in req.get('assets',[]):
            role = asset['role']
            if role not in roles: raise ValueError('Unknown asset role')
            source = Path(asset['path']).resolve()
            target = p/'references'/role/source.name
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists(): raise ValueError('Asset collision; preserve originals')
            shutil.copy2(source,target)
            copied.append(dict(asset,project_path=str(target.relative_to(p))))
        write(p/'strategy.json',strategy)
        write(p/'logs/skill_assets.json',copied)
        action = 'plan' if action == 'plan' else 'new'
    if not project or not re.fullmatch(r'[\w-]+',project): raise ValueError('Select current project from chat; session/project required')
    p = root/'projects'/project
    if not (p/'strategy.json').is_file(): raise FileNotFoundError(p/'strategy.json')
    sessions[args.session] = project; write(HOME/'config/sessions.json',sessions)
    statepath = p/'logs/ai_ad_director.json'; state = read(statepath,{'stages':{}})
    post_generation = False
    def summary(status,stage):
        m = read(p/'shots.json',{})
        final = p/'output/final.mp4'
        print(json.dumps({'project':project,'status':status,'current_stage':stage,'generated_shots':sum(bool(s.get('output_path')) for s in m.get('shots',[])),'failed_shots':[s['shot_id'] for s in m.get('shots',[]) if 'fail' in s.get('status','')],'next_step':state.get('next_step','Inspect QA evidence if blocked'), 'final_file':str(final) if final.is_file() else None,'state_file':str(statepath)},ensure_ascii=False))
    def call(command, flags=(), cache=False):
        fingerprint = snapshot(p,root)
        old = state['stages'].get(command,{})
        if cache and old.get('success') and old.get('fingerprint') == fingerprint: return
        log = p/'logs'/('skill_'+command+'.log'); log.parent.mkdir(parents=True,exist_ok=True)
        state['current_stage']=command; state['status']='running'; write(statepath,state)
        with log.open('w',encoding='utf-8') as stream:
            result = subprocess.run([config.get('python') or sys.executable,str(root/'ad.py'),command,project,*flags],cwd=root,stdout=stream,stderr=subprocess.STDOUT,env=dict(__import__('os').environ,PYTHONUTF8='1'))
        state['stages'][command]={'success':result.returncode==0,'fingerprint':snapshot(p,root),'log':str(log)}
        state['status']='executed' if not result.returncode else 'failed'; write(statepath,state)
        if result.returncode: raise RuntimeError(f'{command} failed; preserved state: {log}')
    if action == 'status': summary(state.get('status','not_started'),state.get('current_stage','plan')); return
    if action == 'resume' and (p/'output/final.mp4').is_file() and state.get('final_fingerprint') == snapshot(p,root) and all(s['status']=='done' for s in read(p/'shots.json',{}).get('shots',[])):
        summary('complete','render'); return
    if action == 'copy':
        state['next_step']='Codex revise strategy/script and only affected shots in existing shots.json; rerun continuity, refs, previs, lint and preflight; keep unaffected task IDs'
        write(statepath,state); summary('needs_copy_revision','strategy/plan'); return
    if action in {'new','plan','resume','generate','redo'}:
        if not (p/'shots.json').exists(): call('plan')
        for stage in ['continuity','reality','refs','previs','qc-previs','reality-qc','voice-check','h3-lint']:
            call(stage,cache=True)
        call('preflight')
        pre = read(p/'previs/reports/preflight.json',{})
        if pre.get('checks',{}).get('previs3d',{}).get('required'):
            call('previs3d',cache=True); call('preflight'); pre=read(p/'previs/reports/preflight.json',{})
        fingerprint=snapshot(p,root)
        for name,row in state['stages'].items():
            if row.get('success') and name in {'plan','continuity','reality','refs','previs','qc-previs','reality-qc','voice-check','h3-lint','previs3d'}:
                row['fingerprint']=fingerprint
        write(statepath,state)
        if action == 'plan' or not (args.allow_paid or paid):
            state['status']='stopped_before_paid_generation'; state['next_step']='Codex complete missing references/previs and genuine visual reviews; inspect preflight blockers'
            write(statepath,state); summary(state['status'],'preflight'); return
        if not pre.get('paid_ready'):
            state['status']='quality_blocked'; state['next_step']='Repair preflight blockers; no force bypass'
            write(statepath,state); summary('quality_blocked','preflight'); return
        flags=['--allow-paid','--workers','1']
        if args.shot: flags += ['--shot',args.shot]
        if action == 'redo':
            if not args.shot: raise ValueError('Resolve shot from chat before redo')
            m=read(p/'shots.json'); seg=next((g for g in m.get('generation_segments',[]) if args.shot in g['shot_ids']),None)
            target=seg or next((s for s in m['shots'] if s['shot_id']==args.shot),None)
            if target is None: raise ValueError('Unknown shot ID')
            if target.get('status') in {'submission_uncertain','generating','submitted','queued','running'}:
                raise RuntimeError('Existing submission uncertain or active; query/audit it before any redo')
            if seg and len(seg['shot_ids'])>1:
                raise RuntimeError('Shared segment: Codex plan the affected segment or single-shot override in existing manifest; preserve other segment tasks')
            count=state.setdefault('regenerations',{}).get(args.shot,0)
            if count>=2: raise RuntimeError('Two retry submissions reached; stop this shot and report')
            state['regenerations'][args.shot]=count+1; write(statepath,state); flags+=['--regenerate']
        # Existing CLI resumes provider tasks and never blindly resubmits uncertain jobs.
        call('generate',flags)
        post_generation=True
        action='check'
    if action in {'check','reedit','export'}:
        if action=='check':
            for stage in ['reality-qc','qc']: call(stage)
            if not post_generation:
                state['status']='qc_executed_review_reports'; write(statepath,state); summary(state['status'],'qc'); return
            m=read(p/'shots.json')
            if any(s['status'] not in {'approved','editing','done'} for s in m['shots']):
                state['status']='visual_review_required'; write(statepath,state); summary(state['status'],'qc'); return
            for stage in ['transcribe','voice-qc','audio-qc']: call(stage,cache=stage=='transcribe')
            if not read(p/'logs/audio_qc.json',{}).get('passed'): raise RuntimeError('Audio QA failed; repair before edit')
        if action!='export': call('edit')
        call('render')
        state['status']='rendered_requires_final_acceptance'; state['final_fingerprint']=snapshot(p,root); write(statepath,state); summary(state['status'],'render')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'status':'blocked','error':str(exc)},ensure_ascii=False)); sys.exit(1)
