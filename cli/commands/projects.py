"""
Projects command module for IEQ Analytics CLI.

Handles complete project creation and management including:
- Project initialization with folder structure
- Data upload workflow
- Complete analytics pipeline automation
- Project status tracking
"""

import click
from pathlib import Path
from typing import Optional
import json
import yaml
import sys
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()


@click.group()
def projects():
    """🏗️ Create and manage IEQ analysis projects."""
    pass


@projects.command()
@click.option(
    '--name',
    type=str,
    help='Project name (will be used for folder name)'
)
@click.option(
    '--description',
    type=str,
    help='Project description'
)
@click.option(
    '--location',
    type=click.Path(path_type=Path),
    help='Parent directory to create project in (default: current directory)'
)
@click.option(
    '--template',
    type=click.Choice(['basic', 'advanced', 'research']),
    default='basic',
    help='Project template type'
)
@click.option(
    '--skip-interactive',
    is_flag=True,
    help='Skip interactive setup and use defaults'
)
@click.pass_context
def create(ctx, name: Optional[str], description: Optional[str], 
           location: Optional[Path], template: str, skip_interactive: bool):
    """🚀 Create a new IEQ analytics project with complete folder structure."""
    
    console.print("[bold blue]🏗️ Creating New IEQ Analytics Project...[/bold blue]")
    
    # Interactive setup if not skipped
    if not skip_interactive:
        if not name:
            name = Prompt.ask("📝 Enter project name", default="ieq_project")
        
        if not description:
            description = Prompt.ask("📋 Enter project description", default="IEQ Analysis Project")
        
        if not location:
            location = Path(Prompt.ask("📁 Enter parent directory", default=str(Path.cwd())))
        
        template = Prompt.ask(
            "🎨 Choose project template",
            choices=['basic', 'advanced', 'research'],
            default=template
        )
    else:
        # Use defaults for non-interactive mode
        name = name or "ieq_project"
        description = description or "IEQ Analysis Project"
        location = location or Path.cwd()
    
    # Validate inputs
    if not name or not name.strip():
        console.print("[red]❌ Project name cannot be empty[/red]")
        return
    
    # Clean project name (remove special characters, spaces)
    clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()
    if clean_name != name:
        console.print(f"[yellow]⚠️ Project name cleaned: '{name}' → '{clean_name}'[/yellow]")
        name = clean_name
    
    # Create project directory
    project_dir = Path(location) / name
    
    if project_dir.exists():
        if not Confirm.ask(f"[yellow]⚠️ Directory '{project_dir}' already exists. Continue?[/yellow]"):
            console.print("[red]❌ Project creation cancelled[/red]")
            return
    
    try:
        # Create folder structure
        console.print(f"📁 Creating project structure in: {project_dir}")
        _create_project_structure(project_dir, template)
        
        # Create configuration files
        console.print("⚙️ Setting up configuration files...")
        _create_project_config(project_dir, name, description, template)
        
        # Create project metadata
        project_metadata = {
            "name": name,
            "description": description,
            "template": template,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "status": "created",
            "pipeline_steps": {
                "data_upload": False,
                "mapping": False,
                "analysis": False,
                "reporting": False
            }
        }
        
        metadata_file = project_dir / "project.json"
        with open(metadata_file, 'w') as f:
            json.dump(project_metadata, f, indent=2)
        
        # Success message with instructions
        success_panel = Panel(
            f"""
[bold green]✅ Project '{name}' created successfully![/bold green]

📁 Project directory: {project_dir}
🎨 Template: {template}
📋 Description: {description}

[bold]📂 Project Structure:[/bold]
├── data/
│   ├── raw/          # Place your CSV files here
│   └── processed/    # Processed data (auto-generated)
├── config/           # Configuration files
├── output/           # Analysis results and reports
├── docs/             # Documentation
└── project.json      # Project metadata

[bold]🚀 Next Steps:[/bold]
1. Copy your raw CSV data files to: {project_dir}/data/raw/
2. Run: cd {project_dir}
3. Run: ieq-analyzer projects run --auto

[italic]Or use the interactive workflow: ieq-analyzer projects run[/italic]
            """,
            title="🎉 Project Created",
            border_style="green"
        )
        console.print(success_panel)
        
        # Ask if user wants to start the workflow immediately
        if not skip_interactive and Confirm.ask("\n🚀 Would you like to start the analytics workflow now?"):
            # Change context to project directory
            ctx.obj['workspace'] = project_dir
            
            # Start the workflow
            from click.testing import CliRunner
            runner = CliRunner()
            
            console.print("\n[bold]Starting project workflow...[/bold]")
            result = runner.invoke(run, ['--interactive'], obj=ctx.obj)
            
            if result.exit_code != 0:
                console.print("[red]❌ Workflow failed to start[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Error creating project: {e}[/red]")
        sys.exit(1)


