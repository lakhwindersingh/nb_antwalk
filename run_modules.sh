#!/usr/bin/env bash
# ==============================================================================
# Personal OS & Percipience Cargo Workspace Module Runner
# Supports building, testing, linting, installing, and running all 7 Cargo modules:
# - pos_core
# - pos_orchestrator
# - pos_thoughts
# - pos_email
# - pos_triage
# - pos_server
# - pos_cli
# ==============================================================================

set -eo pipefail

# Locate repository root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/../Cargo.toml" ]]; then
    REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
elif [[ -f "${SCRIPT_DIR}/../../Cargo.toml" ]]; then
    REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
elif [[ -f "${SCRIPT_DIR}/Cargo.toml" ]]; then
    REPO_ROOT="${SCRIPT_DIR}"
else
    REPO_ROOT="$(pwd)"
fi

cd "${REPO_ROOT}"

# Color codes for terminal output
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
MAGENTA="\033[0;35m"
NC="\033[0m" # No Color

# Workspace Modules List
MODULES=(
    "pos_core"
    "pos_orchestrator"
    "pos_thoughts"
    "pos_email"
    "pos_triage"
    "pos_server"
    "pos_cli"
)

function print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "  ================================================================"
    echo "    PERSONAL OS • CARGO WORKSPACE MODULE RUNNER (v1.2.0)"
    echo "    Quad-Space Enclave • 7 Integrated Micro-Crates"
    echo "  ================================================================"
    echo -e "${NC}"
}

function print_usage() {
    print_banner
    echo -e "${BOLD}Usage:${NC} ./run_modules.sh <command> [arguments...]"
    echo ""
    echo -e "${BOLD}Commands:${NC}"
    echo -e "  ${GREEN}test${NC}                Run tests across all 7 workspace crates"
    echo -e "  ${GREEN}test-module <name>${NC}  Run tests for a specific module (e.g. pos_core)"
    echo -e "  ${GREEN}build${NC}               Build all workspace crates in debug mode"
    echo -e "  ${GREEN}build-release${NC}       Build all workspace crates in release mode"
    echo -e "  ${GREEN}install [target]${NC}    Install binaries to ~/.cargo/bin (cli, server, or all)"
    echo -e "                      Example: ./run_modules.sh install"
    echo -e "  ${GREEN}check${NC}               Fast syntax & type checking (cargo check --workspace)"
    echo -e "  ${GREEN}cli [subcommand]${NC}    Execute Personal OS CLI binary ('pos')"
    echo -e "                      Aliases: ./run_modules.sh pos [subcommand]"
    echo -e "                      Examples: cli status, pos doctor, pos thought search"
    echo -e "  ${GREEN}server${NC}              Launch Personal OS API daemon & MCP server"
    echo -e "                      Alias: ./run_modules.sh pos_server"
    echo -e "  ${GREEN}mcp-http [url]${NC}      Stdio-to-HTTP JSON-RPC bridge for MCP consumers"
    echo -e "                      Defaults to http://127.0.0.1:8080/mcp"
    echo -e "  ${GREEN}portal${NC}              Launch Enterprise Observability Hub Web Gateway"
    echo -e "  ${GREEN}gate${NC}                Run Percipience PR Verification Gate (7 stages)"
    echo -e "  ${GREEN}audit${NC}               Run Percipience Merkle state audit & maturity check"
    echo -e "  ${GREEN}clean${NC}               Clean target build artifacts"
    echo -e "  ${GREEN}list${NC}                List all 7 registered modules and recovery points"
    echo -e "  ${GREEN}help${NC}                Show this guidance screen"
    echo ""
    echo -e "${BOLD}Cargo Run Shortcuts:${NC}"
    echo -e "  To run via Cargo directly, pass ${CYAN}--bin <name>${NC} or ${CYAN}-p <package>${NC}:"
    echo -e "    ${CYAN}cargo run --bin pos -- status${NC}       or  ${CYAN}cargo run -p pos_cli -- status${NC}"
    echo -e "    ${CYAN}cargo run --bin pos_server${NC}          or  ${CYAN}cargo run -p pos_server${NC}"
    echo -e "  Bare ${CYAN}cargo run${NC} defaults to ${CYAN}pos${NC} (configured via default-members)."
    echo ""
}

