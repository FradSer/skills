"""Extract task receipts from the parent-owned Codex command event stream."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import shutil
from typing import Any


RECEIPT_PREFIX = "SKILL_EVAL_SERVICE_RECEIPT "


def command_argvs(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token and all(character in ";&|()\n" for character in token):
            segments.append([])
        else:
            segments[-1].append(token)
    result = []
    for argv in segments:
        while argv and (argv[0] in {"env", "command"} or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0])):
            argv = argv[1:]
        if not argv:
            continue
        if Path(argv[0]).name in {"sh", "bash", "zsh"}:
            index = next((index for index, value in enumerate(argv[1:], 1) if value in {"-c", "-lc"}), None)
            if index is not None and index + 1 < len(argv):
                result.extend(command_argvs(argv[index + 1]))
                continue
        result.append(argv)
    return result


def successful_commands(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event["item"] for event in events if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "command_execution" and event["item"].get("exit_code") == 0]


def trusted_argvs(command: str, tool: str, executable: Path | None = None, allowed_sources: tuple[str, ...] = (), allowed_path_prefix: Path | None = None) -> list[list[str]]:
    if re.search(r"\balias\s+|\bfunction\s+|\b" + re.escape(tool) + r"\s*\(\s*\)", command):
        return []
    parsed = command_argvs(command)
    declarations = re.findall(r"""\bPATH\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s;]+))""", command)
    if re.search(r"\bPATH\s*=", command) and not declarations:
        return []
    if declarations:
        accepted = {str(allowed_path_prefix) + ":$PATH", "$PWD/.fixture/bin:$PATH"} if allowed_path_prefix else set()
        if any(Path(argv[0]).name == "cd" for argv in parsed):
            accepted.discard("$PWD/.fixture/bin:$PATH")
        if any(next((value for value in declaration if value), "") not in accepted for declaration in declarations):
            return []
    if any(Path(argv[0]).name == "eval" or (Path(argv[0]).name in {"source", "."} and (len(argv) < 2 or argv[1] not in allowed_sources)) for argv in parsed):
        return []
    result = []
    for argv in parsed:
        token = argv[0]
        if token == tool:
            result.append(argv)
        elif executable is not None and Path(token).is_absolute() and Path(token).resolve() == executable.resolve():
            result.append(argv)
        elif executable is not None and tool in {"gh", "lark-cli"} and token in {f".fixture/bin/{tool}", f"./.fixture/bin/{tool}"}:
            result.append(argv)
    return result


def operation_receipts(events: list[dict[str, Any]], tool: str, *operation: str, executable: Path | None = None) -> list[str]:
    receipts = []
    for item in successful_commands(events):
        for argv in trusted_argvs(item.get("command", ""), tool, executable):
            if argv[1:1 + len(operation)] == list(operation) and not any(value in {"--help", "-h"} for value in argv):
                receipts.append(str(item.get("id", "unknown")))
    return receipts


def git_push_receipts(events: list[dict[str, Any]]) -> list[str]:
    receipts = []
    executable = shutil.which("git")
    for item in successful_commands(events):
        for argv in trusted_argvs(item.get("command", ""), "git", Path(executable) if executable else None):
            index = 1
            while index < len(argv) and argv[index].startswith("-"):
                index += 2 if argv[index] in {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"} else 1
            if index < len(argv) and argv[index] == "push" and not any(value in {"--help", "-h"} for value in argv):
                receipts.append(str(item.get("id", "unknown")))
    return receipts


def service_receipts(events: list[dict[str, Any]], bin_directory: Path | None = None) -> list[dict[str, Any]]:
    receipts = []
    for event in events:
        item = event.get("item", {})
        if event.get("type") != "item.completed" or item.get("type") != "command_execution":
            continue
        native = [argv for tool in ("gh", "lark-cli") for argv in trusted_argvs(item.get("command", ""), tool, bin_directory / tool if bin_directory else None)]
        for line in item.get("aggregated_output", "").splitlines():
            if line.startswith(RECEIPT_PREFIX):
                value = json.loads(line[len(RECEIPT_PREFIX):])
                if not isinstance(value, dict):
                    raise ValueError("service receipt must be an object")
                args = value.get("args", [])
                if isinstance(args, list) and any(Path(argv[0]).name == value.get("tool") and argv[1:3] == args[:2] for argv in native):
                    receipts.append(value)
    return receipts
