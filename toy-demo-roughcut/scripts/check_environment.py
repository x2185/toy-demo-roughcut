"""Read-only dependency check. No downloads, installation or configuration changes."""
import argparse
import json
import re
import shutil
import subprocess
import sys


def capabilities(text):
    return set(re.findall(r'^\s*[A-Z.]+\s+(\S+)\s+', text, re.MULTILINE))


def inspect_environment():
    checks = []
    def add(name, ok, detail):
        checks.append({'name': name, 'ok': bool(ok), 'detail': detail})
    add('Python 3.10+', sys.version_info >= (3, 10), sys.executable + ' | ' + sys.version.split()[0])
    try:
        from PIL import Image
        add('Pillow', True, getattr(Image, '__version__', 'available'))
    except ImportError:
        add('Pillow', False, 'Install with this Python: -m pip install Pillow')
    encoders, filters = set(), set()
    for tool in ('ffmpeg', 'ffprobe'):
        path = shutil.which(tool)
        try:
            if not path:
                raise FileNotFoundError('Not found on PATH')
            version = subprocess.run([path, '-version'], capture_output=True, text=True, errors='replace', check=True, timeout=20).stdout.splitlines()[0]
            if tool == 'ffmpeg':
                for option in ('encoders', 'filters'):
                    result = subprocess.run([path, '-hide_banner', '-' + option], capture_output=True, text=True, errors='replace', check=True, timeout=20)
                    if option == 'encoders':
                        encoders = capabilities(result.stdout)
                    else:
                        filters = capabilities(result.stdout)
            add(tool, True, path + ' | ' + version)
        except (OSError, subprocess.SubprocessError, IndexError) as exc:
            add(tool, False, str(exc))
    required_encoders = {'libx264', 'aac', 'pcm_s16le'}
    required_filters = {'setpts', 'fps', 'format', 'atrim', 'asetpts', 'atempo', 'apad', 'concat'}
    for name in sorted(required_encoders | {'libx265'}):
        add('encoder:' + name, name in encoders, 'FFmpeg encoder')
    for name in sorted(required_filters | {'zscale', 'tonemap'}):
        add('filter:' + name, name in filters, 'FFmpeg filter')
    common = all(c['ok'] for c in checks if c['name'] in ('Python 3.10+', 'Pillow', 'ffmpeg', 'ffprobe'))
    sdr = common and required_encoders <= encoders and required_filters <= filters
    return {'checks': checks, 'profiles': {
        'sdr': sdr,
        'hdr-to-sdr': sdr and {'zscale', 'tonemap'} <= filters,
        'preserve-hdr': common and {'libx265', 'aac', 'pcm_s16le'} <= encoders and required_filters <= filters,
    }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['all', 'sdr', 'hdr-to-sdr', 'preserve-hdr'], default='all')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = inspect_environment()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for c in report['checks']:
            print(f"{'OK' if c['ok'] else 'MISSING'} {c['name']}: {c['detail']}")
        for name, ok in report['profiles'].items():
            print(f"PROFILE {name}: {'READY' if ok else 'NOT READY'}")
        print('Capability checks do not replace a render test on the actual footage.')
    # all is an inventory: optional HDR features do not block ordinary SDR use.
    return 0 if report['profiles']['sdr' if args.mode == 'all' else args.mode] else 1


if __name__ == '__main__':
    raise SystemExit(main())