function cmd_list() {
    echo -e "${BOLD}Registered Cargo Modules in Workspace:${NC}"
    echo -e "  ${BLUE}1. pos_core${NC}         [RP_CORE_001]   - SQLite WAL, FTS5, Zero-Knowledge Vault, Privacy Redaction"
    echo -e "  ${BLUE}2. pos_orchestrator${NC} [RP_ORCH_001]   - Meta-Orchestrator Semantic Intent Classifier & Router"
    echo -e "  ${BLUE}3. pos_thoughts${NC}     [RP_THOUGHT_001] - CommonMark Wikilinks, Task Graphs, Ambiguity Scorer"
    echo -e "  ${BLUE}4. pos_email${NC}        [RP_EMAIL_001]   - IMAP/OAuth2 Synchronization & SQLite Message Store"
    echo -e "  ${BLUE}5. pos_triage${NC}       [RP_TRIAGE_001]  - Zero-Shot Category Classifier & Action Extractor"
    echo -e "  ${BLUE}6. pos_server${NC}       [RP_SERVER_001]  - 12 Consolidated Action-Based MCP Tools & REST Daemon"
    echo -e "  ${BLUE}7. pos_cli${NC}          [RP_CLI_001]     - Canonical Clap v4 Terminal Binary ('pos')"
    echo ""
}

function cmd_test() {
    echo -e "${GREEN}${BOLD}🚀 Running unit & integration tests across all 7 modules...${NC}"
    cargo test --workspace -- --nocapture
    echo -e "\n${GREEN}✅ All workspace tests passed successfully!${NC}"
}

function cmd_test_module() {
    local target="$1"
    if [[ -z "$target" ]]; then
        echo -e "${RED}Error: Missing module name.${NC}"
        echo "Available modules: ${MODULES[*]}"
        exit 1
    fi

    local found=false
    for m in "${MODULES[@]}"; do
        if [[ "$m" == "$target" ]]; then
            found=true
            break
        fi
    done

    if [[ "$found" == false ]]; then
        echo -e "${RED}Error: Unknown module '${target}'.${NC}"
        echo "Available modules: ${MODULES[*]}"
        exit 1
    fi

    echo -e "${GREEN}${BOLD}🧪 Running tests for module: ${target}...${NC}"
    cargo test -p "${target}" -- --nocapture
    echo -e "\n${GREEN}✅ Module ${target} tests passed!${NC}"
}

function cmd_build() {
    echo -e "${BLUE}${BOLD}🔨 Building Cargo workspace (debug mode)...${NC}"
    cargo build --workspace
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
}

function cmd_build_release() {
    echo -e "${MAGENTA}${BOLD}🚀 Building Cargo workspace (release mode optimized)...${NC}"
    cargo build --workspace --release
    echo -e "${GREEN}✅ Release build completed successfully!${NC}"
}

