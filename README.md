<div align="center">

# Iceria Contributor Kit

**Write for Iceria with your AI assistant, in the wiki's own style and checked against canon.**

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)
![Code: MIT](https://img.shields.io/badge/code-MIT-green)
![Canon: CC BY-SA 4.0](https://img.shields.io/badge/canon-CC%20BY--SA%204.0-lightgrey)

</div>

A folder you point your AI assistant at when you write for [Iceria](https://iceria.org), so it
drafts in the wiki's own style and checks its facts against the world as it stands. It holds a copy
of the canon pages, the Manual of Style, page templates, and a checker for drafts.

The stewards decline a proposal that is "generic, copied, or leaves its questions unanswered,
whatever tools were used to write it" (Charter 3.1). This kit is there so a draft you made with an
assistant is specific to your nation, checked against canon, and yours.

**Contents:** [Start](#start) · [New nation](#new-nation-before-anything-else) · [Set up a Mac](#set-up-a-mac-once) ·
[Set up Windows](#set-up-windows-once) · [Running the tools](#running-the-tools) ·
[Install and start Claude Code](#install-and-start-claude-code) ·
[Use it with Claude Code](#use-it-with-claude-code) ·
[Where your drafts go](#where-your-drafts-go) ·
[Making your plan last](#making-your-plan-last) ·
[How a page gets written](#how-a-page-gets-written) · [Running the tests](#running-the-tests) ·
[Keeping it current](#keeping-it-current) · [What is in here](#what-is-in-here) ·
[License](#license)

## Start

| You use | Do this |
|---|---|
| Claude Code | Install it once ([steps below](#install-and-start-claude-code)), open this folder and ask for the page you want. `CLAUDE.md` and the skills load by themselves. This is the one path a person has run start to finish. |
| Codex, Cursor or another coding assistant (**untested**) | Open this folder; it reads `AGENTS.md`. No person has run this path yet, so expect rough edges and tell the maintainer. |
| A claude.ai or ChatGPT Project (**untested**) | Paste `project-pack/instructions.md` into the project's instructions and upload every file in `project-pack/knowledge/`. No person has run this path yet either. |

## New nation: before anything else

A new nation starts with its claim, not with pages. You must be 18 or older and have joined the
Iceria Discord. Paint your claim in the Claim Studio (studio.iceria.org) until its pre-check
passes, then post the proposal. Your nation's other pages wait until the stewards make it
provisional, so do not draft them yet.

## Set up a Mac (once)

The tools need Python 3.10 or later and nothing else.

1. **Install Python from [python.org](https://www.python.org/downloads/)**, the latest release.

> [!WARNING]
> Not Homebrew's: Homebrew's Python refuses `pip install` (PEP 668). The `python3` a Mac comes
> with is too old.

2. **Install the certificates.** Open **Applications > Python 3.x** and double-click
   **Install Certificates.command**, so Python can reach the wiki.

> [!TIP]
> If `tools/doctor.py` (step 6) still prints `FIX certificates`, do what that line says.

3. **Open a new Terminal window.** The old one keeps finding the old Python.
4. **Check Git.** Type this; if the Mac offers to install the developer tools, say yes:

   ```bash
   git --version
   ```

5. **Get the kit.** In Terminal, run these one at a time:

   ```bash
   cd ~/Documents
   ```

   ```bash
   git clone https://github.com/eddyplolz/iceria-workflow.git
   ```

   ```bash
   cd iceria-workflow
   ```

6. **Check everything:**

   ```bash
   python3 tools/doctor.py
   ```

   Each line says `OK` or `FIX`, and a `FIX` line names the one thing to do. It exits 0 when every
   line is OK. The humanizer is optional, so until step 7 its line says `OK` and how to add it.

> [!TIP]
> Stuck? Run `python3 tools/doctor.py` and send the kit's maintainer everything it prints.

7. **The AI-tell audit (optional; skip it and the checker says so):**

   ```bash
   python3 -m pip install humanizer-pro
   ```

For updates later, see [Keeping it current](#keeping-it-current) below.

## Set up Windows (once)

<details>
<summary><b>Show the Windows steps</b></summary>

<br>

| Step | Windows |
|---|---|
| 1. Python | Install the latest Python from [python.org](https://www.python.org/downloads/). It brings the `py` command. |
| 2. Git | Install [Git for Windows](https://git-scm.com) or [GitHub Desktop](https://desktop.github.com). |
| 3. Get the kit | `git clone https://github.com/eddyplolz/iceria-workflow.git` (or GitHub Desktop: **File > Clone repository**). For updates, see [Keeping it current](#keeping-it-current) below. |
| 4. Open a terminal in the kit folder | Open the folder in File Explorer, then type `cmd` in its address bar. |
| 5. The AI-tell audit (optional) | `py -m pip install humanizer-pro` |
| 6. Check everything | `py tools/doctor.py`: each line says OK or FIX, and a FIX line names the one thing to do. Stuck? Send the kit's maintainer everything it prints. |

In Git Bash on Windows, run `setup_bot.py` as `winpty py tools/setup_bot.py`, or its hidden
password prompt cannot read what you type.

</details>

## Running the tools

The commands below say `python`. Type `python3` on a Mac and `py` on Windows. All of them read;
none writes to the wiki.

| Command | What it does |
|---|---|
| `python tools/check.py draft.wiki --title "Title"` | The style and canon checker. It also asks the live wiki, read-only, whether each category, infobox field and link exists; `--offline` skips that and says so. Add `--humanizer` for the AI-tell audit. |
| `python tools/doctor.py` | Checks this computer's setup, one line per part. Run it first when a tool fails. |
| `python tools/redlinks.py draft.wiki` | Lists each link in the draft that has no page on the wiki yet. |
| `python tools/map_overlay.py examples/plan.json` | Draws your places and routes on the map, inside your own land only; it works only for a nation whose claim is accepted. Copy `examples/plan.json` to `notes/` and make it yours. |
| `python tools/iceria_calendar.py` | Today's in-world date; `--real 2027-01-15` and `--in-world "14 March 2001"` convert either way. |
| `python tools/refresh_canon.py` | Rebuilds the canon copy from today's wiki; `--check` only says whether a refresh is due. |
| `python tools/setup_bot.py` | Saves your own bot password in your computer's password store; `--check` tests it. |

To test the setup, run the checker on any `.wiki` file (your assistant keeps drafts in
[`notes/drafts/`](#where-your-drafts-go)):

```bash
python tools/check.py notes/drafts/my-draft.wiki --title "Page title"
```

It prints each problem with its line and the rule it breaks, and exits 1 while any error is left.
If it says the kit needs Python 3.10 or newer, Python is not installed yet. With `--humanizer` it
also runs [humanizer-pro](https://pypi.org/project/humanizer-pro/)'s audit for AI-sounding prose;
without humanizer-pro installed, the checker says so and skips that audit.

## Install and start Claude Code

Do this once, after the kit is on your computer (Mac steps 1 to 6 above, or the Windows table). It
needs a Claude account on a paid plan. These commands come from Anthropic's own pages,
[Advanced setup](https://code.claude.com/docs/en/setup) and the
[terminal guide](https://code.claude.com/docs/en/terminal-guide); if either has changed, theirs wins.

**On a Mac:**

1. **Open Terminal in the kit folder.** If the window from Mac step 5 is still open, you are
   already there. Otherwise press `Cmd + Space`, type `Terminal`, press `Enter`, then type:

   ```bash
   cd ~/Documents/iceria-workflow
   ```

2. **Install Claude Code.** Paste this line (`Cmd + V`) and press `Enter`. It shows no progress
   while it downloads, so leave the window open until you see "Claude Code successfully installed!":

   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```

3. **If it printed "Setup notes" saying `~/.local/bin is not in your PATH`**, paste this line and
   press `Enter`. It tells new Terminal windows where `claude` is:

   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   ```

4. **Open a new Terminal window and go to the kit folder again** (the `cd` line above). The old
   window does not know about `claude` yet.
5. **Start it.** Type this and press `Enter`:

   ```bash
   claude
   ```

6. **Log in.** The first time, it asks you to log in with your Claude account. A browser window
   opens; sign in there, then go back to Terminal. After that, `claude` starts straight away.

If Terminal says `command not found: claude`, the install folder is not on your PATH yet: see
["command not found: claude"](https://code.claude.com/docs/en/troubleshoot-install#command-not-found-claude-after-installation)
on Anthropic's troubleshooting page.

In Claude Code you type and press `Enter`; you cannot click, so use the arrow keys. `Esc`
stops Claude when it is working, and `exit` leaves. Always start `claude` from inside the
`iceria-workflow` folder, or it will not see the kit.

<details>
<summary><b>On Windows</b></summary>

<br>

Open PowerShell (`Win + X`, then **Windows PowerShell** or **Terminal**; the prompt starts with
`PS`) and paste this line:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Then open the kit folder in File Explorer, type `cmd` in its address bar, and run `claude` there.
Log in as on a Mac.

</details>

## Use it with Claude Code

Open the `iceria-workflow` folder in Claude Code and ask for what you want, for example "help me
write a page about my capital city". `CLAUDE.md` and these six skills load by themselves:

| Skill | What it is for |
|---|---|
| `iceria-advisor` | Answers "can I do this?" and "how does this work on Iceria?" with a citation from the Charter or canon. |
| `iceria-interview` | Asks you about a page, one question at a time, when your notes are thin. |
| `iceria-draft` | Drafts a page for your own nation in wikitext from your notes and a template. |
| `iceria-canon-check` | Matches every claim in a draft to a canon page and lists the NEW facts. |
| `iceria-self-audit` | The style and AI-tell pass before you read the draft. |
| `iceria-report` | Writes a problem report for you to send when the kit gets something wrong. |

## Where your drafts go

Your assistant saves drafts in `notes/drafts/` inside the kit folder (it makes the folder if it is
missing). The `notes/` folder is not part of git, so `git pull` and a canon refresh never touch your
drafts. Run the checker on a draft there, as in the example above.

## Making your plan last

Your Claude plan has a usage limit that fills as you work. Four habits keep it going:

1. Write one article per session, then type `/clear` before the next one.
2. For checking and fixing passes, type `/model sonnet`; save the bigger model for drafting.
3. Chatting on claude.ai uses the same limit as Claude Code, and switching models does not reset it.
4. Start each session from the kit folder, so Claude reads only what the kit points it to.

## How a page gets written

1. Your assistant drafts the page from your notes and a template, and lists every NEW fact the
   draft adds to canon.
2. It runs the checker and matches each claim to a canon page.
3. You read the whole draft.
4. You post pages of your own nation. A new nation goes in through a proposal and steward review.
   Anything that touches another nation goes to its talk page, or to a steward, first.
5. The check report goes with the draft: the kit version, the checker's result, and the NEW facts.

## Running the tests

<details>
<summary><b>Show the test commands</b></summary>

<br>

```bash
python3 -m pip install pytest
```

```bash
python3 -m pytest tools/tests
```

Run both inside the kit folder (on Windows, `py -m` in place of `python3 -m`). The path `tools/tests` keeps the run
to the kit's own tests wherever you start it.

</details>

## Keeping it current

`VERSION.json` records when this copy was taken from the wiki and the revision of every page in it.
The live wiki always outranks the kit. Get the newest copy with `git pull`, or rebuild `canon/` and
`style/` from today's wiki yourself:

```bash
python tools/refresh_canon.py
```

It only reads. It builds the new copy aside and then moves it in folder by folder. If a move fails
(an editor or virus scanner holding a file open), it puts back the folders it had already moved,
and if it cannot put one back it names the folder and where the old copy is waiting. When a page
has changed since your last refresh, you can also paste the live page into the chat.

A refresh rewrites files that `git pull` also updates, so the two can clash. `python tools/doctor.py`
reminds you of the restore line before you pull. It is this: drop the refreshed copy and take
git's:

```bash
git restore canon style templates project-pack/knowledge VERSION.json
```

```bash
git pull
```

Your drafts and notes are not in those folders, so they stay as they are.

<details>
<summary><b>Your own bot password (optional, recommended)</b></summary>

<br>

Without one, the refresh reads the wiki as a visitor and says so with a `NOTICE`. With one, it reads
as your own bot. Each member makes their own; nobody shares one.

1. Log in to the wiki and open
   [Special:BotPasswords](https://www.iceria.org/wiki/Special:BotPasswords).
2. Type a bot name (for example `kit`) and click **Create**.
3. Tick **Basic rights** only. Leave every other box empty, then click **Create**.
4. Run `python tools/setup_bot.py` and type the login name (`YourName@kit`) and password the wiki
   showed. It tests the login, refuses a bot password that could post, and saves it in your
   computer's own password store: the Keychain on a Mac, Credential Manager on Windows. Neither
   needs an install. (On Linux it uses the keyring package: `pip install keyring`.)

`python tools/setup_bot.py --check` tests the saved one. On a machine with no credential store, set
the environment variables `ICERIA_BOT_USER` and `ICERIA_BOT_PASS` instead, in your shell, never in
a file in this folder. The refresh refuses to run if a file of the kit looks like it holds a bot
password. If a password ever ends up somewhere it should not, delete it at Special:BotPasswords
and make a new one.

</details>

## What is in here

<details>
<summary><b>Show the folders</b></summary>

<br>

- `canon/`: geography, culture zones, history, World Standards, the calendar, and each nation's
  article.
- `style/`: the Manual of Style, AI use on Iceria, the Charter clauses on joining, ownership and
  licensing, and a one-page writing checklist.
- `templates/`: skeletons for nation, city, person, organization, event, treaty and proposal pages,
  and the infobox fields.
- `tools/`: the checker, the refresh and bot-password setup, and their tests.
- `project-pack/`: the same material, flattened for a chat Project.

</details>

## License

The text in `canon/`, `style/` and `templates/` comes from the Iceria wiki and is under
[CC BY-SA 4.0](LICENSE-CANON), as the Charter (5.1) sets. The code in `tools/` is under the
[MIT License](LICENSE).
