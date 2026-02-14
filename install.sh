#!/usr/bin/env bash
# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# PyFly Framework Installer
# Usage:
#   Interactive:     bash install.sh
#   Via curl:        curl -fsSL https://raw.githubusercontent.com/fireflyframework/pyfly/main/install.sh | bash
#   Via get.pyfly:   curl -fsSL https://get.pyfly.io/ | bash
#   Uninstall:       bash install.sh --uninstall
#   Custom dir:      PYFLY_HOME=/opt/pyfly bash install.sh
#   Custom extras:   PYFLY_EXTRAS=web,data bash install.sh

set -euo pipefail

# ── Constants ──────────────────────────────────────────────────────────────────

PYFLY_VERSION="0.1.0"
PYFLY_REPO="https://github.com/fireflyframework/pyfly.git"
DEFAULT_INSTALL_DIR="$HOME/.pyfly"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=12

# ── Color support ──────────────────────────────────────────────────────────────

# Enable colors when output is a terminal
if [ -t 1 ]; then
    BOLD="\033[1m"
    DIM="\033[2m"
    RED="\033[31m"
    GREEN="\033[32m"
    YELLOW="\033[33m"
    CYAN="\033[36m"
    MAGENTA="\033[35m"
    RESET="\033[0m"
else
    BOLD="" DIM="" RED="" GREEN="" YELLOW="" CYAN="" MAGENTA="" RESET=""
fi

# Interactive detection: works both for direct execution AND curl-piped mode.
# When piped via curl, stdin is the script — but /dev/tty is the user's terminal.
if [ -t 0 ]; then
    IS_INTERACTIVE=true
    TTY_IN="/dev/stdin"
elif [ -t 1 ] && [ -e /dev/tty ]; then
    # curl | bash mode — stdout is a terminal, stdin is the pipe, but /dev/tty works
    IS_INTERACTIVE=true
    TTY_IN="/dev/tty"
else
    IS_INTERACTIVE=false
    TTY_IN="/dev/null"
fi

# ── Helper functions ───────────────────────────────────────────────────────────

info()    { printf "${CYAN}[INFO]${RESET}  %s\n" "$1"; }
success() { printf "${GREEN}[OK]${RESET}    %s\n" "$1"; }
warn()    { printf "${YELLOW}[WARN]${RESET}  %s\n" "$1"; }
error()   { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; }
fatal()   { error "$1"; exit 1; }

# Read a line from the user, even when piped via curl
prompt_read() {
    read -r "$@" < "$TTY_IN"
}

banner() {
    printf "${MAGENTA}"
    cat << 'BANNER'
    ____        ________
   / __ \__  __/ ____/ /_  __
  / /_/ / / / / /_  / / / / /
 / ____/ /_/ / __/ / / /_/ /
/_/    \__, /_/   /_/\__, /
      /____/        /____/
BANNER
    printf "${RESET}"
    printf "  ${DIM}:: PyFly Framework Installer :: (v%s)${RESET}\n" "$PYFLY_VERSION"
    printf "  ${DIM}Copyright 2026 Firefly Software Solutions Inc. | Apache 2.0 License${RESET}\n\n"
}

# ── Uninstall ─────────────────────────────────────────────────────────────────

uninstall_pyfly() {
    banner

    local install_dir="${PYFLY_HOME:-$DEFAULT_INSTALL_DIR}"
    install_dir="${install_dir/#\~/$HOME}"

    if [ ! -d "$install_dir" ]; then
        info "PyFly is not installed at $install_dir"
        exit 0
    fi

    info "Found PyFly installation at: $install_dir"

    if [ "$IS_INTERACTIVE" = true ]; then
        printf "\n${BOLD}Remove PyFly installation at %s?${RESET} ${DIM}[y/N]${RESET}: " "$install_dir"
        prompt_read confirm
        case "${confirm:-N}" in
            [Yy]*) ;;
            *) info "Uninstall cancelled."; exit 0 ;;
        esac
    fi

    info "Removing $install_dir ..."
    rm -rf "$install_dir"
    success "PyFly installation removed"

    # Clean up PATH entries from shell profiles
    local cleaned=false
    for profile in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.config/fish/config.fish"; do
        if [ -f "$profile" ] && grep -q "pyfly" "$profile" 2>/dev/null; then
            # Remove lines containing "# PyFly Framework" and the PATH export that follows
            local tmp
            tmp=$(mktemp)
            grep -v "# PyFly Framework" "$profile" | grep -v "$install_dir/bin" > "$tmp" || true
            mv "$tmp" "$profile"
            cleaned=true
            success "Cleaned PATH entry from $profile"
        fi
    done

    if [ "$cleaned" = false ]; then
        info "No PATH entries to clean up"
    fi

    printf "\n${GREEN}${BOLD}PyFly has been uninstalled.${RESET}\n\n"
    exit 0
}

# ── Prerequisite checks ───────────────────────────────────────────────────────

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local version
            version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            local major minor
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge "$MIN_PYTHON_MAJOR" ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ]; then
                PYTHON_CMD="$cmd"
                PYTHON_VERSION="$version"
                return 0
            fi
        fi
    done
    return 1
}

