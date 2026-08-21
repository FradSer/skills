#!/usr/bin/env bash
# Link a skill into other agent runtimes' skill directories — only on explicit user confirmation.
# Canonical source is either ./.agents/skills/<name> (project-local, default) or
# ~/.agents/skills/<name> (global). This script never decides scope on its own;
# the skill-creator SKILL.md asks the user first where to create, and only runs
# this linker after the user explicitly confirms which targets to link.
#
# Usage:
#   ./.agents/skills/skill-creator/scripts/link-skills.sh <skill-name> [--project-root <path>] [--to <target>]... [--force]
#   ./.agents/skills/skill-creator/scripts/link-skills.sh --all [--project-root <path>] [--to <target>]... [--force]
#
#   <target> in: agents (~/.agents/skills), codex (~/.codex/skills),
#               claude (~/.claude/skills), pi (~/.pi/agent/skills)
#   Repeat --to for multiple targets. If no --to is given and stdin is a TTY,
#   the script prompts interactively; otherwise it does nothing and explains
#   how to choose targets (never auto-links 4 targets).

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

PROJECT_ROOT=""
FORCE=false
LINK_ALL=false
SKILL_NAME=""
TO_ARGS=()  # list of target keys: agents|codex|claude|pi

usage() {
  cat <<EOF
${BLUE}link-skills.sh${NC} — ask-first skill linker (no auto-link)

${GREEN}Usage:${NC}
  $0 <skill-name> [--project-root <path>] [--to <target>]... [--force]
  $0 --all [--project-root <path>] [--to <target>]... [--force]

${GREEN}Targets (--to):${NC}
  agents   → ~/.agents/skills/<name>
  codex    → ~/.codex/skills/<name>
  claude   → ~/.claude/skills/<name>
  pi       → ~/.pi/agent/skills/<name>
  Repeat --to for multiple targets. Example: --to codex --to claude

${GREEN}Options:${NC}
  --project-root <path>  Project root containing .agents/skills (default: git top-level or cwd)
  --force                Replace existing non-symlink directories with symlinks (backs up)
  --all                  Link every skill found under the canonical source dir
  -h, --help             Show help

${GREEN}Behaviour:${NC}
  Canonical source is either <project-root>/.agents/skills/<name> or
  ~/.agents/skills/<name> — whichever exists (project preferred when both exist).
  System (~/.agents/skills) and project (./.agents/skills) are separate intents:
  creation asks first where to create; this script only links after explicit
  user confirmation. With no --to and a TTY, it prompts; without a TTY and no
  --to, it does nothing and prints how to choose targets.

EOF
}

log_info()    { printf "${BLUE}[INFO]${NC} %s\n" "$1" >&2; }
log_success() { printf "${GREEN}[OK]${NC} %s\n" "$1" >&2; }
log_warn()    { printf "${YELLOW}[WARN]${NC} %s\n" "$1" >&2; }
log_error()   { printf "${RED}[ERR]${NC} %s\n" "$1" >&2; }

resolve_project_root() {
  if [[ -n "$PROJECT_ROOT" ]]; then
    (cd "$PROJECT_ROOT" && pwd)
    return
  fi
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    git rev-parse --show-toplevel
    return
  fi
  pwd
}

target_path_for() {
  case "$1" in
    agents) echo "$HOME/.agents/skills" ;;
    codex)  echo "$HOME/.codex/skills" ;;
    claude) echo "$HOME/.claude/skills" ;;
    pi)     echo "$HOME/.pi/agent/skills" ;;
    *)      echo "" ;;
  esac
}

find_canonical() {
  local skill="$1" project_root="$2"
  local proj="$project_root/.agents/skills/$skill"
  local glob="$HOME/.agents/skills/$skill"
  if [[ -f "$proj/SKILL.md" && -f "$glob/SKILL.md" ]]; then
    printf "${YELLOW}[WARN]${NC} Both project and global copies exist; preferring project: %s\n" "$proj" >&2
    echo "$proj"
    return 0
  fi
  if [[ -f "$proj/SKILL.md" ]]; then echo "$proj"; return 0; fi
  if [[ -f "$glob/SKILL.md" ]]; then echo "$glob"; return 0; fi
  return 1
}

prompt_for_targets() {
  local canonical="$1"
  echo ""
  printf "${BLUE}Canonical:${NC} %s\n" "$canonical"
  echo "System (~/.agents/skills) and project (./.agents/skills) are separate."
  echo "Choose which agent runtimes to symlink this skill into (comma-separated), or 'none':"
  echo "  [agents] ~/.agents/skills  [codex] ~/.codex/skills  [claude] ~/.claude/skills  [pi] ~/.pi/agent/skills"
  printf "Targets (e.g. codex,claude or none): "
  local ans
  # shellcheck disable=SC2162
  read ans || ans="none"
  ans="$(echo "$ans" | tr '[:upper:]' '[:lower:]' | tr -d ' ')"
  if [[ "$ans" == "none" || "$ans" == "n" || "$ans" == "" ]]; then
    echo "none"
    return 0
  fi
  # normalize: allow full names or keys
  echo "$ans"
}