function cmd_install() {
    local target="${1:-all}"
    case "${target}" in
        all|"")
            echo -e "${GREEN}${BOLD}📦 Installing Personal OS binaries ('pos' CLI & 'pos_server') to ~/.cargo/bin...${NC}"
            cargo install --path workplace/modules/pos_cli --force
            cargo install --path workplace/modules/pos_server --force
            echo -e "\n${GREEN}✅ Successfully installed 'pos' and 'pos_server' to ~/.cargo/bin!${NC}"
            ;;
        cli|pos|pos_cli)
            echo -e "${GREEN}${BOLD}📦 Installing Personal OS CLI ('pos') to ~/.cargo/bin...${NC}"
            cargo install --path workplace/modules/pos_cli --force
            echo -e "\n${GREEN}✅ Successfully installed 'pos' to ~/.cargo/bin!${NC}"
            ;;
        server|pos_server)
            echo -e "${GREEN}${BOLD}📦 Installing Personal OS Daemon ('pos_server') to ~/.cargo/bin...${NC}"
            cargo install --path workplace/modules/pos_server --force
            echo -e "\n${GREEN}✅ Successfully installed 'pos_server' to ~/.cargo/bin!${NC}"
            ;;
        *)
            echo -e "${RED}Error: Unknown install target '${target}'.${NC}"
            echo "Valid targets: all (default), cli (pos), server (pos_server)"
            exit 1
            ;;
    esac
}

function cmd_check() {
    echo -e "${CYAN}${BOLD}🔍 Checking workspace syntax and types...${NC}"
    cargo check --workspace
    echo -e "${GREEN}✅ All crates checked without compiler errors!${NC}"
}

function cmd_cli() {
    shift || true
    echo -e "${CYAN}${BOLD}▶ Executing Personal OS CLI ('pos')...${NC}"
    if [[ $# -eq 0 ]]; then
        cargo run --bin pos -- --help
    else
        cargo run --bin pos -- "$@"
    fi
}

function cmd_server() {
    shift || true
    echo -e "${MAGENTA}${BOLD}🌐 Starting Personal OS API Daemon & MCP Server...${NC}" >&2
    if [[ -x "${REPO_ROOT}/target/debug/pos_server" ]]; then
        exec "${REPO_ROOT}/target/debug/pos_server" "$@"
    else
        exec cargo run --quiet -p pos_server -- "$@"
    fi
}

function cmd_bridge() {
    local target_url="${1:-http://127.0.0.1:8080/mcp}"
    python3 -c '
import sys, json, urllib.request

target = sys.argv[1]
buffer = ""
for line in sys.stdin:
    buffer += line
    try:
        data = json.loads(buffer)
        req = urllib.request.Request(target, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            sys.stdout.write(resp.read().decode("utf-8") + "\n")
            sys.stdout.flush()
        buffer = ""
    except json.JSONDecodeError:
        continue
' "${target_url}"
}

function cmd_portal() {
    echo -e "${CYAN}${BOLD}🚀 Starting Percipience Observability Hub Web Gateway...${NC}"
    python3 workplace/portal/server.py 8088
}

function cmd_gate() {
    echo -e "${YELLOW}${BOLD}🚥 Triggering Percipience PR Gatekeeper Verification...${NC}"
    ./.nb/bin/percipience gate
}

function cmd_audit() {
    echo -e "${YELLOW}${BOLD}🛡️ Triggering Percipience Merkle Continuity & Maturity Audit...${NC}"
    ./.nb/bin/percipience audit
}

function cmd_clean() {
    echo -e "${RED}${BOLD}🧹 Cleaning build artifacts...${NC}"
    cargo clean
    echo -e "${GREEN}✅ Clean completed.${NC}"
}

# Command Dispatcher
COMMAND="${1:-help}"

case "${COMMAND}" in
    test)
        cmd_test
        ;;
    test-module)
        cmd_test_module "$2"
        ;;
    build)
        cmd_build
        ;;
    build-release)
        cmd_build_release
        ;;
    install)
        cmd_install "$2"
        ;;
    check)
        cmd_check
        ;;
    cli|pos|pos_cli)
        cmd_cli "$@"
        ;;
    server|pos_server)
        cmd_server "$@"
        ;;
    bridge|mcp-http|mcp-bridge)
        cmd_bridge "$2"
        ;;
    portal)
        cmd_portal
        ;;
    gate)
        cmd_gate
        ;;
    audit)
        cmd_audit
        ;;
    clean)
        cmd_clean
        ;;
    list)
        cmd_list
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: ${COMMAND}${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