@projects.command()
@click.option(
    '--auto',
    is_flag=True,
    help='Run complete pipeline automatically (non-interactive)'
)
@click.option(
    '--parallel',
    is_flag=True,
    help='Enable parallel processing'
)
@click.option(
    '--template',
    type=click.Choice(['executive', 'technical', 'research']),
    default='executive',
    help='Report template to generate'
)
@click.pass_context
def run(ctx, auto: bool, parallel: bool, template: str):
    """🚀 Run the complete IEQ analytics workflow for the current project."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    
    # Check if this is a valid project
    project_file = workspace / "project.json"
    if not project_file.exists():
        console.print("[red]❌ Not in a valid IEQ analytics project directory[/red]")
        console.print("Run 'ieq-analyzer projects create' to create a new project")
        return
    
    # Load project metadata
    with open(project_file, 'r') as f:
        project_metadata = json.load(f)
    
    project_name = project_metadata.get('name', 'Unknown Project')
    
    console.print(f"[bold green]🚀 Starting IEQ Analytics Workflow[/bold green]")
    console.print(f"📋 Project: {project_name}")
    console.print(f"📁 Workspace: {workspace}")
    
    # Define directories
    data_raw = workspace / "data" / "raw"
    data_processed = workspace / "data" / "processed"
    output_dir = workspace / "output"
    config_dir = workspace / "config"
    
    try:
        # Step 0: Check for data files
        console.print("\n[bold]Step 0: Data Validation[/bold]")
        csv_files = list(data_raw.glob("*.csv"))
        
        if not csv_files:
            if auto:
                console.print("[red]❌ No CSV files found in data/raw directory[/red]")
                console.print(f"Please copy your CSV files to: {data_raw}")
                return
            else:
                # Interactive data upload workflow
                _interactive_data_upload(data_raw)
                # Re-check for files
                csv_files = list(data_raw.glob("*.csv"))
                
                if not csv_files:
                    console.print("[red]❌ No CSV files found. Workflow cannot continue.[/red]")
                    return
        
        console.print(f"✅ Found {len(csv_files)} CSV files ready for processing")
        
        # Update project status
        project_metadata['pipeline_steps']['data_upload'] = True
        project_metadata['status'] = 'data_ready'
        
        # Complete pipeline workflow
        workflow_panel = Panel(
            """
[bold]🔄 Complete IEQ Analytics Pipeline[/bold]

1. 🗂️  Data Mapping (Raw CSV → Standardized Format)
2. 🔬 Comprehensive Analysis (Room + Building Level)  
3. 📊 Visualization Generation
4. 📋 Report Generation
5. 💾 Export Results

