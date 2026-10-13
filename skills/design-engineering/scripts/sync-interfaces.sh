#!/usr/bin/env bash
#
# Interfaces Skills 同步脚本
# 从 jakubkrehel/skills 与 emilkowalski/skills 重建 design-engineering 的派生参考树
#
# The local router SKILL.md, README.md, SYNC.md, agents/ and scripts/ are preserved;
# every other file under skills/design-engineering/ is derived.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
UPSTREAM_REPO="https://github.com/jakubkrehel/skills.git"
UPSTREAM_BRANCH="main"
UPSTREAM_PATH="skills"
# 本地路由器 skill 目录（本地自有 SKILL.md；references/ 派生内容整树重建）
ROUTER="design-engineering"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
TARGET_DIR="$SCRIPT_DIR/.."
GENERATOR="$SCRIPT_DIR/../../../tools/skill-sync/interfaces.py"
BACKUP_DIR="$SCRIPT_DIR/../../../.backup/interfaces"
TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/skills-interfaces-sync.XXXXXX")"

# 本地保留的顶层条目（不被覆盖）
LOCAL_ENTRIES=("SKILL.md" "README.md" "SYNC.md" "agents" "scripts")

log_info()    { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
log_success() { printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"; }
log_warning() { printf "${YELLOW}[WARNING]${NC} %s\n" "$1"; }
log_error()   { printf "${RED}[ERROR]${NC} %s\n" "$1"; }

# 原地更新 SYNC.md 中 **Key**: value 形式的字段
update_sync_md_field() {
    local file="$1" key="$2" value="$3"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^\*\*$key\*\*: .*|**$key**: $value|" "$file"
    else
        sed -i "s|^\*\*$key\*\*: .*|**$key**: $value|" "$file"
    fi
}

check_requirements() {
    local missing_tools=()
    for tool in git diff uv; do
        command -v "$tool" >/dev/null 2>&1 || missing_tools+=("$tool")
    done
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
        exit 1
    fi
}

cleanup() {
    [ -d "$TEMP_DIR" ] && rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# 克隆上游 skills 目录（sparse checkout）
clone_upstream() {
    log_info "正在从上游仓库获取 skills 目录..."

    mkdir -p "$TEMP_DIR"
    git clone --depth 1 --filter=blob:none --sparse --branch "$UPSTREAM_BRANCH" \
        "$UPSTREAM_REPO" "$TEMP_DIR/repo" 2>/dev/null
    git -C "$TEMP_DIR/repo" sparse-checkout set --skip-checks "$UPSTREAM_PATH" 2>/dev/null

    if [ ! -d "$TEMP_DIR/repo/$UPSTREAM_PATH" ]; then
        log_error "上游仓库中未找到 $UPSTREAM_PATH 目录"
        return 1
    fi

    git clone --depth 1 --filter=blob:none --sparse --branch main \
        "https://github.com/emilkowalski/skills.git" "$TEMP_DIR/emil" 2>/dev/null
    git -C "$TEMP_DIR/emil" sparse-checkout set --skip-checks skills 2>/dev/null
    log_success "上游文件获取完成"
    return 0
}

# 创建备份
create_backup() {
    if [ ! -d "$TARGET_DIR" ]; then
        log_info "参考树不存在,跳过备份"
        return 0
    fi

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$BACKUP_DIR"
    local backup_path
    backup_path=$(mktemp -d "$BACKUP_DIR/$timestamp.XXXXXX")
    cp -R "$TARGET_DIR" "$backup_path/$ROUTER"
    log_success "已备份参考树到: $backup_path"
}

# 判断顶层条目是否为本地自有内容
is_local_entry() {
    local name="$1"
    local entry
    for entry in "${LOCAL_ENTRIES[@]}"; do
        [ "$name" = "$entry" ] && return 0
    done
    return 1
}

# Build a complete candidate before comparing or touching installed content.
check_diff() {
    local upstream_skills="$TEMP_DIR/repo/$UPSTREAM_PATH"
    local has_changes=false
    local new_count=0 changed_count=0 deleted_count=0

    log_info "检查文件差异..."

    local compare_dir="$TEMP_DIR/refpacked"
    uv run --no-project --with pyyaml python "$GENERATOR" "$upstream_skills" "$compare_dir" --emil "$TEMP_DIR/emil/skills" || return 2

    local candidate_dir="$compare_dir/$ROUTER"
    if [ ! -d "$candidate_dir" ]; then
        log_error "生成的上游候选缺少 $ROUTER 目录"
        return 2
    fi

    # 检查新增和变更的文件
    while IFS= read -r -d '' upstream_file; do
        local rel_path="${upstream_file#"$candidate_dir"/}"
        local local_file="$TARGET_DIR/$rel_path"

        if [ ! -f "$local_file" ]; then
            new_count=$((new_count + 1))
            has_changes=true
        elif ! diff -q "$local_file" "$upstream_file" >/dev/null 2>&1; then
            changed_count=$((changed_count + 1))
            has_changes=true
        fi
    done < <(find "$candidate_dir" -type f -print0)

    # 检查本地已删除的上游文件（本地自有内容除外）
    while IFS= read -r -d '' local_file; do
        local rel_path="${local_file#"$TARGET_DIR"/}"
        local top="${rel_path%%/*}"
        is_local_entry "$top" && continue

        if [ ! -f "$candidate_dir/$rel_path" ]; then
            deleted_count=$((deleted_count + 1))
            has_changes=true
        fi
    done < <(find "$TARGET_DIR" -type f -print0)

    if [ "$has_changes" = true ]; then
        [ $new_count -gt 0 ]      && log_info "  新增: $new_count 个文件"
        [ $changed_count -gt 0 ] && log_info "  变更: $changed_count 个文件"
        [ $deleted_count -gt 0 ] && log_info "  删除: $deleted_count 个文件(上游已移除)"
        return 1
    else
        log_success "所有文件已是最新版本"
        return 0
    fi
}

# 执行同步
sync_files() {
    local no_backup="$1"

    if [ "$no_backup" != "true" ]; then
        create_backup
    fi

    log_info "正在同步文件..."

    # 删除旧的派生内容（保留本地自有条目）
    while IFS= read -r -d '' item; do
        local basename
        basename=$(basename "$item")
        is_local_entry "$basename" && continue
        rm -rf "$item"
    done < <(find "$TARGET_DIR" -maxdepth 1 -mindepth 1 -print0)

    # 复制新的候选树
    cp -R "$TEMP_DIR/refpacked/$ROUTER/." "$TARGET_DIR/"

    # 更新 SYNC.md 元数据：同步日期 / 上游分支 / 同步到的 commit
    local sync_md="$TARGET_DIR/SYNC.md"
    if [ -f "$sync_md" ]; then
        local synced_commit today
        today=$(date +%Y-%m-%d)
        synced_commit=$(git -C "$TEMP_DIR/repo" rev-parse --short HEAD 2>/dev/null || echo "unknown")
        update_sync_md_field "$sync_md" "Last sync" "$today"
        update_sync_md_field "$sync_md" "Synced commit" "$synced_commit"
        update_sync_md_field "$sync_md" "Emil synced commit" "$(git -C "$TEMP_DIR/emil" rev-parse HEAD)"
        log_info "已更新 SYNC.md (date=$today, commit=$synced_commit)"
    fi
}

show_help() {
    cat << EOF
${BLUE}Design Engineering Skills 同步脚本${NC}

${GREEN}用法:${NC}
    $0 [选项]

${GREEN}选项:${NC}
    -h, --help          显示此帮助信息
    -c, --check         仅检查是否有更新,不执行同步
    -f, --force         强制同步,跳过确认
    --no-backup         同步时不创建备份

${GREEN}示例:${NC}
    $0                  # 同步并备份现有文件
    $0 --check          # 仅检查更新
    $0 --force          # 强制同步,跳过确认

${GREEN}上游仓库:${NC}
    $UPSTREAM_REPO (branch: $UPSTREAM_BRANCH, path: $UPSTREAM_PATH)
    https://github.com/emilkowalski/skills (branch: main, path: skills)

${GREEN}本地变换:${NC}
    仅 design-engineering 可发现；全部上游能力保留为参考流程

EOF
}

main() {
    local check_only=false
    local force_sync=false
    local no_backup=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            -f|--force)
                force_sync=true
                shift
                ;;
            --no-backup)
                no_backup=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "开始同步 Design Engineering skills..."

    check_requirements
    clone_upstream

    local has_diff=0
    check_diff || has_diff=$?
    if [ "$has_diff" -gt 1 ]; then
        log_error "生成上游候选失败,本地内容未修改"
        exit "$has_diff"
    fi

    if [ "$check_only" = true ]; then
        if [ $has_diff -eq 0 ]; then
            log_success "没有更新"
            exit 0
        else
            log_info "有更新可用,运行 $0 进行同步"
            exit 1
        fi
    fi

    if [ $has_diff -eq 0 ] && [ "$force_sync" != true ]; then
        exit 0
    fi

    if [ "$force_sync" != true ] && [ -t 0 ]; then
        echo -n "是否继续同步? [y/N] "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "取消同步"
            exit 0
        fi
    fi

    sync_files "$no_backup"

    log_success "同步完成!"
    log_info "建议执行以下命令提交更改:"
    echo ""
    echo "    git add skills/design-engineering/"
    echo ""
}

main "$@"
