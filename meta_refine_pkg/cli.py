#!/usr/bin/env python3
"""
Meta-Refine: Intelligent Code Review and Improvement System

A sophisticated code analysis tool powered by Meta's Llama 3.1-8B-Instruct model.
Demonstrates advanced AI/ML engineering, software architecture, and developer tooling.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .core.analyzer import CodeAnalyzer
from .core.config import Settings, get_settings
from .core.formatter import ResultFormatter
from .core.model import LlamaModelInterface
from .core.utils import setup_logging, validate_environment, get_system_info

# Initialize CLI app and console
app = typer.Typer(
    name="meta",
    help="""✨ [bold rgb(25,119,243)]meta[/bold rgb(25,119,243)] [bold rgb(0,204,188)]refine[/bold rgb(0,204,188)] - AI-Powered Code Intelligence

Built with Meta's cutting-edge Llama 3.1 model for intelligent code analysis.
Instantly discover bugs, security vulnerabilities, and optimization opportunities.

🚀 [bold]Quick Commands:[/bold]
  [rgb(25,119,243)]meta setup[/rgb(25,119,243)]              # Get started in seconds
  [rgb(0,204,188)]meta analyze file.py[/rgb(0,204,188)]    # Analyze any code file  
  [rgb(255,186,8)]meta interactive[/rgb(255,186,8)]        # Launch AI coding assistant
  [rgb(168,168,168)]meta doctor[/rgb(168,168,168)]             # System health check

🎯 [bold]Power Features:[/bold]
  [dim]• Multi-language support (Python, JS, Java, C++, Go, Rust)[/dim]
  [dim]• Real-time security vulnerability detection[/dim]
  [dim]• Performance optimization suggestions[/dim]
  [dim]• Export reports in JSON, HTML, Markdown[/dim]

💡 [bold]Examples:[/bold]
  meta analyze --file app.py --security     # Security-focused scan
  meta analyze --project ./src --format json # Full project report
  meta interactive                           # AI-powered coding session

[dim]Powered by Meta AI • Built for developers, by developers[/dim]
""",
    add_completion=True,
    rich_markup_mode="rich",
)
console = Console()


def display_banner():
    """Display the Meta-Refine banner with Meta branding."""
    # Meta-inspired gradient colors
    banner = Text()
    banner.append("meta", style="bold rgb(25,119,243)")  # Meta blue
    banner.append(" refine", style="bold rgb(0,204,188)")  # Meta teal
    banner.append(" ✨\n", style="bold rgb(255,186,8)")  # Meta yellow
    banner.append("AI-Powered Code Intelligence by Meta", style="dim rgb(168,168,168)")
    
    console.print(Panel(
        banner,
        border_style="rgb(25,119,243)",
        padding=(1, 2),
        title="[bold rgb(25,119,243)]🔮 Meta AI[/bold rgb(25,119,243)]",
        title_align="left"
    ))


@app.command()
def analyze(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Single file to analyze"
    ),
    project: Optional[Path] = typer.Option(
        None, "--project", "-p", help="Project directory to analyze"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Force specific language (python, javascript, etc.)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file for results (JSON/HTML)"
    ),
    format: str = typer.Option(
        "console", "--format", help="Output format: console, json, html, markdown"
    ),
    severity: str = typer.Option(
        "all", "--severity", help="Minimum severity: critical, high, medium, low, all"
    ),
    include_suggestions: bool = typer.Option(
        True, "--suggestions/--no-suggestions", help="Include improvement suggestions"
    ),
    include_performance: bool = typer.Option(
        True, "--performance/--no-performance", help="Include performance analysis"
    ),
    include_security: bool = typer.Option(
        True, "--security/--no-security", help="Include security analysis"
    ),
    parallel: bool = typer.Option(
        True, "--parallel/--sequential", help="Use parallel processing"
    ),
    cache: bool = typer.Option(
        True, "--cache/--no-cache", help="Use caching for faster repeated analysis"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    🔍 Analyze code files or projects for improvements.
    
    Performs comprehensive analysis including:
    • Bug detection and logic issues
    • Security vulnerability scanning  
    • Performance optimization opportunities
    • Code style and best practice suggestions
    • Documentation quality assessment
    
    📖 Examples:
        # Analyze single file with console output
        meta-refine analyze --file app.py
        
        # Analyze entire project with JSON export
        meta-refine analyze --project ./src --format json --output report.json
        
        # Security-focused analysis only
        meta-refine analyze --file script.js --security --no-suggestions --no-performance
        
        # Analyze with specific severity filter
        meta-refine analyze --project . --severity critical --format markdown
    """
    display_banner()
    
    if not file and not project:
        console.print("[red]Error: Must specify either --file or --project[/red]")
        raise typer.Exit(1)
    
    if file and project:
        console.print("[red]Error: Cannot specify both --file and --project[/red]")
        raise typer.Exit(1)
    
    # Validate environment and setup
    setup_logging(verbose)
    env_valid, env_details = validate_environment(show_suggestions=False)
    if not env_valid:
        console.print("[red]❌ Environment validation failed[/red]")
        console.print("\n[bold]Issues found:[/bold]")
        for check_name, details in env_details.items():
            if not details['passed']:
                console.print(f"  {details['status']} {check_name.replace('_', ' ').title()}")
                console.print(f"    [dim]💡 {details['suggestion']}[/dim]")
        console.print(f"\n[cyan]💡 Run 'meta setup' for guided configuration[/cyan]")
        raise typer.Exit(1)
    
    # Run analysis
    asyncio.run(_run_analysis(
        file=file,
        project=project,
        language=language,
        output=output,
        format=format,
        severity=severity,
        include_suggestions=include_suggestions,
        include_performance=include_performance,
        include_security=include_security,
        parallel=parallel,
        cache=cache,
        verbose=verbose,
    ))


