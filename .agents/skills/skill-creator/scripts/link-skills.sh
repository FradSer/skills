#!/usr/bin/env bash
# Link a project-local skill into every agent runtime's skill directory.
# Canonical source: ./.agents/skills/<skill-name>  (git-tracked, project-local)
# Targets (symlinks): ~/.agents/skills, ~/.codex/skills, ~/.claude/skills, ~/.pi/agent/skills
#
# Usage:
#   ./skills/skill-creator/scripts/link-skills.sh <skill-name> [--project-root <path>] [--force]
#   ./skills/skill-creator/scripts/link-skills.sh --all   # link every skill under ./.agents/skills
#
# Upstream skill-creator defaults to ~/.agents/skills (global, untracked).
# This fork inverts that: project-local is canonical, global dirs are symlink views.
# ~/.claude/skills and ~/.pi/agent/skills contain per-skill symlinks to ~/.agents/skills
# on this host, but we still link them explicitly so a newly-created project skill is
# immediately visible to every runtime without relying on transitive discovery.

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
# SKILL_CREATOR_ROOT = .../skills/skill-creator ; REPO_ROOT = .../skills
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"

PROJECT_ROOT=""
FORCE=false
LINK_ALL=false
SKILL_NAME=""

usage() {
  cat <<EOF
${BLUE}link-skills.sh${NC} — project-first skill linker

${GREEN}Usage:${NC}
  $0 <skill-name> [--project-root <path>] [--force]
  $0 --all [--project-root <path>] [--force]

${GREEN}Options:${NC}
  --project-root <path>  Project root containing .agents/skills (default: git top-level or cwd)
  --force                Replace existing non-symlink directories with symlinks (backs up to .backup)
  --all                  Link every skill found under <project-root>/.agents/skills
  -h, --help             Show help

${GREEN}Behaviour:${NC}
  Canonical source must be: <project-root>/.agents/skills/<skill-name>/SKILL.md
  Targets symlinked (each is a per-skill symlink, not a directory symlink):
    - ~/.agents/skills/<skill-name>    -> canonical  (hub shared by several runtimes)
    - ~/.codex/skills/<skill-name>     -> canonical  (independent store)
    - ~/.claude/skills/<skill-name>    -> canonical  (Claude Code)
    - ~/.pi/agent/skills/<skill-name>  -> canonical  (Pi coding agent)

EOF
}

log_info()    { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
log_success() { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
log_warn()    { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
log_error()   { printf "${RED}[ERR]${NC} %s\n" "$1"; }

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

link_one_skill() {
  local skill="$1"
  local project_root="$2"
  local canonical="$project_root/.agents/skills/$skill"

  if [[ ! -f "$canonical/SKILL.md" ]]; then
    log_error "Canonical skill not found: $canonical/SKILL.md"
    log_info  "Expected layout: <project-root>/.agents/skills/<skill-name>/SKILL.md"
    log_info  "Create it first (see skill-creator SKILL.md) then re-run this script."
    return 1
  fi

  local targets=(
    "$HOME/.agents/skills/$skill"
    "$HOME/.codex/skills/$skill"
    "$HOME/.claude/skills/$skill"
    "$HOME/.pi/agent/skills/$skill"
  )

  for link_path in "${targets[@]}"; do
    local link_dir
    link_dir="$(dirname "$link_path")"

    mkdir -p "$link_dir"

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
    --) shift; break ;;
    -*) log_error "Unknown flag: $1"; usage; exit 1 ;;
    *) if [[ -z "$SKILL_NAME" ]]; then SKILL_NAME="$1"; else log_error "Unexpected arg: $1"; usage; exit 1; fi; shift ;;
  esac
done

PROJECT_ROOT="$(resolve_project_root)"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

if [[ "$LINK_ALL" == true ]]; then
  if [[ ! -d "$PROJECT_ROOT/.agents/skills" ]]; then
    log_error "No .agents/skills found at $PROJECT_ROOT/.agents/skills"
    exit 1
  fi
  count=0
  for d in "$PROJECT_ROOT"/.agents/skills/*; do
    [[ -d "$d" ]] || continue
    [[ -f "$d/SKILL.md" ]] || { log_warn "Skip $(basename "$d") — no SKILL.md"; continue; }
    link_one_skill "$(basename "$d")" "$PROJECT_ROOT"
    count=$((count+1))
  done
  log_success "Done — linked $count skill(s) from $PROJECT_ROOT/.agents/skills"
  exit 0
fi

if [[ -z "$SKILL_NAME" ]]; then
  usage; exit 1
fi

# Validate kebab-case (same rule as quick_validate.py)
if ! [[ "$SKILL_NAME" =~ ^[a-z0-9-]+$ ]] || [[ "$SKILL_NAME" == -* ]] || [[ "$SKILL_NAME" == *- ]] || [[ "$SKILL_NAME" == *--* ]]; then
  log_error "Skill name must be kebab-case (lowercase, digits, hyphens, no leading/trailing/double hyphens): $SKILL_NAME"
  exit 1
fi

link_one_skill "$SKILL_NAME" "$PROJECT_ROOT"
