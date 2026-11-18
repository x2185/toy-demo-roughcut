"""Delivery checks with synthetic footage; no private source videos required."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'toy-demo-roughcut' / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render = load('render_edit')
environment = load('check_environment')


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=64x96:rate=30:duration=3',
                        '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', '-c:v', 'libx264', '-c:a', 'aac', str(self.source)], check=True)
        self.target = self.root / 'result.mp4'
        self.plan = self.root / 'plan.json'
        self.plan.write_text(json.dumps({'source': str(self.source), 'output': str(self.target),
            'clips': [{'start': 0, 'end': 1}, {'start': 1.5, 'end': 2.5, 'speed': 2}]}), encoding='utf-8')

    def invoke(self):
        with patch.object(sys, 'argv', ['render_edit.py', str(self.plan)]):
            render.main()

    def assert_no_delivery(self):
        self.assertFalse(self.target.exists())
        self.assertFalse(self.target.with_suffix('.edit.json').exists())
        self.assertFalse(list(self.root.glob('roughcut-*')))

    def test_success_preserves_source_and_delivers_verified_pair(self):
        original = self.source.read_bytes()
        self.invoke()
        record = json.loads(self.target.with_suffix('.edit.json').read_text(encoding='utf-8'))
        self.assertEqual(record['dimensions'], [64, 96])
        self.assertAlmostEqual(record['actual_duration'], 1.5, delta=0.1)
        self.assertEqual(self.source.read_bytes(), original)
        with self.assertRaises(FileExistsError):
            self.invoke()

    def test_mux_failure_leaves_no_formal_output(self):
        real_run = render.run
        def fail_mux(cmd):
            if cmd[-1].endswith('verified.mp4'):
                Path(cmd[-1]).write_bytes(b'incomplete')
                raise subprocess.CalledProcessError(1, cmd)
            real_run(cmd)
        with patch.object(render, 'run', side_effect=fail_mux):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke()
        self.assert_no_delivery()

    def test_decode_failure_leaves_no_formal_output(self):
        real_run = render.run
        def fail_decode(cmd):
            if '-xerror' in cmd:
                raise subprocess.CalledProcessError(1, cmd)
            real_run(cmd)
        with patch.object(render, 'run', side_effect=fail_decode):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke()
        self.assert_no_delivery()

    def test_late_conflict_preserves_other_file_and_removes_our_record(self):
        staged_video, staged_record = self.root / 'staged.mp4', self.root / 'staged.json'
        staged_video.write_bytes(b'validated')
        staged_record.write_text('{}')
        self.target.write_bytes(b'other task')
        with self.assertRaises(FileExistsError):
            render.publish_result(staged_video, staged_record, self.target)
        self.assertEqual(self.target.read_bytes(), b'other task')
        self.assertFalse(self.target.with_suffix('.edit.json').exists())

    def test_existing_record_is_not_overwritten(self):
        record = self.target.with_suffix('.edit.json')
        record.write_bytes(b'personal record')
        with self.assertRaises(FileExistsError):
            self.invoke()
        self.assertEqual(record.read_bytes(), b'personal record')
        self.assertFalse(self.target.exists())


class EnvironmentTests(unittest.TestCase):
    def test_missing_tools_is_a_failed_profile(self):
        with patch.object(environment.shutil, 'which', return_value=None):
            result = environment.inspect_environment()
        self.assertFalse(any(result['profiles'].values()))

    def test_optional_hdr_capabilities_do_not_block_sdr(self):
        encoders = ' V..... libx264 H264\n A..... aac AAC\n A..... pcm_s16le PCM\n'
        filters = '\n'.join(' ... ' + n + ' V->V' for n in ['setpts', 'fps', 'format', 'atrim', 'asetpts', 'atempo', 'apad', 'concat'])
        def result(cmd, **kwargs):
            text = encoders if '-encoders' in cmd else filters if '-filters' in cmd else 'test version 1'
            return subprocess.CompletedProcess(cmd, 0, text, '')
        with patch.object(environment.shutil, 'which', side_effect=lambda n: n), patch.object(environment.subprocess, 'run', side_effect=result):
            report = environment.inspect_environment()
        self.assertTrue(report['profiles']['sdr'])
        self.assertFalse(report['profiles']['hdr-to-sdr'])
        self.assertFalse(report['profiles']['preserve-hdr'])


if __name__ == '__main__':
    unittest.main()