check_prerequisites() {
    info "Checking prerequisites..."

    if find_python; then
        success "Python $PYTHON_VERSION found ($PYTHON_CMD)"
    else
        fatal "Python >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} is required. Please install it first."
    fi

    if "$PYTHON_CMD" -c "import venv" &>/dev/null; then
        success "venv module available"
    else
        fatal "Python venv module is required. Install it with: sudo apt install python3-venv (Debian/Ubuntu)"
    fi

    if "$PYTHON_CMD" -m pip --version &>/dev/null; then
        success "pip available"
    else
        fatal "pip is required. Install it with: $PYTHON_CMD -m ensurepip --upgrade"
    fi

    if command -v git &>/dev/null; then
        success "git available"
    else
        warn "git not found. Some features may be limited."
    fi
}

# ── Interactive prompts ────────────────────────────────────────────────────────

prompt_install_dir() {
    if [ "$IS_INTERACTIVE" = true ] && [ -z "${PYFLY_HOME:-}" ]; then
        printf "\n${BOLD}Installation directory${RESET} ${DIM}[%s]${RESET}: " "$DEFAULT_INSTALL_DIR"
        prompt_read user_dir
        INSTALL_DIR="${user_dir:-$DEFAULT_INSTALL_DIR}"
    else
        INSTALL_DIR="${PYFLY_HOME:-$DEFAULT_INSTALL_DIR}"
    fi
    INSTALL_DIR="${INSTALL_DIR/#\~/$HOME}"
    info "Install directory: $INSTALL_DIR"
}

prompt_extras() {
    if [ "$IS_INTERACTIVE" = true ] && [ -z "${PYFLY_EXTRAS:-}" ]; then
        printf "\n${BOLD}Available extras:${RESET}\n"
        printf "  ${CYAN}1${RESET}) full      — All modules (recommended)\n"
        printf "  ${CYAN}2${RESET}) web       — Web framework (Starlette, uvicorn)\n"
        printf "  ${CYAN}3${RESET}) data      — Database (SQLAlchemy, Alembic)\n"
        printf "  ${CYAN}4${RESET}) eda       — Event-Driven (Kafka, RabbitMQ)\n"
        printf "  ${CYAN}5${RESET}) security  — Auth & JWT\n"
        printf "  ${CYAN}6${RESET}) custom    — Enter comma-separated extras\n"
        printf "\n${BOLD}Select extras${RESET} ${DIM}[1]${RESET}: "
        prompt_read choice
        case "${choice:-1}" in
            1) EXTRAS="full" ;;
            2) EXTRAS="web" ;;
            3) EXTRAS="data" ;;
            4) EXTRAS="eda" ;;
            5) EXTRAS="security" ;;
            6)
                printf "${BOLD}Enter extras${RESET} ${DIM}(comma-separated, e.g. web,data,security)${RESET}: "
                prompt_read custom_extras
                EXTRAS="${custom_extras:-full}"
                ;;
            *) EXTRAS="full" ;;
        esac
    else
        EXTRAS="${PYFLY_EXTRAS:-full}"
    fi
    info "Selected extras: $EXTRAS"
}

prompt_add_to_path() {
    ADD_TO_PATH=false
    if [ "$IS_INTERACTIVE" = true ]; then
        printf "\n${BOLD}Add pyfly to PATH?${RESET} ${DIM}[Y/n]${RESET}: "
        prompt_read add_path
        case "${add_path:-Y}" in
            [Yy]*) ADD_TO_PATH=true ;;
            *) ADD_TO_PATH=false ;;
        esac
    else
        ADD_TO_PATH=true
    fi
}

# ── Installation ───────────────────────────────────────────────────────────────

detect_source_dir() {
    # If this script is in a pyfly source directory, use it
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/pyproject.toml" ] && grep -q 'name = "pyfly"' "$SCRIPT_DIR/pyproject.toml" 2>/dev/null; then
        SOURCE_DIR="$SCRIPT_DIR"
        info "Source detected at: $SOURCE_DIR"
        return 0
    fi

    # If PYFLY_SOURCE is set, use it
    if [ -n "${PYFLY_SOURCE:-}" ] && [ -d "$PYFLY_SOURCE" ]; then
        SOURCE_DIR="$PYFLY_SOURCE"
        info "Source from PYFLY_SOURCE: $SOURCE_DIR"
        return 0
    fi

    # No local source — clone from GitHub (curl | bash mode)
    if ! command -v git &>/dev/null; then
        fatal "git is required to install PyFly via curl. Please install git first."
    fi
    info "Cloning PyFly from $PYFLY_REPO ..."
    SOURCE_DIR="$(mktemp -d)/pyfly"
    git clone --depth 1 "$PYFLY_REPO" "$SOURCE_DIR" --quiet
    success "Cloned PyFly source"
}

