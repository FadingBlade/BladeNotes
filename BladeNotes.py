#!/usr/bin/env python3
"""
BladeNotes — terminal notes manager. No cloud. No accounts. Just notes.

  notes new <title>            create a new note (opens editor)
  notes write <id> <text>      append text to a note
  notes read <id>              read a note
  notes list                   list all notes
  notes search <keyword>       search notes
  notes edit <id> <text>       overwrite a note's body
  notes rename <id> <title>    rename a note
  notes tag <id> <tag>         add a tag
  notes remove <id>            delete a note
  notes clear --all            delete all notes
  notes export <id> [<file>]   export a note to .txt
  notes stats                  show stats
  notes update                 update to latest version
  notes uninstall              remove BladeNotes
  notes help                   show all commands
"""

import sys, os, json, shutil, urllib.request
from datetime import datetime, date
from pathlib import Path

VERSION   = "1.0.0"
DATA_DIR  = Path.home() / ".bladenotes"
DATA_FILE = DATA_DIR / "notes.json"
RAW       = "https://raw.githubusercontent.com/FadingBlade/BladeNotes/main/BladeNotes.py"

# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    RST  = "\033[0m";  BOLD = "\033[1m";  DIM  = "\033[2m"
    BRED = "\033[91m"; BGRN = "\033[92m"; BYEL = "\033[93m"
    BBLU = "\033[94m"; BMAG = "\033[95m"; BCYN = "\033[96m"; BWHT = "\033[97m"
    RED  = "\033[31m"; GRN  = "\033[32m"; YEL  = "\033[33m"; CYN  = "\033[36m"

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        for attr in [a for a in vars(C) if not a.startswith("_")]:
            setattr(C, attr, "")

# ── Storage ───────────────────────────────────────────────────────────────────

