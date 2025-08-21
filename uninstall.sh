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