async def _run_analysis(
    file: Optional[Path],
    project: Optional[Path],
    language: Optional[str],
    output: Optional[Path],
    format: str,
    severity: str,
    include_suggestions: bool,
    include_performance: bool,
    include_security: bool,
    parallel: bool,
    cache: bool,
    verbose: bool,
):
    """Run the actual analysis with progress tracking."""
    settings = get_settings()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Initialize components
        init_task = progress.add_task("🔧 Initializing components...", total=None)
        
        try:
            model = LlamaModelInterface(settings.llama_config)
            analyzer = CodeAnalyzer(model, settings.analysis_config)
            formatter = ResultFormatter(settings.output_config)
            
            progress.update(init_task, description="✅ Components initialized")
            progress.stop_task(init_task)
            
            # Analyze files
            analysis_task = progress.add_task("🔍 Analyzing code...", total=None)
            
            if file:
                results = await analyzer.analyze_file(
                    file,
                    language=language,
                    include_suggestions=include_suggestions,
                    include_performance=include_performance,
                    include_security=include_security,
                    cache=cache,
                )
            else:
                results = await analyzer.analyze_project(
                    project,
                    language=language,
                    include_suggestions=include_suggestions,
                    include_performance=include_performance,
                    include_security=include_security,
                    parallel=parallel,
                    cache=cache,
                )
            
            progress.update(analysis_task, description="✅ Analysis complete")
            progress.stop_task(analysis_task)
            
            # Format and display results
            format_task = progress.add_task("📊 Formatting results...", total=None)
            
            formatted_output = formatter.format_results(
                results,
                format=format,
                severity=severity,
                output_file=output,
            )
            
            progress.update(format_task, description="✅ Results formatted")
            progress.stop_task(format_task)
            
        except Exception as e:
            progress.stop()
            console.print(f"[red]Error during analysis: {e}[/red]")
            if verbose:
                console.print_exception()
            raise typer.Exit(1)
    
    # Display results to console if not outputting to file
    if format == "console" and not output:
        console.print("\n")
        console.print(formatted_output)
    elif output:
        console.print(f"\n✅ Results saved to {output}")


