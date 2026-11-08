#!/usr/bin/env python3
"""PreToolUse hook for Bash: block shell file edits and chained commands.

Exit 2 blocks the call and sends stderr back to Claude (subagents included).
"""
import json
import re
import sys

cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")

# Ignore quoted text so patterns like grep 'a|b' or "x; y" don't trip the checks.
bare = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", cmd)
# Harmless redirects: 2>&1, >/dev/null, 2>/dev/null.
bare = re.sub(r"\d?>&\d|\d?>>?\s*/dev/null", "", bare)

problems = []
if re.search(r"\b(sed|perl)\s+(-\w*\s+)*-\w*i", bare):
    problems.append("in-place edit (sed -i / perl -i)")
if re.search(r"<<-?\s*\S", bare):
    problems.append("heredoc")
if re.search(r"\btee\b", bare):
    problems.append("tee")
if re.search(r">", bare):
    problems.append("output redirect (> or >>)")
if re.search(r"&&|\|\||;|\|", bare):
    problems.append("chained or piped command (&&, ||, ;, |)")

if problems:
    print(
        "Blocked: " + ", ".join(problems) + ". "
        "Edit files with the Edit or Write tools, never from the shell. "
        "Run each command as its own Bash call with no &&, ||, ; or pipes.",
        file=sys.stderr,
    )
    sys.exit(2)