link_one_skill() {
  local skill="$1" canonical="$2"
  local targets=()

  if [[ ${#TO_ARGS[@]} -gt 0 ]]; then
    targets=("${TO_ARGS[@]}")
  else
    if [[ -t 0 ]]; then
      local picked
      picked="$(prompt_for_targets "$canonical")"
      if [[ "$picked" == "none" ]]; then
        log_info "No targets selected — skipping link for $skill (canonical stays at $canonical)"
        return 0
      fi
      IFS=',' read -ra targets <<< "$picked"
    else
      log_info "No --to specified and no TTY — not linking $skill."
      log_info "Re-run with explicit targets, e.g.: $0 $skill --to codex --to claude"
      log_info "Canonical remains at: $canonical (no symlinks created)"
      return 0
    fi
  fi

  for key in "${targets[@]}"; do
    key="$(echo "$key" | tr '[:upper:]' '[:lower:]' | xargs)"
    [[ -z "$key" ]] && continue
    local base
    base="$(target_path_for "$key")"
    if [[ -z "$base" ]]; then
      log_warn "Unknown target '$key' — expected one of: agents, codex, claude, pi (skipping)"
      continue
    fi
    local link_path="$base/$skill"
    # Don't link to itself
    if [[ "$link_path" == "$canonical" ]]; then
      log_info "Skip $link_path — already canonical"
      continue
    fi
    mkdir -p "$base"
    if [[ -L "$link_path" ]]; then
      local cur
      cur="$(readlink "$link_path" 2>/dev/null || true)"
      if [[ "$cur" == "$canonical" ]]; then
        log_success "Already linked: $link_path -> $canonical"
        continue
      fi
      if [[ "$FORCE" == true ]]; then
        rm "$link_path"
        ln -s "$canonical" "$link_path"
        log_success "Re-linked: $link_path -> $canonical"
      else
        log_warn "Exists as symlink to different target: $link_path -> $cur (use --force to replace)"
      fi
      continue
    fi
    if [[ -e "$link_path" ]]; then
      if [[ "$FORCE" == true ]]; then
        local backup="$link_path.backup.$(date +%Y%m%d%H%M%S)"
        mv "$link_path" "$backup"
        log_warn "Backed up existing $link_path -> $backup"
        ln -s "$canonical" "$link_path"
        log_success "Linked: $link_path -> $canonical"
      else
        log_warn "Exists as real file/dir: $link_path (use --force to replace with symlink)"
      fi
      continue
    fi
    ln -s "$canonical" "$link_path"
    log_success "Linked: $link_path -> $canonical"
  done
}

# ---- arg parse ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --all) LINK_ALL=true; shift ;;
    --force|-f) FORCE=true; shift ;;
    --project-root) PROJECT_ROOT="$2"; shift 2 ;;
    --to) TO_ARGS+=("$2"); shift 2 ;;
    --) shift; break ;;
    -*) log_error "Unknown flag: $1"; usage; exit 1 ;;
    *) if [[ -z "$SKILL_NAME" ]]; then SKILL_NAME="$1"; else log_error "Unexpected arg: $1"; usage; exit 1; fi; shift ;;
  esac
done

PROJECT_ROOT="$(resolve_project_root)"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

if [[ "$LINK_ALL" == true ]]; then
  # Determine source dir: prefer project if it has skills, else global
  SRC=""
  if [[ -d "$PROJECT_ROOT/.agents/skills" ]]; then SRC="$PROJECT_ROOT/.agents/skills"; fi
  # If project empty and global has skills and user didn't specify project, also consider global?
  # For --all we only link from project by default; global --all is explicit via --project-root ~ or via single-skill calls.
  if [[ -z "$SRC" || ! -d "$SRC" ]]; then
    log_error "No .agents/skills found at $PROJECT_ROOT/.agents/skills"
    exit 1
  fi
  count=0
  for d in "$SRC"/*; do
    [[ -d "$d" ]] || continue
    [[ -f "$d/SKILL.md" ]] || { log_warn "Skip $(basename "$d") — no SKILL.md"; continue; }
    canon="$(find_canonical "$(basename "$d")" "$PROJECT_ROOT" 2>/dev/null || echo "$d")"
    link_one_skill "$(basename "$d")" "$canon"
    count=$((count+1))
  done
  log_success "Done — processed $count skill(s) from $SRC (only explicitly chosen targets were linked)"
  exit 0
fi

if [[ -z "$SKILL_NAME" ]]; then
  usage; exit 1
fi

if ! [[ "$SKILL_NAME" =~ ^[a-z0-9-]+$ ]] || [[ "$SKILL_NAME" == -* ]] || [[ "$SKILL_NAME" == *- ]] || [[ "$SKILL_NAME" == *--* ]]; then
  log_error "Skill name must be kebab-case (lowercase, digits, hyphens, no leading/trailing/double hyphens): $SKILL_NAME"
  exit 1
fi

CANONICAL="$(find_canonical "$SKILL_NAME" "$PROJECT_ROOT" 2>/dev/null || true)"
if [[ -z "$CANONICAL" ]]; then
  log_error "Skill not found in either $PROJECT_ROOT/.agents/skills/$SKILL_NAME or ~/.agents/skills/$SKILL_NAME"
  log_info  "Create it first (ask-first: .agents/skills/<name> or ~/.agents/skills/<name>), then re-run this linker after user confirms targets."
  exit 1
fi

link_one_skill "$SKILL_NAME" "$CANONICAL"