[italic]This process will analyze all uploaded data automatically...[/italic]
            """,
            title="🔄 Pipeline Overview",
            border_style="blue"
        )
        console.print(workflow_panel)
        
        # Import commands for pipeline execution
        from cli.commands.mapping import mapping
        from cli.commands.analyze import analyze
        from cli.commands.report import report
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Step 1: Data Mapping
        console.print("\n[bold]Step 1: Data Mapping[/bold]")
        mapping_args = [
            '--data-dir', str(data_raw),
            '--output-dir', str(data_processed)
        ]
        if auto:
            mapping_args.append('--auto')
        
        mapping_result = runner.invoke(mapping, mapping_args, obj=ctx.obj)
        if mapping_result.exit_code != 0:
            console.print("[red]❌ Data mapping failed![/red]")
            return
        
        project_metadata['pipeline_steps']['mapping'] = True
        
        # Step 2: Analysis
        console.print("\n[bold]Step 2: Comprehensive Analysis[/bold]")
        analysis_args = [
            'mapped-data',
            '--data-dir', str(data_processed / "mapped_data"),
            '--output-dir', str(output_dir / "analysis"),
            '--generate-plots'
        ]
        if parallel:
            analysis_args.append('--parallel')
        
        analysis_result = runner.invoke(analyze, analysis_args, obj=ctx.obj)
        if analysis_result.exit_code != 0:
            console.print("[red]❌ Analysis failed![/red]")
            return
        
        project_metadata['pipeline_steps']['analysis'] = True
        
        # Step 3: Report Generation
        console.print("\n[bold]Step 3: Report Generation[/bold]")
        report_result = runner.invoke(report, [
            'generate',
            '--analysis-dir', str(output_dir / "analysis"),
            '--output-dir', str(output_dir / "reports"),
            '--template', template,
            '--include-plots'
        ], obj=ctx.obj)
        
        if report_result.exit_code == 0:
            project_metadata['pipeline_steps']['reporting'] = True
        
        # Final status update
        project_metadata['status'] = 'completed'
        project_metadata['completed_at'] = datetime.now().isoformat()
        
        # Save updated metadata
        with open(project_file, 'w') as f:
            json.dump(project_metadata, f, indent=2)
        
        # Success summary
        completion_panel = Panel(
            f"""
[bold green]🎉 Project workflow completed successfully![/bold green]

📋 Project: {project_name}
📁 Workspace: {workspace}

[bold]📊 Generated Results:[/bold]
📂 Processed Data: data/processed/
📈 Analysis Results: output/analysis/
📋 Reports: output/reports/
🎨 Visualizations: output/analysis/plots/

[bold]📋 Quick Access:[/bold]
• View results: ls {output_dir}
• Open reports: open {output_dir}/reports/
• Review data: ieq-analyzer projects status

