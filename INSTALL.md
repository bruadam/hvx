# IEQ Analytics CLI Installation Guide

## Quick Install

### Unix/Linux/macOS
```bash
# Simple installation (recommended)
./install.sh

# Development installation
./install.sh --dev

# Global installation (not recommended)
./install.sh --global
```

### Windows
```cmd
# Simple installation (recommended)
install.bat

# Development installation  
install.bat --dev

# Global installation (not recommended)
install.bat --global
```

## Manual Installation

If the automated scripts don't work, you can install manually:

### Prerequisites
- Python 3.8 or higher
- pip

### Manual Steps

1. **Create virtual environment (recommended):**
   ```bash
   # Unix/Linux/macOS
   python -m venv venv_ieq
   source venv_ieq/bin/activate
   
   # Windows
   python -m venv venv_ieq
   venv_ieq\Scripts\activate.bat
   ```

2. **Install the CLI:**
   ```bash
   pip install -e .
   ```

3. **Test installation:**
   ```bash
   ieq-analyzer --help
   ```

## Usage

After installation, use the CLI with the `ieq-analyzer` command:

### Quick Start
```bash
# Show help
ieq-analyzer --help

# Map raw data to standardized format
ieq-analyzer mapping map-data --input-dir data/raw --output-dir output/mapped

# Analyze mapped data
ieq-analyzer analyze mapped-data --data-dir output/mapped --output-dir output

# Create analytics rules
ieq-analyzer rules create --interactive

# Generate reports from YAML tests
ieq-analyzer report from-yaml --interactive
```

### Command Overview

| Command | Description |
|---------|-------------|
| `mapping` | Convert raw data to standardized format |
| `analyze` | Analyze mapped IEQ data |
| `rules` | Create, list, delete, and test analytics rules |
| `report` | Generate reports and visualizations |

### Detailed Command Help

```bash
# Get help for specific commands
ieq-analyzer mapping --help
ieq-analyzer analyze --help  
ieq-analyzer rules --help
ieq-analyzer report --help

# Get help for subcommands
ieq-analyzer rules create --help
ieq-analyzer report from-yaml --help
```

## Configuration

The CLI uses configuration files in the `config/` directory:

- `tests.yaml` - Analytics rules and thresholds
- `en16798_thresholds.yaml` - EN16798 standard thresholds
- `mapping_config.json` - Data mapping configuration
- `report_config.yaml` - Report generation settings

## Data Flow

1. **Raw Data** (`data/raw/`) → **Mapping** → **Mapped Data** (`output/mapped/`)
2. **Mapped Data** → **Analysis** → **Analysis Results** (`output/`)
3. **Analysis Results** → **Reporting** → **Reports & Visualizations** (`output/plots/`)

## Troubleshooting

### Command not found
If `ieq-analyzer` is not found after installation:

1. **Virtual Environment:** Make sure it's activated
   ```bash
   # Unix/Linux/macOS
   source venv_ieq/bin/activate
   
   # Windows  
   venv_ieq\Scripts\activate.bat
   ```

2. **Global Installation:** Add Python Scripts to PATH
   ```bash
   # Find Python Scripts directory
   python -c "import sys; print(sys.prefix + '/bin')"  # Unix
   python -c "import sys; print(sys.prefix + '\\Scripts')"  # Windows
   ```

### Import Errors
If you get import errors, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Permission Errors
On Unix systems, you may need to make scripts executable:
```bash
chmod +x install.sh
```

## Uninstallation

### Automated
- **Unix/Linux/macOS:** Run the generated `uninstall.sh` script
- **Windows:** Run the generated `uninstall.bat` script

### Manual
```bash
# Uninstall the package
pip uninstall ieq-analyzer

# Remove virtual environment (if used)
rm -rf venv_ieq  # Unix
rmdir /s venv_ieq  # Windows
```

## Development

For development installation:
```bash
# Install in development mode
./install.sh --dev  # Unix
install.bat --dev   # Windows

# Now changes to the code are immediately reflected
```

## Support

For issues and questions:
1. Check the command help: `ieq-analyzer --help`
2. Verify your data format matches the expected structure
3. Check configuration files in `config/` directory
4. Review logs and error messages for specific guidance
