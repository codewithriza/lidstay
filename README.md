# lidstay

Keep your Mac awake for a command, a timer, or an open-ended session. Opt into closed-lid operation when you need it.

```sh
lidstay --lid -- codex
lidstay --lid --for 2h
lidstay -- npm run build
```

Built with macOS tools. No runtime dependencies, background service, or network access.

## Install

Requires macOS and its built-in Bash, `caffeinate`, and `pmset`. Closed-lid sessions require administrator access.

```sh
git clone https://github.com/codewithriza/lidstay.git
cd lidstay
mkdir -p "$HOME/.local/bin"
install -m 755 bin/lidstay "$HOME/.local/bin/lidstay"
```

If `~/.local/bin` is not on your PATH, add this line to `~/.zshrc` and open a new terminal:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Use

| Command | Behavior |
| --- | --- |
| `lidstay` | Prevent idle sleep until Ctrl-C |
| `lidstay --for 45m` | Prevent idle sleep for 45 minutes |
| `lidstay --lid` | Also prevent lid-close sleep until Ctrl-C |
| `lidstay --lid --for 2h` | Closed-lid session lasting two hours |
| `lidstay --lid -- codex` | Keep awake while Codex runs |
| `lidstay --lid -- claude` | Keep awake while Claude Code runs |
| `lidstay -- python3 train.py` | Keep awake until the command exits |
| `lidstay status` | Inspect system sleep and saved session state |
| `lidstay restore` | Recover an interrupted closed-lid session |

For music, start playback in your preferred app, then run `lidstay --lid`. Stop the session with Ctrl-C when finished. Durations accept positive whole seconds (`s`), minutes (`m`), or hours (`h`), up to seven days. A timer and a command cannot be combined.

Commands run as your current user, not as root. Arguments and standard input are passed through, and the command's exit status is returned. Terminal interrupts stop the session; scripts that spawn independent or detached processes remain responsible for those processes.

## Sleep behavior

By default, lidstay uses `caffeinate -i` to prevent idle system sleep. The display can still turn off, and closing the lid retains normal macOS behavior.

`--lid` temporarily sets `pmset -a disablesleep 1`. This is a **system-wide setting**, including battery power. The previous value is saved in `~/Library/Application Support/lidstay/session` and restored on normal exit, Ctrl-C, termination, or terminal closure. Only one closed-lid session is allowed at a time. Ordinary caffeinate sessions can overlap.

If sleep was already disabled before the session, it remains disabled afterward. To explicitly restore normal macOS sleep behavior:

```sh
sudo pmset -a disablesleep 0
```

While a closed-lid session is active, lidstay refreshes its sudo authorization once a minute so restoration can run without another password prompt. It does not modify sudoers or install a privileged helper. If restoration fails, it reports an error and keeps the recovery state.

A forced kill (`kill -9`), power loss, or OS failure cannot run cleanup. After an interrupted session, run `lidstay restore`; it reads the saved setting and restores it after administrator authentication. Do not remove the saved state before recovery. Avoid changing the same power setting from another app during a session.

Closed-lid behavior depends on the Mac and macOS version. Test a short session on your own machine before relying on it for long-running work. Keep the Mac on a ventilated surface, never awake inside a bag; battery drain continues while sleep is disabled. Lidstay does not bypass thermal shutdown or keep work running after power loss.

## Development

```sh
bash -n bin/lidstay
python3 -m unittest discover -s tests -v
```

The lifecycle tests substitute macOS commands and never change the test host's power settings. CI runs them on macOS and Linux. Python is needed only for tests.

To customize behavior, edit `bin/lidstay`. Keep changes to global power settings inside the saved-state lifecycle, and test both an initially enabled and initially disabled sleep setting.

## Uninstall

Stop any active session and run `lidstay restore` if it reports interrupted state. Then remove the executable:

```sh
rm "$HOME/.local/bin/lidstay"
```

## License

MIT. See [LICENSE](LICENSE).