[italic]Your complete IEQ analysis is ready for review![/italic]
            """,
            title="✅ Pipeline Complete",
            border_style="green"
        )
        console.print(completion_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Pipeline failed: {e}[/red]")
        # Update project status
        project_metadata['status'] = 'failed'
        project_metadata['error'] = str(e)
        with open(project_file, 'w') as f:
            json.dump(project_metadata, f, indent=2)
        sys.exit(1)


@projects.command()
@click.pass_context
def status(ctx):
    """📊 Show current project status and progress."""
    
    workspace = ctx.obj.get('workspace', Path.cwd())
    project_file = workspace / "project.json"
    
    if not project_file.exists():
        console.print("[red]❌ Not in a valid IEQ analytics project directory[/red]")
        console.print("Run 'ieq-analyzer projects create' to create a new project")
        return
    
    # Load project metadata
    with open(project_file, 'r') as f:
        project_metadata = json.load(f)
    
    # Display project information
    console.print(f"[bold blue]📊 Project Status: {project_metadata.get('name', 'Unknown')}[/bold blue]")
    
    # Basic info table
    info_table = Table(title="Project Information")
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Name", project_metadata.get('name', 'Unknown'))
    info_table.add_row("Description", project_metadata.get('description', 'No description'))
    info_table.add_row("Template", project_metadata.get('template', 'Unknown'))
    info_table.add_row("Status", project_metadata.get('status', 'Unknown'))
    info_table.add_row("Created", project_metadata.get('created_at', 'Unknown'))
    
    if 'completed_at' in project_metadata:
        info_table.add_row("Completed", project_metadata['completed_at'])
    
    console.print(info_table)
    
    # Pipeline progress
    console.print("\n[bold]🔄 Pipeline Progress:[/bold]")
    steps = project_metadata.get('pipeline_steps', {})
    
    progress_table = Table()
    progress_table.add_column("Step", style="cyan")
    progress_table.add_column("Status", style="white")
    progress_table.add_column("Description", style="dim")
    
    step_info = {
        'data_upload': ('Data Upload', 'CSV files uploaded to data/raw/'),
        'mapping': ('Data Mapping', 'Raw data converted to standardized format'),
        'analysis': ('Analysis', 'IEQ analysis completed'),
        'reporting': ('Reporting', 'Analysis reports generated')
    }
    
    for step_key, (step_name, step_desc) in step_info.items():
        status = "✅ Complete" if steps.get(step_key, False) else "⏳ Pending"
        progress_table.add_row(step_name, status, step_desc)
    
    console.print(progress_table)
    
    # File counts and sizes
    console.print("\n[bold]📁 Directory Status:[/bold]")
    
    dirs_to_check = {
        'data/raw': 'Raw CSV files',
        'data/processed': 'Processed data files',
        'output/analysis': 'Analysis results',
        'output/reports': 'Generated reports',
        'config': 'Configuration files'
    }
    
    for dir_path, description in dirs_to_check.items():
        full_path = workspace / dir_path
        if full_path.exists():
            file_count = len(list(full_path.rglob('*')))
            console.print(f"  📂 {dir_path}: {file_count} files - {description}")
        else:
            console.print(f"  📂 {dir_path}: [dim]Directory not found[/dim]")
    
    # Show next steps
    status = project_metadata.get('status', 'unknown')
    console.print(f"\n[bold]🚀 Next Steps:[/bold]")
    
    if status == 'created':
        console.print("  1. Copy CSV files to data/raw/")
        console.print("  2. Run: ieq-analyzer projects run")
    elif status == 'data_ready':
        console.print("  1. Run: ieq-analyzer projects run")
    elif status == 'completed':
        console.print("  ✅ Project complete! Review results in output/ directory")
        console.print("  💡 Generate additional reports: ieq-analyzer report generate")
    elif status == 'failed':
        console.print("  ⚠️ Previous run failed. Check error logs and retry.")
        console.print("  🔄 Retry: ieq-analyzer projects run")


def _create_project_structure(project_dir: Path, template: str):
    """Create the complete project folder structure."""
    
    # Create base directories
    directories = [
        "data/raw",
        "data/processed",
        "config",
        "output/analysis",
        "output/reports",
        "output/plots",
        "docs",
        "scripts"
    ]
    
    # Add template-specific directories
    if template == 'research':
        directories.extend([
            "notebooks",
            "references",
            "manuscripts"
        ])
    elif template == 'advanced':
        directories.extend([
            "custom_scripts",
            "external_data"
        ])
    
    for directory in directories:
        (project_dir / directory).mkdir(parents=True, exist_ok=True)
    
    # Create README files
    _create_readme_files(project_dir, template)
    
    # Create .gitignore
    gitignore_content = """
