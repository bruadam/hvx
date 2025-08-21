#!/bin/bash

# IEQ Analytics CLI Installation Script
# This script installs the IEQ Analytics CLI as a global command: ieq-analyzer

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_success "Python $PYTHON_VERSION found"
        
        # Check if Python version is >= 3.8
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            print_success "Python version is compatible (>= 3.8)"
        else
            print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip installation..."
    
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    elif command -v pip &> /dev/null; then
        print_success "pip found"
    else
        print_error "pip is not installed. Please install pip."
        exit 1
    fi
}

# Create virtual environment (optional)
setup_venv() {
    if [ "$1" = "--global" ]; then
        print_warning "Installing globally (not recommended for production)"
        return
    fi
    
    print_status "Setting up virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv_ieq" ]; then
        python3 -m venv venv_ieq
        print_success "Virtual environment created: venv_ieq"
    else
        print_warning "Virtual environment already exists: venv_ieq"
    fi
    
    # Activate virtual environment
    source venv_ieq/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
}

# Install the CLI package
install_cli() {
    print_status "Installing IEQ Analytics CLI..."
    
    # Install in development mode so changes are immediately available
    if [ "$1" = "--dev" ]; then
        pip install -e .
        print_success "IEQ Analytics CLI installed in development mode"
    else
        pip install .
        print_success "IEQ Analytics CLI installed"
    fi

}

# Create desktop entry (Linux only)
create_desktop_entry() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Creating desktop entry..."
        
        DESKTOP_FILE="$HOME/.local/share/applications/ieq-analyzer.desktop"
        mkdir -p "$(dirname "$DESKTOP_FILE")"
        
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=IEQ Analyzer
Comment=Indoor Environmental Quality Analysis Tool
Exec=ieq-analyzer
Icon=utilities-terminal
Terminal=true
Categories=Development;Science;
EOF
        
        print_success "Desktop entry created: $DESKTOP_FILE"
    fi
}

# Test the installation
test_installation() {
    print_status "Testing installation..."
    
    if command -v ieq-analyzer &> /dev/null; then
        print_success "ieq-analyzer command is available"
        
        # Test version command
        if ieq-analyzer --version &> /dev/null; then
            print_success "Version command works"
        else
            print_warning "Version command failed, but CLI is installed"
        fi
        
        # Show help
        print_status "CLI Help:"
        echo "=========================="
        ieq-analyzer --help
        echo "=========================="
        
    else
        print_error "ieq-analyzer command not found in PATH"
        print_warning "You may need to restart your terminal or add the installation directory to PATH"
        
        # Try to find where it was installed
        PYTHON_BIN_DIR=$(python3 -c "import sys; print(sys.prefix + '/bin')")
        if [ -f "$PYTHON_BIN_DIR/ieq-analyzer" ]; then
            print_status "Found ieq-analyzer at: $PYTHON_BIN_DIR/ieq-analyzer"
            print_status "Add $PYTHON_BIN_DIR to your PATH or create a symlink"
        fi
    fi
}

# Create uninstall script
create_uninstall_script() {
    print_status "Creating uninstall script..."
    
    cat > uninstall.sh << 'EOF'
#!/bin/bash

# IEQ Analytics CLI Uninstall Script

print_status() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_status "Uninstalling IEQ Analytics CLI..."

# Uninstall the package
if command -v pip3 &> /dev/null; then
    pip3 uninstall ieq-analyzer -y
elif command -v pip &> /dev/null; then
    pip uninstall ieq-analyzer -y
else
    echo "pip not found, manual cleanup may be required"
fi

# Remove desktop entry (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    DESKTOP_FILE="$HOME/.local/share/applications/ieq-analyzer.desktop"
    if [ -f "$DESKTOP_FILE" ]; then
        rm "$DESKTOP_FILE"
        print_success "Desktop entry removed"
    fi
fi

# Remove virtual environment if exists
if [ -d "venv_ieq" ]; then
    read -p "Remove virtual environment (venv_ieq)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv_ieq
        print_success "Virtual environment removed"
    fi
fi

print_success "IEQ Analytics CLI uninstalled"
EOF
    
    chmod +x uninstall.sh
    print_success "Uninstall script created: ./uninstall.sh"
}

# Show usage information
show_usage() {
    cat << EOF

🏢 IEQ Analytics CLI Installation Script

Usage: $0 [OPTIONS]

OPTIONS:
    --global    Install globally (not recommended)
    --dev       Install in development mode
    --help      Show this help message

EXAMPLES:
    $0                  # Install in virtual environment (recommended)
    $0 --dev            # Install in development mode
    $0 --global         # Install globally (not recommended)

POST-INSTALLATION:
    After installation, you can use the CLI with:
    
    ieq-analyzer --help                           # Show help
    ieq-analyzer mapping --help                   # Map raw data
    ieq-analyzer analyze --help                   # Analyze data
    ieq-analyzer rules create --interactive       # Create rules
    ieq-analyzer report from-yaml --interactive   # Generate reports

EOF
}

# Main installation function
main() {
    echo "🏢 IEQ Analytics CLI Installation"
    echo "================================="
    
    # Parse command line arguments
    GLOBAL_INSTALL=false
    DEV_INSTALL=false
    
    for arg in "$@"; do
        case $arg in
            --global)
                GLOBAL_INSTALL=true
                shift
                ;;
            --dev)
                DEV_INSTALL=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $arg"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Run installation steps
    check_python
    check_pip
    
    if [ "$GLOBAL_INSTALL" = false ]; then
        setup_venv
    fi
    
    if [ "$DEV_INSTALL" = true ]; then
        install_cli --dev
    else
        install_cli
    fi
    
    create_desktop_entry
    test_installation
    create_uninstall_script
    
    echo ""
    print_success "🎉 Installation completed successfully!"
    echo ""
    echo "📚 Quick Start:"
    echo "   ieq-analyzer --help                           # Show help"
    echo "   ieq-analyzer mapping --help                   # Map raw data"
    echo "   ieq-analyzer analyze --help                   # Analyze data"
    echo "   ieq-analyzer rules create --interactive       # Create rules"
    echo "   ieq-analyzer report from-yaml --interactive   # Generate reports"
    echo ""
    echo "🗑️  To uninstall: ./uninstall.sh"
    echo ""
}

# Run main function with all arguments
main "$@"