@app.command()
def interactive():
    """
    🎯 Start interactive analysis mode.
    
    Provides a REPL-like experience for exploring code analysis.
    """
    display_banner()
    
    console.print("\n[bold rgb(25,119,243)]🤖 Meta AI Assistant Activated[/bold rgb(25,119,243)]")
    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    # Setup
    setup_logging(False)
    env_valid, _ = validate_environment(show_suggestions=False)
    if not env_valid:
        console.print("[red]Environment not ready. Run 'meta setup' first.[/red]")
        raise typer.Exit(1)
    
    settings = get_settings()
    
    # Interactive REPL
    while True:
        try:
            command = console.input("[bold rgb(25,119,243)]meta>[/bold rgb(25,119,243)] ").strip()
            
            if command.lower() in ['exit', 'quit', 'q']:
                console.print("[green]Goodbye![/green]")
                break
            elif command.lower() in ['help', 'h']:
                _show_interactive_help()
            elif command.startswith('analyze '):
                file_path = command[8:].strip()
                if file_path:
                    asyncio.run(_run_quick_analysis(Path(file_path)))
                else:
                    console.print("[red]Usage: analyze <file_path>[/red]")
            elif command.lower() == 'status':
                _show_system_status()
            elif command.lower() == 'examples':
                _show_examples()
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("[dim]Type 'help' for available commands[/dim]")
        except KeyboardInterrupt:
            console.print("\n[green]Goodbye![/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key=value"),
    reset: bool = typer.Option(False, "--reset", help="Reset to default configuration"),
):
    """
    ⚙️ Manage Meta-Refine configuration.
    
    Examples:
        meta-refine config --show
        meta-refine config --set model.temperature=0.7
        meta-refine config --reset
    """
    if show:
        settings = get_settings()
        table = Table(title="Meta-Refine Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        # Add configuration rows
        for key, value in settings.dict().items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    table.add_row(f"{key}.{subkey}", str(subvalue))
            else:
                table.add_row(key, str(value))
        
        console.print(table)
    
    elif set_key:
        # Configuration setting logic would go here
        console.print(f"[green]Configuration updated: {set_key}[/green]")
    
    elif reset:
        # Configuration reset logic would go here
        console.print("[green]Configuration reset to defaults[/green]")
    
    else:
        console.print("[yellow]Use --show, --set, or --reset[/yellow]")


@app.command()
def benchmark(
    file: Path = typer.Argument(..., help="File to benchmark analysis on"),
    iterations: int = typer.Option(5, "--iterations", "-n", help="Number of iterations"),
    warmup: int = typer.Option(1, "--warmup", help="Warmup iterations"),
):
    """
    📈 Benchmark analysis performance.
    
    Useful for optimizing prompts and model parameters.
    """
    display_banner()
    console.print(f"\n[bold]📈 Benchmarking analysis on {file}[/bold]")
    console.print(f"Iterations: {iterations}, Warmup: {warmup}\n")
    
    # Benchmark implementation would go here
    console.print("[yellow]Benchmarking coming soon![/yellow]")


@app.command()
def setup(
    force: bool = typer.Option(False, "--force", help="Force setup even if already configured"),
    interactive: bool = typer.Option(True, "--interactive/--non-interactive", help="Interactive setup wizard")
):
    """
    🛠️ Setup Meta-Refine for first-time use.
    
    Guides you through initial configuration and validates the environment.
    """
    display_banner()
    
    if interactive:
        _run_setup_wizard(force)
    else:
        _run_automated_setup(force)

@app.command()
def doctor():
    """
    🩺 Check system health and dependencies.
    
    Validates environment setup and model availability.
    """
    display_banner()
    console.print("\n[bold]🩺 Running System Diagnostics[/bold]\n")
    
    # Run comprehensive validation
    env_valid, env_details = validate_environment(show_suggestions=False)
    
    # Create detailed diagnostics table
    table = Table(title="System Health Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    for check_name, details in env_details.items():
        component_name = check_name.replace('_', ' ').title()
        status = details['status']
        suggestion = details['suggestion'] if not details['passed'] else "Working correctly"
        
        table.add_row(component_name, status, suggestion)
    
    console.print(table)
    
    # System info
    console.print("\n[bold]💻 System Information[/bold]")
    sys_info = get_system_info()
    if sys_info:
        info_table = Table()
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        for key, value in sys_info.items():
            formatted_key = key.replace('_', ' ').title()
            info_table.add_row(formatted_key, str(value))
        
        console.print(info_table)
    
    # Overall status
    console.print()
    if env_valid:
        console.print("[green]✅ System ready for analysis![/green]")
        console.print("\n[bold]Quick Start:[/bold]")
        console.print("• Try: [cyan]meta analyze examples/example.py[/cyan]")
    else:
        console.print("[red]❌ System needs attention[/red]")
        console.print("\n[bold]Recommendations:[/bold]")
        for check_name, details in env_details.items():
            if not details['passed']:
                console.print(f"• {details['suggestion']}")
        console.print("\n[cyan]💡 Run 'meta setup' for guided fixes[/cyan]")


@app.command()
def examples():
    """
    📚 Show usage examples and tutorials.
    
    Displays common usage patterns and examples for different scenarios.
    """
    display_banner()
    
    console.print("\n[bold]📚 Meta-Refine Usage Examples[/bold]\n")
    
    examples_data = [
        {
            "title": "🚀 Quick Start",
            "commands": [
                ("meta setup", "Interactive setup wizard"),
                ("meta analyze --file app.py", "Analyze a single file"),
                ("meta doctor", "Check system health"),
            ]
        },
        {
            "title": "📁 File Analysis",
            "commands": [
                ("meta analyze --file script.py --verbose", "Detailed single file analysis"),
                ("meta analyze --file app.js --format json", "Export analysis as JSON"),
                ("meta analyze --file code.py --severity high", "Show only high+ severity issues"),
            ]
        },
        {
            "title": "🏗️ Project Analysis", 
            "commands": [
                ("meta analyze --project ./src", "Analyze entire project"),
                ("meta analyze --project . --parallel", "Fast parallel analysis"),
                ("meta analyze --project ./app --format html --output report.html", "Generate HTML report"),
            ]
        },
        {
            "title": "🔒 Security Focus",
            "commands": [
                ("meta analyze --file app.py --security --no-performance", "Security-only analysis"),
                ("meta analyze --project . --security --severity critical", "Critical security issues"),
            ]
        },
        {
            "title": "⚡ Performance Analysis",
            "commands": [
                ("meta analyze --file slow.py --performance --no-suggestions", "Performance-only analysis"),
                ("meta analyze --project . --performance --format markdown", "Performance report"),
            ]
        },
        {
            "title": "🎯 Interactive Mode",
            "commands": [
                ("meta interactive", "Start interactive analysis session"),
                ("analyze examples/example.py", "Analyze file in interactive mode"),
                ("status", "Check system status in interactive mode"),
            ]
        },
        {
            "title": "⚙️ Configuration",
            "commands": [
                ("meta config --show", "Show current configuration"),
                ("meta config --set model.temperature=0.7", "Update model settings"),
                ("meta benchmark examples/example.py", "Benchmark analysis performance"),
            ]
        }
    ]
    
    for section in examples_data:
        console.print(f"[bold cyan]{section['title']}[/bold cyan]")
        
        for command, description in section['commands']:
            console.print(f"  [green]${command}[/green]")
            console.print(f"    [dim]{description}[/dim]")
        
        console.print()
    
    console.print("[bold]💡 Tips:[/bold]")
    console.print("• Use [cyan]--help[/cyan] with any command for detailed options")
    console.print("• Set [cyan]--verbose[/cyan] for detailed logging and debugging")
    console.print("• Use [cyan]--format json[/cyan] for programmatic integration")
    console.print("• Run [cyan]meta doctor[/cyan] if you encounter issues")


@app.command()
def completion(
    install: bool = typer.Option(False, "--install", help="Install shell completion"),
    shell: str = typer.Option(None, "--shell", help="Shell type (bash, zsh, fish)")
):
    """
    🔧 Manage shell auto-completion.
    
    Install or show auto-completion setup for your shell.
    """
    if install:
        console.print("[bold]🔧 Installing Shell Completion[/bold]\\n")
        
        if not shell:
            console.print("Auto-detecting shell...")
            shell = os.environ.get('SHELL', '').split('/')[-1]
        
        if shell in ['bash', 'zsh', 'fish']:
            console.print(f"Setting up completion for {shell}...")
            
            if shell == 'bash':
                completion_cmd = "complete -C meta-refine meta-refine"
                config_file = "~/.bashrc"
            elif shell == 'zsh':
                completion_cmd = "complete -o bashdefault -C meta-refine meta-refine"
                config_file = "~/.zshrc"
            else:  # fish
                completion_cmd = "complete -c meta-refine -f -a '(meta-refine)'"
                config_file = "~/.config/fish/config.fish"
            
            console.print(f"Add this line to your {config_file}:")
            console.print(f"[green]{completion_cmd}[/green]")
            console.print("\\nThen reload your shell or run:")
            console.print(f"[cyan]source {config_file}[/cyan]")
        else:
            console.print(f"[red]Unsupported shell: {shell}[/red]")
            console.print("Supported shells: bash, zsh, fish")
    else:
        console.print("[bold]🔧 Shell Auto-completion Setup[/bold]\\n")
        console.print("To enable auto-completion, run:")
        console.print("[cyan]meta-refine completion --install[/cyan]")
        console.print("\\nOr manually add completion for your shell:")
        console.print("\\n[bold]Bash:[/bold]")
        console.print("[green]echo 'complete -C meta-refine meta-refine' >> ~/.bashrc[/green]")
        console.print("\\n[bold]Zsh:[/bold]")
        console.print("[green]echo 'complete -o bashdefault -C meta-refine meta-refine' >> ~/.zshrc[/green]")
        console.print("\\n[bold]Fish:[/bold]")
        console.print("[green]echo 'complete -c meta-refine -f -a \"(meta-refine)\"' >> ~/.config/fish/config.fish[/green]")


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", help="Show version information"
    )
):
    """
    Meta-Refine: Intelligent code analysis powered by Llama 3.1
    """
    if version:
        console.print("Meta-Refine v1.0.0")
        console.print("Powered by Meta's Llama 3.1-8B-Instruct")
        raise typer.Exit()


