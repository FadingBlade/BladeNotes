# BladeNotes
Local terminal notes manager.
## Install
**Linux / macOS:**
```sh
curl -fsSL https://raw.githubusercontent.com/FadingBlade/BladeNotes/main/install.sh | sh
```
**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/FadingBlade/BladeNotes/main/install.ps1 | iex
```
The installer detects your OS and installs Python if needed and adds the `notes` command to your PATH.

---

## Commands
```
notes new <title>              create a new note
notes write <id> <text>        append text to a note
notes read <id>                read a note
notes list                     list all notes
notes list --tag <tag>         filter by tag
notes search <keyword>         search title, body, and tags
notes edit <id> <text>         overwrite note body
notes rename <id> <title>      rename a note
notes tag <id> <tag>           add a tag to a note
notes remove <id>              delete a note
notes clear --all              delete all notes
notes export <id> [<file>]     export a note to .txt
notes stats                    show summary stats
notes update                   update to latest version
notes uninstall                remove BladeNotes
notes help                     show all commands
notes                          show all commands
```

---

## Requirements
- Python 3.7+ (installer handles this)
- Works fully offline — no internet needed after install

---

## Uninstall
**Linux / macOS:** `rm ~/.local/bin/notes ~/.local/bin/BladeNotes.py`

**Windows:** Delete `%USERPROFILE%\.BladeNotes` and remove it from PATH in System Settings.

(Or just run `notes uninstall`)