def load() -> list:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def save(notes: list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def next_id(notes: list) -> int:
    return max((n["id"] for n in notes), default=0) + 1

# ── Helpers ───────────────────────────────────────────────────────────────────

def cols() -> int:
    return shutil.get_terminal_size((80, 24)).columns

def ruler(char="─"):
    return C.DIM + char * min(cols(), 72) + C.RST

def fmt_tags(tags: list) -> str:
    if not tags:
        return ""
    return " " + " ".join(f"{C.BMAG}#{t}{C.RST}" for t in tags)

def fmt_item(n: dict) -> str:
    nid      = f"{C.DIM}#{n['id']:>3}{C.RST} "
    title    = n.get("title", "Untitled")
    tags     = fmt_tags(n.get("tags", []))
    created  = n.get("created", "")
    updated  = n.get("updated", "")
    ts       = updated if updated else created
    words    = len(n.get("body", "").split())
    meta     = f" {C.DIM}({words}w  {ts}){C.RST}"
    return f"  {nid}{C.BWHT}{title}{C.RST}{tags}{meta}"

def die(msg: str):
    print(f"\n  {C.BRED}✖ {msg}{C.RST}\n"); sys.exit(1)

def warn(msg: str):
    print(f"\n  {C.BYEL}⚠ {msg}{C.RST}\n")

def get_id(s: str) -> int:
    try:    return int(s.lstrip("#"))
    except: die(f"'{s}' is not a valid note ID.")

def find(notes: list, nid: int) -> dict:
    for n in notes:
        if n["id"] == nid:
            return n
    die(f"No note with ID #{nid}.")

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def _find_self():
    script = os.path.abspath(__file__)
    folder = os.path.dirname(script)
    return script, folder

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_new(args):
    if not args: die("Usage: notes new <title>")
    title = " ".join(args).strip()
    notes = load()
    # Check for duplicate title
    for n in notes:
        if n.get("title", "").lower() == title.lower():
            warn(f"A note named \"{title}\" already exists (#{n['id']}).")
            return
    n = {
        "id":      next_id(notes),
        "title":   title,
        "body":    "",
        "tags":    [],
        "created": now(),
        "updated": "",
    }
    notes.append(n)
    save(notes)
    print(f"\n  {C.BGRN}✔ Created{C.RST}\n{fmt_item(n)}")
    print(f"\n  {C.DIM}Use  notes write {n['id']} <text>  to add content.{C.RST}\n")

def cmd_write(args):
    if len(args) < 2: die("Usage: notes write <id> <text>")
    nid   = get_id(args[0])
    text  = " ".join(args[1:]).strip()
    notes = load()
    n     = find(notes, nid)
    n["body"]    = (n["body"] + "\n" + text).lstrip("\n")
    n["updated"] = now()
    save(notes)
    print(f"\n  {C.BGRN}✔ Written{C.RST}\n{fmt_item(n)}\n")

def cmd_read(args):
    if not args: die("Usage: notes read <id>")
    nid   = get_id(args[0])
    notes = load()
    n     = find(notes, nid)
    body  = n.get("body", "").strip()
    print()
    print(f"  {C.BOLD}{C.BWHT}{n['title']}{C.RST}{fmt_tags(n.get('tags',[]))}")
    print(f"  {C.DIM}created {n.get('created','')}  "
          + (f"updated {n.get('updated','')}" if n.get("updated") else "") + C.RST)
    print(f"  {ruler()}")
    if body:
        for line in body.splitlines():
            print(f"  {line}")
    else:
        print(f"  {C.DIM}(empty){C.RST}")
    print()

def cmd_list(args):
    notes = load()
    filter_tag = None
    i = 0
    while i < len(args):
        if args[i] == "--tag" and i+1 < len(args):
            i += 1; filter_tag = args[i].lstrip("#")
        i += 1
    items = notes
    if filter_tag:
        items = [n for n in items if filter_tag in n.get("tags", [])]
    print()
    if not items:
        print(f"  {C.DIM}No notes found.{C.RST}\n"); return
    label = f"all notes  ({len(items)})"
    if filter_tag: label += f"  #{filter_tag}"
    print(f"  {C.BOLD}{C.BCYN}BladeNotes{C.RST}  {C.DIM}{label}{C.RST}")
    print(f"  {ruler()}")
    for n in items:
        print(fmt_item(n))
    print()

def cmd_search(args):
    if not args: die("Usage: notes search <keyword>")
    q     = " ".join(args).lower()
    notes = load()
    found = [n for n in notes
             if q in n.get("title","").lower()
             or q in n.get("body","").lower()
             or any(q in t.lower() for t in n.get("tags",[]))]
    print()
    if not found:
        print(f"  {C.DIM}No results for \"{q}\".{C.RST}\n"); return
    print(f"  {C.BOLD}Search:{C.RST} {C.DIM}\"{q}\"  ({len(found)} result{'s' if len(found)!=1 else ''}){C.RST}")
    print(f"  {ruler()}")
    for n in found:
        print(fmt_item(n))
    print()

def cmd_edit(args):
    if len(args) < 2: die("Usage: notes edit <id> <text>")
    nid   = get_id(args[0])
    text  = " ".join(args[1:]).strip()
    notes = load()
    n     = find(notes, nid)
    n["body"]    = text
    n["updated"] = now()
    save(notes)
    print(f"\n  {C.BCYN}✎ Updated{C.RST}\n{fmt_item(n)}\n")

def cmd_rename(args):
    if len(args) < 2: die("Usage: notes rename <id> <new title>")
    nid   = get_id(args[0])
    title = " ".join(args[1:]).strip()
    notes = load()
    n     = find(notes, nid)
    n["title"]   = title
    n["updated"] = now()
    save(notes)
    print(f"\n  {C.BCYN}✎ Renamed{C.RST}\n{fmt_item(n)}\n")

def cmd_tag(args):
    if len(args) < 2: die("Usage: notes tag <id> <tag>")
    nid = get_id(args[0]); tag = args[1].lstrip("#")
    notes = load(); n = find(notes, nid)
    if tag not in n.setdefault("tags", []): n["tags"].append(tag)
    n["updated"] = now()
    save(notes)
    print(f"\n  {C.BMAG}# Tagged{C.RST}\n{fmt_item(n)}\n")

def cmd_remove(args):
    if not args: die("Usage: notes remove <id>")
    nid   = get_id(args[0])
    notes = load(); n = find(notes, nid)
    notes.remove(n); save(notes)
    print(f"\n  {C.BRED}✖ Removed{C.RST}  {C.DIM}#{nid} \"{n['title']}\"{C.RST}\n")

def cmd_clear(args):
    if "--all" not in args: die("Usage: notes clear --all")
    notes = load(); count = len(notes); save([])
    print(f"\n  {C.BRED}✖ Cleared all {count} note{'s' if count!=1 else ''}.{C.RST}\n")

def cmd_export(args):
    if not args: die("Usage: notes export <id> [<file>]")
    nid     = get_id(args[0])
    outfile = args[1] if len(args) > 1 else None
    notes   = load(); n = find(notes, nid)
    lines   = [
        n["title"],
        "=" * len(n["title"]),
        f"Created : {n.get('created','')}",
        f"Updated : {n.get('updated','')}",
        f"Tags    : {' '.join('#'+t for t in n.get('tags',[]))}",
        "",
        n.get("body","").strip(),
    ]
    output = "\n".join(lines)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n  {C.BGRN}✔ Exported \"{n['title']}\" to {outfile}{C.RST}\n")
    else:
        print(); print(output); print()

