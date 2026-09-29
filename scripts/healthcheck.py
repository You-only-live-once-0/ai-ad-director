"""Read-only local dependency checks; no installations, network or secret output."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

HOME = Path(__file__).resolve().parents[1]
CONFIG = HOME / 'config/project.json'

def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else default

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    for attempt in range(6):
        try:
            temp.replace(path)
            return
        except PermissionError:
            if attempt == 5: raise
            time.sleep(.15 * (attempt + 1))

def discover():
    config = read(CONFIG) or read(HOME / 'config/project.example.json')
    if not config:
        raise FileNotFoundError('config/project.json and project.example.json are missing')
    root = Path(config.get('project_root') or HOME / '__unconfigured_pipeline__')
    if not (root / config['entrypoint']).is_file():
        candidates = []
        for base in config.get('search_roots') or [str(Path.home() / 'Documents' / 'Codex')]:
            if not Path(base).is_dir():
                continue
            for current, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in {'node_modules','.git','.venv','venv','__pycache__'}]
                p = Path(current)
                if p.name == 'ai-ad-pipeline' and 'ad.py' in files and (p / 'director').is_dir() and (p / 'providers/current_video_provider.py').is_file():
                    candidates.append(p)
                    dirs[:] = []
        if len(candidates) != 1:
            raise RuntimeError(f'Pipeline discovery found {len(candidates)} candidates; choose an existing checkout, do not rebuild')
        root = candidates[0]
        config['project_root'] = str(root)
        write(CONFIG, config)
    return config, root

def check(force=False):
    config, root = discover()
    paths = [CONFIG, root/'ad.py', root/'providers/current_video_provider.py', root/'providers/h3_duration_bridge.py', root/'package-lock.json', root.parent.parent/'work/whisperx-venv/Scripts/whisperx.exe']
    skills = ['video-talkcraft','video-shotcraft','story-video-director','reality-world-consistency','visual-video','visual-image','h3-prompt-writing','video-storyboard','analyzing-products','writing-ad-copy','supercmo-setup']
    skillbase = Path.home()/'.codex/skills'
    agentbase = Path.home()/'.agents/skills'
    skillpaths = {s: next((b/s/'SKILL.md' for b in [skillbase,agentbase] if (b/s/'SKILL.md').is_file()), skillbase/s/'SKILL.md') for s in skills}
    spec = importlib.util.spec_from_file_location('existing_provider',root/'providers/current_video_provider.py')
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    env = getattr(provider, 'EXISTING_ENV', root / '__provider_env_unset__')
    vision = Path.home()/'.codex-video-vision/plugin/mcp-server/dist/index.js'
    paths += list(skillpaths.values()) + [env, vision, root/'node_modules/remotion/package.json', root/'director/spatial.py']
    signature = hashlib.sha256(repr([(str(p),p.stat().st_mtime_ns,p.stat().st_size) if p.exists() else (str(p),None) for p in paths] + [sys.executable,shutil.which('node'), bool(os.getenv('PAIPU_API_KEY')),bool(os.getenv('PAIPU_API_BASE_URL'))]).encode()).hexdigest()
    cached = read(HOME/'config/health.json', {})
    if not force and cached.get('signature') == signature:
        return dict(cached, cached=True)
    def version(exe):
        if not exe: return False
        try: return subprocess.run([exe,'--version'],capture_output=True,timeout=15).returncode == 0
        except (OSError,subprocess.TimeoutExpired): return False
    try:
        provider.config()
        paipu = True
    except Exception:
        paipu = False
    checks = {'project_path':root.is_dir(),'ad.py':(root/'ad.py').is_file(),'python':version(config.get('python') or sys.executable), 'python_dependencies':all(importlib.util.find_spec(n) is not None for n in ['requests','PIL']), 'node':version(shutil.which('node')), 'remotion':(root/'node_modules/remotion/package.json').is_file(), 'paipu_configuration':paipu, 'h3_provider':(root/'providers/h3_duration_bridge.py').is_file(), 'whisperx':paths[5].is_file(), 'codex_video_vision_installed':vision.is_file(), 'spatial_engine':(root/'director/spatial.py').is_file(), 'installed_skills':all(p.is_file() for p in skillpaths.values())}
    result = {'passed':all(checks.values()),'checks':checks,'missing_skills':[s for s,p in skillpaths.items() if not p.is_file()], 'project_root':str(root),'signature':signature,'cached':False,'scope':'local availability only; API/model/vision execution and media QA require per-job verification'}
    write(HOME/'config/health.json',result)
    return result

if __name__ == '__main__':
    try:
        result = check('--refresh' in sys.argv)
        print(json.dumps(result,ensure_ascii=False))
        sys.exit(0 if result['passed'] else 1)
    except Exception as exc:
        print(json.dumps({'passed':False,'error':str(exc)},ensure_ascii=False)); sys.exit(1)
