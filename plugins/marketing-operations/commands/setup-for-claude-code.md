---
description: If you intend to use the plugin skills within Claude Code then run this command in the Code tab to install the Python dependencies. If you will be running the skills from Cowork then you can skip this command
allowed-tools: ["Bash", "Read", "AskUserQuestion"]
---

# Set up Marketing Operations on this machine

Most people can skip this entirely — every skill in this plugin installs whatever it
needs on its own, the first time it runs. This command exists only to make that install
*permanent* on your own computer, so it never has to happen again.

## Step 0: Find the Python interpreter

Every step below runs Python, so settle this first:

```bash
PY=""; for c in python3 python; do
  command -v "$c" >/dev/null 2>&1 && "$c" -c "pass" 2>/dev/null && { PY="$c"; break; }
done
[ -n "$PY" ] && echo "python ok: $PY" || echo "python missing"
```

**Use whatever it names wherever this command writes `python3`.** macOS and Linux generally
answer `python3`; a Windows install from python.org answers `python`.

**On `python missing`, match the advice to the machine** — `uname -s` says which (`Darwin`,
`Linux`, or `MINGW`/`MSYS` under Git Bash on Windows):

- **macOS** — Python ships with the OS but needs Apple's developer tools switched on once.
  This is the common case on a Mac that has never been used for development:

  > Your Mac has Python but hasn't switched it on yet. Run `xcode-select --install` and click
  > through the installer that appears. A few minutes, and it doesn't need your password.

- **Windows** — install from [python.org](https://www.python.org/downloads/), ticking **Add
  python.exe to PATH** on the first screen, or run `winget install Python.Python.3.12`.

- **Linux** — `sudo apt install python3` on Debian and Ubuntu, `sudo dnf install python3` on
  Fedora.

Wait for them, re-run the check, and carry on once it names an interpreter. Everything from
here needs it, this command included.

## Step 1: Figure out where this is running

```bash
python3 -c "import os; print('cowork' if os.path.isdir('/mnt/user-data') or os.path.isdir('/mnt/outputs') else ('claude-code' if os.environ.get('CLAUDECODE') else 'unknown'))"
```

**Check for Cowork first, and don't use `CLAUDECODE` to rule it out.** Cowork *is* Claude
Code, running in a cloud container, so that variable is set in both places. The thing that
actually separates them is the container's own `/mnt` folders, which exist in Cowork and
on nobody's laptop. Test those first or Cowork reports itself as Claude Code and installs
packages into a container that gets thrown away.

### Running in Cowork

Tell the user this, then stop — don't install anything:

> Nothing to do here — you can start using the plugin's skills right away. Each one
> installs anything it needs automatically, in the background, the first time it runs.
>
> If you also use Claude Code (the **Code** tab in the desktop app), re-run this same
> command there. That installs the dependencies directly on your computer, so the
> skills use those instead of installing their own each time they run.

Never suggest the plugin needs Claude Code to work in Cowork — it doesn't. Claude Code
is only a convenience for people who use both.

### Running in Claude Code

Continue to Step 2 — installs here land on the user's own machine and persist.

## Step 2: Install

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_dependencies.py --install-missing
```

Everything installs at the user level — nothing needs a password or touches system-wide
files. That includes `gifsicle`, which installs as a plain Python package instead of
requiring a separate install through Homebrew.

Run it, then run the plain check again and tell the user what changed. The useful thing
to report is what a skill would otherwise have had to install for itself mid-run.

## Step 3: The Clay CLI, for anyone uploading contact lists

Only the `list-upload` skill uses this, and only for people whose team runs Clay. Ask first:

> One more thing, and it only matters if you clean and upload **contact lists** with Clay.
>
> Clay's command-line tool lets me send a whole list as a file. Without it, every row of
> your list gets written out one at a time before Clay even starts — around 7 minutes for a
> 1,000-row list, 18 for 2,500. With it, any size takes seconds.
>
> Setting it up takes about a minute and ends with you approving a sign-in in your browser.
> Want me to?

Where they say no, stop here — `list-upload` still works through the Clay connector, and it
says so when it runs.

### Install

**Clay's CLI is macOS and Linux only.** The launcher is a shell script and the release ships
four binaries — `darwin-arm64`, `darwin-x64`, `linux-arm64`, `linux-x64` — with nothing for
Windows. On Windows, say so and stop here; `list-upload` uses the Clay connector instead, at
the cost the table in that skill sets out.

The CLI ships in Clay's own repository as a launcher that downloads a checksum-verified
binary for this machine on first use. (The `clay` and `clay-cli` packages on npm are
unrelated projects by other authors.)

```bash
mkdir -p ~/.clay && rm -rf ~/.clay/agent-plugins
git clone -q --depth 1 https://github.com/clay-run/agent-plugins.git ~/.clay/agent-plugins
~/.clay/agent-plugins/clay/bin/clay --version
```

`~/.clay/agent-plugins/clay/bin/clay` is where `list-upload` looks, so this path is the one
to use.

### Sign in

Check first — a machine that has been set up before is already signed in:

```bash
~/.clay/agent-plugins/clay/bin/clay whoami
```

That returns the workspace and user when a session exists. Otherwise start the device flow.
It waits for approval, so run it in the background and read the file:

```bash
~/.clay/agent-plugins/clay/bin/clay login --device > /tmp/clay_login.log 2>&1 &
sleep 5; cat /tmp/clay_login.log
```

Give the user the URL and the code, wait for them to approve it, then confirm with `whoami`
and tell them which Clay workspace they landed in. The session lives in
`~/.config/clay/config.json` and every later run reuses it.

### Where the routines have to be switched on

The CLI reaches a Clay function only when that function has **API & CLI** enabled. In Clay,
open the function → **Integrations** → tick **API & CLI**. Worth mentioning now, because the
symptom later is a `not_found` on a routine that plainly exists.

## Step 4: The Salesforce CLI, for anyone looking up contacts in Salesforce

Also `list-upload` only, and only where the team runs Salesforce. Ask:

> Last one, and it only matters if your contact lists get checked against **Salesforce**.
>
> Salesforce's own command-line tool lets me look the whole list up in one query — a
> 2,287-address list came back in about 9 seconds in testing. Through the connector the same
> lookup is written out in chunks and takes far longer.
>
> It installs in a minute and ends with you signing in through your browser. Want me to?

Where they say no, stop — `list-upload` still queries Salesforce through the connector.

### Install and sign in

```bash
npm install -g @salesforce/cli
sf --version
```

Homebrew works too (`brew install --cask salesforce-cli`) where npm's global directory needs
a password.

Check for an existing org first — a machine set up before is already signed in:

```bash
sf org list
```

Otherwise sign in. This opens a browser and returns once the user has approved it, so run it
in the background and tell them to expect the browser tab:

```bash
sf org login web --alias <their-org-name> --set-default
```

Confirm with `sf org list` and tell them which org and username they landed in.

**This version signs in through a local browser.** For a machine with no browser, the
alternatives are `sf org login jwt` (a connected app plus a private key, which is admin
setup) and `sf org login sfdx-url`. Worth knowing before promising it works everywhere.

## Notes

- Skills never depend on this having been run — they check and install for themselves,
  every time, quietly. This command only saves them a few seconds.
- The Knak Email Marketing plugin needs nothing installed at all — `email-brief-generator`,
  `email-scorer` and `newsletter-content-sourcer` are pure model work, so it has no setup
  command of its own.
- `--json` gives machine-readable output, if something needs to check status before
  running this.