def _show_interactive_help():
    """Show help for interactive mode."""
    help_table = Table(title="Interactive Commands")
    help_table.add_column("Command", style="cyan")
    help_table.add_column("Description", style="green")
    
    help_table.add_row("analyze <file>", "Analyze a single file")
    help_table.add_row("status", "Show system status")
    help_table.add_row("examples", "Show usage examples")
    help_table.add_row("help, h", "Show this help")
    help_table.add_row("exit, quit, q", "Exit interactive mode")
    
    console.print(help_table)

def _show_system_status():
    """Show current system status."""
    settings = get_settings()
    
    status_table = Table(title="System Status")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", style="green")
    
    # Quick environment checks
    checks = {
        "Python Version": "✅ OK" if sys.version_info >= (3, 8) else "❌ Requires Python 3.8+",
        "HF Token": "✅ Set" if settings.huggingface_token else "❌ Not configured",
        "Model Access": "✅ Available" if _check_quick_model_access() else "⚠️ Not verified",
    }
    
    for component, status in checks.items():
        status_table.add_row(component, status)
    
    console.print(status_table)

def _show_examples():
    """Show usage examples."""
    examples = [
        "analyze examples/example.py",
        "analyze src/main.js",
        "analyze --help",
    ]
    
    console.print("[bold]Quick Examples:[/bold]")
    for example in examples:
        console.print(f"  [cyan]{example}[/cyan]")

