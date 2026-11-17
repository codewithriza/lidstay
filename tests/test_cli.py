"""Exercise lifecycle behavior without changing host power settings."""
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

CLI = Path(__file__).resolve().parents[1] / 'bin' / 'lidstay'

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.state = self.root / 'sleep-setting'
        self.state.write_text('0\n')
        self.env = dict(os.environ, HOME=str(self.root), SETTING=str(self.state),
                        PATH=str(self.bin) + ':' + os.environ['PATH'])
        scripts = {
            'uname': 'echo Darwin',
            'sudo': 'case "$1" in -v) exit 0;; -n) shift;; esac\n[ "$1" != -v ] || exit 0\nexec "$@"',
            'pmset': 'if [ "$1" = -g ]; then printf "SleepDisabled %s\\n" "$(cat "$SETTING")"; else echo "$3" > "$SETTING"; fi',
            'caffeinate': 'exec sleep 30',
        }
        for name, source in scripts.items():
            p = self.bin / name
            p.write_text('#!/bin/sh\n' + source + '\n')
            p.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, input=None):
        return subprocess.run([str(CLI), *args], env=self.env, input=input,
                              capture_output=True, text=True, timeout=10)

    def test_command_exit_and_arguments(self):
        r = self.run_cli('--lid', '--', 'sh', '-c', 'printf "%s" "$1"; exit 7', 'sh', 'two words')
        self.assertEqual(r.returncode, 7)
        self.assertEqual(r.stdout, 'two words')
        self.assertEqual(self.state.read_text().strip(), '0')

    def test_preserves_preexisting_disabled_sleep(self):
        self.state.write_text('1\n')
        self.assertEqual(self.run_cli('--lid', '--', 'true').returncode, 0)
        self.assertEqual(self.state.read_text().strip(), '1')

    def test_default_does_not_change_setting(self):
        self.assertEqual(self.run_cli('--', 'true').returncode, 0)
        self.assertEqual(self.state.read_text().strip(), '0')

    def test_stdin_is_preserved(self):
        r = self.run_cli('--', 'cat', input='interactive input\n')
        self.assertEqual(r.stdout, 'interactive input\n')

    def test_timer_restores(self):
        self.assertEqual(self.run_cli('--lid', '--for', '1s').returncode, 0)
        self.assertEqual(self.state.read_text().strip(), '0')

    def test_invalid_arguments_do_not_change_setting(self):
        for args in [('--for', '0m'), ('--for', '09m'), ('--for', 'oops'), ('--for', '1s', '--', 'true'), ('--',), ('--bad',)]:
            self.assertNotEqual(self.run_cli(*args).returncode, 0)
        self.assertEqual(self.state.read_text().strip(), '0')

    def test_recovery(self):
        lock = self.root / 'Library/Application Support/lidstay/session'
        lock.mkdir(parents=True)
        (lock / 'previous').write_text('0\n')
        (lock / 'pid').write_text('99999999\n')
        self.state.write_text('1\n')
        self.assertEqual(self.run_cli('restore').returncode, 0)
        self.assertEqual(self.state.read_text().strip(), '0')
        self.assertFalse(lock.exists())

    def test_termination_restores_sleep(self):
        p = subprocess.Popen([str(CLI), '--lid', '--for', '30s'], env=self.env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if self.state.read_text().strip() == '1':
                    break
                time.sleep(0.05)
            self.assertEqual(self.state.read_text().strip(), '1')
            p.terminate()
            self.assertEqual(p.wait(timeout=10), 143)
            self.assertEqual(self.state.read_text().strip(), '0')
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()

    def test_live_lock_is_not_overwritten(self):
        lock = self.root / 'Library/Application Support/lidstay/session'
        lock.mkdir(parents=True)
        (lock / 'pid').write_text(str(os.getpid()))
        (lock / 'previous').write_text('0\n')
        self.assertNotEqual(self.run_cli('--lid', '--', 'true').returncode, 0)
        self.assertNotEqual(self.run_cli('restore').returncode, 0)
        self.assertTrue(lock.exists())

if __name__ == '__main__':
    unittest.main()
