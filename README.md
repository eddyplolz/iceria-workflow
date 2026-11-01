# Iceria contributor kit

A folder you point your AI assistant at when you write for [Iceria](https://iceria.org), so it
drafts in the wiki's own style and checks its facts against the world as it stands. It holds a copy
of the canon pages, the Manual of Style, page templates, and a checker for drafts.

The stewards decline a proposal that is "generic, copied, or leaves its questions unanswered,
whatever tools were used to write it" (Charter 3.1). This kit is there so a draft you made with an
assistant is specific to your nation, checked against canon, and yours.

## Start

| You use | Do this |
|---|---|
| Claude Code | Open this folder and ask for the page you want. `CLAUDE.md` and the skills load by themselves. |
| Codex, Cursor or another coding assistant | Open this folder; it reads `AGENTS.md`. |
| A claude.ai or ChatGPT Project | Paste `project-pack/instructions.md` into the project's instructions and upload every file in `project-pack/knowledge/`. |

## Set up your computer (once)

The tools need Python 3.10 or later and nothing else.

| Step | Mac | Windows |
|---|---|---|
| 1. Python | Install the latest Python from [python.org](https://www.python.org/downloads/). The `python3` a Mac comes with is too old. Then open **Applications > Python 3.x** and double-click **Install Certificates.command**, so Python can reach the wiki. Open a new Terminal window afterwards, or the old one keeps finding the old Python. | Install the latest Python from [python.org](https://www.python.org/downloads/). It brings the `py` command. |
| 2. Git | Open **Terminal** and type `git --version`. If the Mac offers to install the developer tools, say yes. Or use [GitHub Desktop](https://desktop.github.com). | Install [Git for Windows](https://git-scm.com) or [GitHub Desktop](https://desktop.github.com). |
| 3. Get the kit | `git clone https://github.com/eddyplolz/iceria-workflow.git` (or GitHub Desktop: **File > Clone repository**), then `git pull` inside it for updates. | The same. |
| 4. Open a terminal in the kit folder | **Terminal**, then `cd ` and drag the folder onto the window. | Open the folder in File Explorer, then type `cmd` in its address bar. |
| 5. The AI-tell audit | `python3 -m pip install humanizer-pro` | `py -m pip install humanizer-pro` |
| How to run a tool | `python3 tools/check.py ...` | `py tools/check.py ...` |

The commands below say `python`. Type `python3` on a Mac and `py` on Windows. To test the setup,
run the checker on any `.wiki` file:

```
python tools/check.py my-draft.wiki --title "Page title"
```

If it says the kit needs Python 3.10 or newer, step 1 is not done yet. If the wiki tools say this
Python cannot check the wiki's certificate, run **Install Certificates.command** from step 1. In
Git Bash on Windows, run `setup_bot.py` as `winpty py tools/setup_bot.py`, or its hidden password
prompt cannot read what you type.

The checker prints each problem with its line and the rule it breaks, and exits 1 while any error is left.
Add `--humanizer` and it also runs [humanizer-pro](https://pypi.org/project/humanizer-pro/)'s
audit for AI-sounding prose (step 5). The kit works without it: if step 5 is not done, the checker
says so and skips that audit.

## How a page gets written

1. Your assistant drafts the page from your notes and a template, and lists every NEW fact the
   draft adds to canon.
2. It runs the checker and matches each claim to a canon page.
3. You read the whole draft.
4. You post pages of your own nation. A new nation goes in through a proposal and steward review.
   Anything that touches another nation goes to its talk page, or to a steward, first.
5. The check report goes with the draft: the kit version, the checker's result, and the NEW facts.

## Keeping it current

`VERSION.json` records when this copy was taken from the wiki and the revision of every page in it.
The live wiki always outranks the kit. Get the newest copy with `git pull`, or rebuild `canon/` and
`style/` from today's wiki yourself:

```
python tools/refresh_canon.py
```

It only reads. It builds the new copy aside and then moves it in folder by folder. If a move fails
(an editor or virus scanner holding a file open), it puts back the folders it had already moved,
and if it cannot put one back it names the folder and where the old copy is waiting. When a page
has changed since your last refresh, you can also paste the live page into the chat.

A refresh rewrites files that `git pull` also updates, so the two can clash. Before you pull, drop
the refreshed copy and take git's:

```
git restore canon style templates project-pack/knowledge VERSION.json
git pull
```

Your drafts and notes are not in those folders, so they stay as they are.

### Your own bot password (optional, recommended)

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

## What is in here

- `canon/`: geography, culture zones, history, World Standards, the calendar, and each nation's
  article.
- `style/`: the Manual of Style, AI use on Iceria, the Charter clauses on joining, ownership and
  licensing, and a one-page writing checklist.
- `templates/`: skeletons for nation, city, person, organization, event, treaty and proposal pages,
  and the infobox fields.
- `tools/`: the checker, the refresh and bot-password setup, and their tests.
- `project-pack/`: the same material, flattened for a chat Project.

## License

The text in `canon/`, `style/` and `templates/` comes from the Iceria wiki and is under
[CC BY-SA 4.0](LICENSE-CANON), as the Charter (5.1) sets. The code in `tools/` is under the
[MIT License](LICENSE).
