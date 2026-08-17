#!/usr/bin/env bash
#
# Lark CLI Skills 同步脚本
# 从 lark-cli skills list 刷新 SKILL.md 路由索引与 SYNC.md 元数据
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
TARGET_DIR="$SCRIPT_DIR/.."
SYNC_MD="$TARGET_DIR/SYNC.md"
ROUTER_MD="$TARGET_DIR/SKILL.md"
GEN_INDEX_SCRIPT="$SCRIPT_DIR/../../../tools/skill-sync/gen-index.py"

show_help() {
    cat << EOF
${BLUE}Lark CLI Skills 同步脚本${NC}

${GREEN}用法:${NC}
    $0 [选项]

${GREEN}选项:${NC}
    -h, --help          显示此帮助信息
    -c, --check         检查本地 router 索引与当前 lark-cli 是否一致
    -f, --force         强制刷新,跳过确认

${GREEN}说明:${NC}
    上游 lark-cli 使用嵌入式 binary 管理 sub-skills (lark-cli skills read <name>)。
    本脚本调用 'lark-cli skills list' 重新生成 SKILL.md 路由表并更新 SYNC.md 元数据。

EOF
}

log_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

log_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

log_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}

update_sync_md_field() {
    local file="$1" key="$2" value="$3"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^\*\*$key\*\*: .*|**$key**: $value|" "$file"
    else
        sed -i "s|^\*\*$key\*\*: .*|**$key**: $value|" "$file"
    fi
}

check_requirements() {
    local missing=()
    for tool in lark-cli python3; do
        if ! command -v "$tool" &>/dev/null; then
            missing+=("$tool")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing[*]}"
        exit 1
    fi
}

cleanup_obsolete_subdirs() {
    # 确保没有遗留的本地子 skill 目录
    find "$TARGET_DIR" -maxdepth 1 -mindepth 1 -type d -name "lark-*" -exec rm -rf {} + 2>/dev/null || true
    rm -rf "$TARGET_DIR/.backup" 2>/dev/null || true
}

main() {
    local check_only=false
    local force_sync=false

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
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    check_requirements

    if [ ! -f "$GEN_INDEX_SCRIPT" ]; then
        log_error "未找到 gen-index.py: $GEN_INDEX_SCRIPT"
        exit 1
    fi

    if [ "$check_only" = true ]; then
        log_info "检查 router 索引与当前 lark-cli 一致性..."
        if python3 "$GEN_INDEX_SCRIPT" --from-cli --router "$ROUTER_MD" --hoist lark-shared --check; then
            log_success "Router 索引与已安装 lark-cli 一致"
            exit 0
        else
            log_warning "Router 索引需要更新，请运行 $0"
            exit 1
        fi
    fi

    log_info "正在从 lark-cli skills list 刷新 SKILL.md 路由索引..."
    python3 "$GEN_INDEX_SCRIPT" --from-cli --router "$ROUTER_MD" --hoist lark-shared

    cleanup_obsolete_subdirs

    if [ -f "$SYNC_MD" ]; then
        local today lark_ver
        today=$(date +%Y-%m-%d)
        lark_ver=$(lark-cli --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "unknown")
        update_sync_md_field "$SYNC_MD" "Last sync" "$today"
        update_sync_md_field "$SYNC_MD" "lark-cli version" "$lark_ver"
        log_info "已更新 SYNC.md (date=$today, lark-cli=$lark_ver)"
    fi

    log_success "Router 索引与元数据同步完成"
}

main "$@"