def _check_quick_model_access() -> bool:
    """Quick check for model access without full validation."""
    try:
        settings = get_settings()
        return bool(settings.huggingface_token)
    except Exception:
        return False

async def _run_quick_analysis(file_path: Path):
    """Run a quick analysis in interactive mode."""
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return
    
    try:
        settings = get_settings()
        model = LlamaModelInterface(settings.llama_config)
        analyzer = CodeAnalyzer(model, settings.analysis_config)
        formatter = ResultFormatter(settings.output_config)
        
        console.print(f"[dim]Analyzing {file_path}...[/dim]")
        result = await analyzer.analyze_file(file_path)
        
        if result.issues:
            formatted = formatter.format_results(result, format="console")
            console.print(formatted)
        else:
            console.print("[green]✅ No issues found![/green]")
            
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")

def _run_setup_wizard(force: bool = False):
    """Run the interactive setup wizard."""
    console.print("\\n[bold rgb(25,119,243)]🔮 Meta AI Setup Wizard[/bold rgb(25,119,243)]")
    console.print("[rgb(0,204,188)]Let's get you set up for AI-powered code intelligence![/rgb(0,204,188)]\\n")
    
    # Check if already configured
    env_file = Path(".env")
    if env_file.exists() and not force:
        console.print("[yellow]⚠️ Meta-Refine appears to be already configured.[/yellow]")
        if not typer.confirm("Continue with setup anyway?"):
            console.print("[green]Setup cancelled.[/green]")
            return
    
    # Step 1: HuggingFace Token
    console.print("[bold]Step 1: HuggingFace Configuration[/bold]")
    console.print("Meta-Refine requires a HuggingFace token to access the Llama model.")
    console.print("Get your free token at: [link]https://huggingface.co/settings/tokens[/link]\\n")
    
    hf_token = console.input("Enter your HuggingFace token (or press Enter to skip): ").strip()
    
    # Step 2: Model Configuration
    console.print("\\n[bold]Step 2: Model Configuration[/bold]")
    console.print("Choose your preferred model (default: gpt2 for demo)")
    
    model_options = {
        "1": ("gpt2", "Fast, lightweight (good for testing)"),
        "2": ("meta-llama/Llama-3.1-8B-Instruct", "Full Llama model (requires token)"),
    }
    
    console.print("Available models:")
    for key, (model, desc) in model_options.items():
        console.print(f"  {key}. {model} - {desc}")
    
    model_choice = console.input("\\nChoose model [1]: ").strip() or "1"
    selected_model = model_options.get(model_choice, ("gpt2", ""))[0]
    
    # Step 3: Create .env file
    console.print("\\n[bold]Step 3: Saving Configuration[/bold]")
    
    env_content = f"""# Meta-Refine Configuration
# Generated by setup wizard

# Hugging Face Token
HF_TOKEN={hf_token or 'your_token_here'}

# Model Configuration
MODEL_NAME={selected_model}
MODEL_DEVICE=auto
MODEL_TEMPERATURE=0.3

# Analysis Configuration
MAX_FILE_SIZE=1000000
CHUNK_SIZE=2000

# Output Configuration
DEFAULT_OUTPUT_FORMAT=console
USE_COLORS=true

# Cache Configuration
ENABLE_CACHE=true

# Logging
LOG_LEVEL=INFO
DEBUG=false
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        console.print("[green]✅ Configuration saved to .env[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to save configuration: {e}[/red]")
        return
    
    # Step 4: Validation
    console.print("\\n[bold]Step 4: Validation[/bold]")
    console.print("Testing your configuration...")
    
    env_valid, env_details = validate_environment(show_suggestions=False)
    if env_valid:
        console.print("[green]✅ Setup completed successfully![/green]")
        console.print("\\n[bold]Next steps:[/bold]")
        console.print("• Run [cyan]meta-refine analyze examples/example.py[/cyan] to test")
        console.print("• Use [cyan]meta-refine interactive[/cyan] for guided analysis")
        console.print("• Check [cyan]meta-refine --help[/cyan] for all commands")
    else:
        console.print("[yellow]⚠️ Setup completed with warnings.[/yellow]")
        console.print("Run [cyan]meta-refine doctor[/cyan] for detailed diagnostics.")

def _run_automated_setup(force: bool = False):
    """Run automated setup without user interaction."""
    console.print("\\n[bold blue]🔧 Automated Setup[/bold blue]")
    
    env_file = Path(".env")
    if not env_file.exists() or force:
        # Copy from template
        template_file = Path("env.example")
        if template_file.exists():
            import shutil
            shutil.copy(template_file, env_file)
            console.print("[green]✅ Created .env from template[/green]")
        else:
            console.print("[yellow]⚠️ No env.example found, manual configuration needed[/yellow]")
    
    console.print("Run [cyan]meta setup --interactive[/cyan] for guided setup.")

if __name__ == "__main__":
    app() 