install_pyfly() {
    info "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"

    # Copy source
    info "Copying PyFly source..."
    if [ "$SOURCE_DIR" != "$INSTALL_DIR/source" ]; then
        rm -rf "$INSTALL_DIR/source"
        cp -r "$SOURCE_DIR" "$INSTALL_DIR/source"
        rm -rf "$INSTALL_DIR/source/.worktrees" \
               "$INSTALL_DIR/source/.venv" \
               "$INSTALL_DIR/source/.pytest_cache" \
               "$INSTALL_DIR/source/.mypy_cache" \
               "$INSTALL_DIR/source/.ruff_cache" \
               "$INSTALL_DIR/source/htmlcov" \
               "$INSTALL_DIR/source/.coverage"
    fi
    success "Source copied"

    # Create virtual environment
    info "Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$INSTALL_DIR/venv"
    success "Virtual environment created"

    # Install PyFly
    local pip_cmd="$INSTALL_DIR/venv/bin/pip"
    info "Installing PyFly with extras: $EXTRAS ..."
    "$pip_cmd" install --upgrade pip --quiet

    local extras_str
    extras_str=$(echo "$EXTRAS" | tr ',' ',')
    "$pip_cmd" install -e "$INSTALL_DIR/source[$extras_str]" --quiet
    success "PyFly installed successfully"

    # Create wrapper script
    info "Creating pyfly wrapper..."
    mkdir -p "$INSTALL_DIR/bin"
    cat > "$INSTALL_DIR/bin/pyfly" << WRAPPER
#!/usr/bin/env bash
# PyFly CLI wrapper — activates the venv and runs pyfly
exec "$INSTALL_DIR/venv/bin/pyfly" "\$@"
WRAPPER
    chmod +x "$INSTALL_DIR/bin/pyfly"
    success "Wrapper created at: $INSTALL_DIR/bin/pyfly"
}

configure_path() {
    if [ "$ADD_TO_PATH" = false ]; then
        return
    fi

    local bin_dir="$INSTALL_DIR/bin"

    local shell_profile=""
    local path_line=""
    case "${SHELL:-/bin/bash}" in
        */zsh)  shell_profile="$HOME/.zshrc" ;;
        */bash)
            if [ -f "$HOME/.bash_profile" ]; then
                shell_profile="$HOME/.bash_profile"
            else
                shell_profile="$HOME/.bashrc"
            fi
            ;;
        */fish)
            shell_profile="$HOME/.config/fish/config.fish"
            ;;
        *)  shell_profile="$HOME/.profile" ;;
    esac

    if echo "$PATH" | tr ':' '\n' | grep -q "^${bin_dir}$"; then
        info "pyfly is already in PATH"
        return
    fi

    if [ -n "$shell_profile" ]; then
        if ! grep -q "$bin_dir" "$shell_profile" 2>/dev/null; then
            case "${SHELL:-/bin/bash}" in
                */fish) path_line="set -gx PATH $bin_dir \$PATH" ;;
                *)      path_line="export PATH=\"$bin_dir:\$PATH\"" ;;
            esac
            {
                echo ""
                echo "# PyFly Framework"
                echo "$path_line"
            } >> "$shell_profile"
            success "Added pyfly to PATH in $shell_profile"
            info "Run 'source $shell_profile' or open a new terminal to use pyfly"
        else
            info "pyfly PATH entry already exists in $shell_profile"
        fi
    fi
}

print_summary() {
    printf "\n"
    printf "${GREEN}${BOLD}Installation complete!${RESET}\n\n"
    printf "  ${BOLD}Installation:${RESET}  %s\n" "$INSTALL_DIR"
    printf "  ${BOLD}PyFly binary:${RESET}  %s/bin/pyfly\n" "$INSTALL_DIR"
    printf "  ${BOLD}Extras:${RESET}        %s\n" "$EXTRAS"
    printf "  ${BOLD}Python:${RESET}        %s\n" "$PYTHON_VERSION"
    printf "\n"
    printf "  ${BOLD}Get started:${RESET}\n"
    printf "    ${CYAN}pyfly --help${RESET}         Show available commands\n"
    printf "    ${CYAN}pyfly new my-app${RESET}     Create a new project\n"
    printf "    ${CYAN}pyfly doctor${RESET}         Check your environment\n"
    printf "    ${CYAN}pyfly info${RESET}           Show framework info\n"
    printf "\n"
    printf "  ${BOLD}Uninstall:${RESET}\n"
    printf "    ${CYAN}bash install.sh --uninstall${RESET}\n"
    printf "\n"
}

# ── Cleanup on failure ─────────────────────────────────────────────────────────

cleanup_on_failure() {
    if [ -n "${INSTALL_DIR:-}" ] && [ -d "$INSTALL_DIR" ]; then
        warn "Installation failed. Cleaning up $INSTALL_DIR..."
        rm -rf "$INSTALL_DIR"
    fi
}

trap cleanup_on_failure ERR

# ── Main ───────────────────────────────────────────────────────────────────────

main() {
    # Handle --uninstall flag
    if [ "${1:-}" = "--uninstall" ] || [ "${1:-}" = "uninstall" ]; then
        uninstall_pyfly
    fi

    banner
    check_prerequisites
    detect_source_dir
    prompt_install_dir
    prompt_extras
    prompt_add_to_path
    install_pyfly
    configure_path
    print_summary
}

main "$@"