def cmd_stats(args):
    notes   = load()
    total   = len(notes)
    words   = sum(len(n.get("body","").split()) for n in notes)
    empty   = sum(1 for n in notes if not n.get("body","").strip())
    tag_counts = {}
    for n in notes:
        for t in n.get("tags",[]): tag_counts[t] = tag_counts.get(t,0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
    w = 28
    print()
    print(f"  {C.BOLD}{C.BCYN}BladeNotes stats{C.RST}")
    print(f"  {ruler()}")
    print(f"  {'Total notes':<{w}} {C.BWHT}{total}{C.RST}")
    print(f"  {'Total words':<{w}} {C.BWHT}{words}{C.RST}")
    print(f"  {'Empty notes':<{w}} {C.DIM}{empty}{C.RST}")
    if top_tags:
        print(f"  {ruler('·')}")
        tag_str = "  ".join(f"{C.BMAG}#{tag}{C.RST} ({n})" for tag, n in top_tags)
        print(f"  Top tags   {tag_str}")
    print()

def cmd_update(args):
    script, _ = _find_self()
    print(f"\n  {C.DIM}Checking for updates...{C.RST}", flush=True)
    try:
        with urllib.request.urlopen(RAW, timeout=8) as r:
            new_src = r.read()
        new_ver = VERSION
        for line in new_src.decode().splitlines():
            if line.strip().startswith("VERSION"):
                try: new_ver = line.split('"')[1]
                except IndexError: pass
                break
        if new_ver == VERSION:
            print(f"  {C.BGRN}✔ Already up to date{C.RST}  (v{VERSION})\n"); return
        with open(script, "wb") as f:
            f.write(new_src)
        print(f"  {C.BGRN}✔ Updated{C.RST}  v{VERSION} → v{new_ver}\n")
    except Exception as e:
        print(f"  {C.BRED}✖ Update failed:{C.RST} {e}\n")

def cmd_uninstall(args):
    script, folder = _find_self()
    print(f"\n  {C.BYEL}This will remove BladeNotes from your machine.{C.RST}")
    try:
        ans = input("  Are you sure? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {C.DIM}Cancelled.{C.RST}\n"); return
    if ans != "y":
        print(f"  {C.DIM}Cancelled.{C.RST}\n"); return
    removed = []
    if DATA_DIR.exists():
        try: shutil.rmtree(DATA_DIR); removed.append(str(DATA_DIR))
        except Exception as e: print(f"  {C.DIM}Could not remove {DATA_DIR}: {e}{C.RST}")
    try: os.remove(script); removed.append(script)
    except Exception as e: print(f"  {C.DIM}Could not remove {script}: {e}{C.RST}")
    for wrapper in [os.path.join(folder, "notes"), os.path.join(folder, "notes.cmd")]:
        if os.path.exists(wrapper):
            try: os.remove(wrapper); removed.append(wrapper)
            except Exception as e: print(f"  {C.DIM}Could not remove {wrapper}: {e}{C.RST}")
    if removed:
        print(f"\n  {C.BGRN}✔ Removed:{C.RST}")
        for f in removed: print(f"    {C.DIM}{f}{C.RST}")
    print(f"\n  {C.DIM}BladeNotes uninstalled. Goodbye.{C.RST}\n")

def cmd_help(args):
    print(f"""
  {C.BOLD}{C.BCYN}BladeNotes{C.RST} {C.DIM}v{VERSION}{C.RST}  — terminal notes manager

  {C.BOLD}Commands:{C.RST}
    {C.BCYN}notes new <title>{C.RST}                create a new note
    {C.BCYN}notes write <id> <text>{C.RST}          append text to a note
    {C.BCYN}notes read <id>{C.RST}                  read a note
    {C.BCYN}notes list{C.RST} {C.DIM}[--tag <tag>]{C.RST}          list all notes
    {C.BCYN}notes search <keyword>{C.RST}           search title, body, tags
    {C.BCYN}notes edit <id> <text>{C.RST}           overwrite note body
    {C.BCYN}notes rename <id> <title>{C.RST}        rename a note
    {C.BCYN}notes tag <id> <tag>{C.RST}             add a tag
    {C.BCYN}notes remove <id>{C.RST}                delete a note
    {C.BCYN}notes clear --all{C.RST}                delete all notes
    {C.BCYN}notes export <id> [<file>]{C.RST}       export note to .txt
    {C.BCYN}notes stats{C.RST}                      summary stats
    {C.BCYN}notes update{C.RST}                     update to latest version
    {C.BCYN}notes uninstall{C.RST}                  remove BladeNotes
    {C.BCYN}notes help{C.RST}                       show this help

  {C.BOLD}Shortcuts:{C.RST}
    {C.DIM}new→n  list→ls  remove→rm  search→s{C.RST}

  {C.DIM}Data stored at: {DATA_FILE}{C.RST}
""")

# ── Main ──────────────────────────────────────────────────────────────────────

ALIASES  = {"n": "new", "ls": "list", "rm": "remove", "s": "search"}
DISPATCH = {
    "new":       cmd_new,
    "write":     cmd_write,
    "read":      cmd_read,
    "list":      cmd_list,
    "search":    cmd_search,
    "edit":      cmd_edit,
    "rename":    cmd_rename,
    "tag":       cmd_tag,
    "remove":    cmd_remove,
    "clear":     cmd_clear,
    "export":    cmd_export,
    "stats":     cmd_stats,
    "update":    cmd_update,
    "uninstall": cmd_uninstall,
    "help":      cmd_help,
}

def main():
    args = sys.argv[1:]
    if not args:
        cmd_help([]); return
    cmd  = ALIASES.get(args[0].lower(), args[0].lower())
    rest = args[1:]
    if cmd in DISPATCH:
        DISPATCH[cmd](rest)
    else:
        die(f"Unknown command: '{cmd}' — try notes help")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.DIM}Bye.{C.RST}")