# Data files
data/raw/*.csv
data/processed/
*.log

# Output files
output/
*.pdf
*.html

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    with open(project_dir / ".gitignore", 'w') as f:
        f.write(gitignore_content.strip())


def _create_readme_files(project_dir: Path, template: str):
    """Create README files for the project."""
    
    main_readme = f"""# IEQ Analytics Project

This project was created using the IEQ Analytics CLI tool with the **{template}** template.

## Quick Start

1. **Add your data**: Copy CSV files to `data/raw/`
2. **Run analysis**: `ieq-analyzer projects run`
3. **View results**: Check `output/reports/` for generated reports

## Project Structure

```
├── data/
│   ├── raw/          # Your original CSV files (add files here)
│   └── processed/    # Processed data (auto-generated)
├── config/           # Configuration files
├── output/           # All analysis results
│   ├── analysis/     # Detailed analysis data
│   ├── reports/      # Generated reports (PDF, HTML)
│   └── plots/        # Visualization charts
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Commands

- `ieq-analyzer projects status` - Check project progress
- `ieq-analyzer projects run` - Run complete analysis pipeline
- `ieq-analyzer projects run --auto` - Run without interactive prompts

## Data Format

Your CSV files should contain IEQ sensor data with columns for:
- Timestamp/timestamp
- Temperature
- Humidity
- CO2
- Additional environmental parameters

The system will automatically detect and map your column names.

## Generated Results

After running the analysis, you'll find:

- **Reports**: Professional PDF and HTML reports in `output/reports/`
- **Charts**: Visualization plots in `output/plots/`
- **Data**: Processed data in `data/processed/`
- **Analysis**: Detailed analysis results in `output/analysis/`

For more information, visit the docs/ directory or run `ieq-analyzer --help`
"""
    
    with open(project_dir / "README.md", 'w') as f:
        f.write(main_readme)
    
    # Data README
    data_readme = """# Data Directory

## raw/
Place your original CSV sensor data files here. The system supports:
- Multiple buildings and rooms
- Various sensor types (temperature, humidity, CO2, etc.)
- Different timestamp formats
- Custom column naming

## processed/
Auto-generated processed data in standardized format.
Don't modify files in this directory manually.
"""
    
    with open(project_dir / "data" / "README.md", 'w') as f:
        f.write(data_readme)


def _create_project_config(project_dir: Path, name: str, description: str, template: str):
    """Create default configuration files for the project."""
    
    config_dir = project_dir / "config"
    
    # Create basic tests.yaml
    tests_config = {
        "tests": {
            "temp_comfort_opening": {
                "description": "Temperature comfort during opening hours (20-26°C)",
                "feature": "temperature",
                "period": "all_year",
                "filter": "opening_hours",
                "mode": "bidirectional",
                "limits": {"upper": 26, "lower": 20}
            },
            "co2_quality_opening": {
                "description": "CO2 air quality during opening hours (<1000ppm)",
                "feature": "co2",
                "period": "all_year", 
                "filter": "opening_hours",
                "mode": "unidirectional_ascending",
                "limit": 1000
            },
            "humidity_comfort": {
                "description": "Humidity comfort (30-60%)",
                "feature": "humidity",
                "period": "all_year",
                "filter": "all_hours",
                "mode": "bidirectional",
                "limits": {"upper": 60, "lower": 30}
            }
        },
        "periods": {
            "all_year": {"months": [1,2,3,4,5,6,7,8,9,10,11,12]}
        },
        "filters": {
            "opening_hours": {
                "hours": [8,9,10,11,12,13,14,15],
                "weekdays_only": True
            },
            "all_hours": {
                "hours": list(range(24)),
                "weekdays_only": False
            }
        }
    }
    
    with open(config_dir / "tests.yaml", 'w') as f:
        yaml.dump(tests_config, f, default_flow_style=False)
    
    # Create mapping config
    mapping_config = {
        "version": "1.0",
        "default_building_name": f"{name}_building",
        "timestamp_formats": [
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M"
        ],
        "parameter_mappings": {
            "temperature": ["temp", "temperature", "air_temp"],
            "humidity": ["humidity", "rh", "relative_humidity"],
            "co2": ["co2", "carbon_dioxide", "co2_ppm"]
        }
    }
    
    with open(config_dir / "mapping_config.json", 'w') as f:
        json.dump(mapping_config, f, indent=2)


def _interactive_data_upload(data_raw: Path):
    """Guide user through data upload process."""
    
    console.print("\n[bold yellow]📂 Data Upload Required[/bold yellow]")
    
    upload_panel = Panel(
        f"""
[bold]No CSV files found in data directory![/bold]

Please copy your CSV sensor data files to:
📁 {data_raw}

[bold]Supported formats:[/bold]
• CSV files with headers
• Temperature, humidity, CO2 data
• Timestamp columns
• Multiple buildings/rooms

[italic]The system will automatically detect and map your column names.[/italic]
        """,
        title="📤 Data Upload Instructions",
        border_style="yellow"
    )
    console.print(upload_panel)
    
    # Wait for user to upload files
    console.print("\n[bold]Waiting for data upload...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        
        task = progress.add_task("Checking for CSV files...", total=None)
        
        while True:
            csv_files = list(data_raw.glob("*.csv"))
            if csv_files:
                progress.update(task, description=f"✅ Found {len(csv_files)} CSV files!")
                break
            
            time.sleep(2)
            
            # Ask user if they want to continue waiting
            if not progress.tasks:  # Check if we should ask
                try:
                    if not Confirm.ask("\n⏱️ Still waiting for files. Continue?", default=True):
                        console.print("[red]❌ Data upload cancelled[/red]")
                        return
                except KeyboardInterrupt:
                    console.print("\n[red]❌ Upload cancelled by user[/red]")
                    return
    
    console.print(f"[green]✅ Successfully detected {len(csv_files)} CSV files![/green]")
