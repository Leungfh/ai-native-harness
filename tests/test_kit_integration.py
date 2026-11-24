import subprocess
import sys
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})


class KitIntegrationTests(unittest.TestCase):
    def test_verify_detects_tampering_and_recovers(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'dist'
            result = run('tools/kit.py', 'build', '--out', output)
            self.assertEqual(result.returncode, 0, result.stderr)
            archive = next(output.glob('*.zip'))
            unpacked = Path(temp) / 'unpacked'
            with zipfile.ZipFile(archive) as package:
                package.extractall(unpacked)
            self.assertEqual(run('tools/kit.py', 'verify', cwd=unpacked).returncode, 0)
            version = unpacked / 'VERSION'
            original = version.read_bytes()
            version.write_bytes(b'tampered')
            self.assertNotEqual(run('tools/kit.py', 'verify', cwd=unpacked).returncode, 0)
            version.write_bytes(original)
            self.assertEqual(run('tools/kit.py', 'verify', cwd=unpacked).returncode, 0)
            self.assertEqual(run('tools/kit.py', 'build', '--out', output).returncode, 0)

    def test_plan_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / 'AGENTS.md').write_text('local rules', encoding='utf-8')
            result = run('tools/kit.py', 'plan', target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('已有同名·人工合并\tAGENTS.md', result.stdout)
            self.assertEqual((target / 'AGENTS.md').read_text(encoding='utf-8'), 'local rules')

    def test_example_business_behavior(self):
        result = run('-m', 'unittest', 'discover', '-s', 'example', '-p', 'test_*.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Ran 4 tests', result.stderr)


if __name__ == '__main__':
    unittest.main()
