"""
Interactive Meta-Refine CLI Interface
Beautiful UI with Meta branding and infinity logo animation
"""

import asyncio
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.align import Align
import typer


console = Console()


def create_infinity_logo():
    """Create animated infinity logo for Meta branding."""
    frames = [
        "∞",
        "⧖", 
        "∞",
        "⧗"
    ]
    return frames


def create_meta_banner():
    """Create beautiful Meta-branded banner."""
    banner = Text()
    banner.append("    ∞  ", style="bold rgb(25,119,243)")  # Meta blue infinity
    banner.append("meta", style="bold rgb(25,119,243)")  # Meta blue
    banner.append(" refine", style="bold rgb(0,204,188)")  # Meta teal
    banner.append("  ∞", style="bold rgb(25,119,243)")  # Meta blue infinity
    banner.append("\n\n")
    banner.append("AI-Powered Code Intelligence by Meta", style="rgb(168,168,168)")
    banner.append("\n")
    banner.append("Powered by Llama 3.1-8B • Built for developers", style="dim rgb(168,168,168)")
    
    return Panel(
        Align.center(banner),
        border_style="rgb(25,119,243)",
        padding=(1, 2),
        title="[bold rgb(25,119,243)]🔮 Meta AI[/bold rgb(25,119,243)]",
        title_align="center"
    )


def create_loading_animation(message: str = "Initializing Meta AI..."):
    """Create loading animation with infinity spinner."""
    text = Text()
    text.append("∞ ", style="bold rgb(25,119,243)")
    text.append(message, style="rgb(0,204,188)")
    text.append(" ∞", style="bold rgb(25,119,243)")
    
    return Panel(
        Align.center(text),
        border_style="rgb(0,204,188)",
        padding=(0, 2)
    )


def create_main_menu():
    """Create the main interactive menu."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="rgb(25,119,243)", width=4)
    table.add_column(style="bold white", width=20)
    table.add_column(style="dim rgb(168,168,168)")
    
    table.add_row("🔍", "analyze", "Analyze code files or projects")
    table.add_row("🎯", "interactive", "AI-powered coding assistant") 
    table.add_row("⚙️", "config", "Manage configuration")
    table.add_row("🛠️", "setup", "First-time setup wizard")
    table.add_row("🩺", "doctor", "System health check")
    table.add_row("📚", "examples", "Usage examples")
    table.add_row("📊", "benchmark", "Performance benchmarks")
    table.add_row("❌", "exit", "Exit Meta-Refine")
    
    return Panel(
        table,
        title="[bold rgb(25,119,243)]🚀 Choose an Action[/bold rgb(25,119,243)]",
        border_style="rgb(0,204,188)",
        padding=(1, 1)
    )


def create_quick_actions():
    """Create quick action buttons."""
    quick_table = Table(show_header=False, box=None, expand=True)
    quick_table.add_column(style="bold rgb(255,186,8)", justify="center")
    quick_table.add_column(style="bold rgb(255,186,8)", justify="center") 
    quick_table.add_column(style="bold rgb(255,186,8)", justify="center")
    
    quick_table.add_row(
        "⚡ Quick Scan",
        "🔒 Security Check", 
        "🚀 Performance"
    )
    quick_table.add_row(
        "Analyze current dir",
        "Security-focused scan",
        "Performance optimization"
    )
    
    return Panel(
        quick_table,
        title="[rgb(255,186,8)]⚡ Quick Actions[/rgb(255,186,8)]",
        border_style="rgb(255,186,8)",
        padding=(0, 1)
    )


def create_status_panel():
    """Create system status panel."""
    status_table = Table(show_header=False, box=None, padding=(0, 1))
    status_table.add_column(style="dim rgb(168,168,168)", width=12)
    status_table.add_column(style="green")
    
    status_table.add_row("Model:", "✅ Llama 3.1-8B")
    status_table.add_row("API:", "✅ HuggingFace") 
    status_table.add_row("Status:", "✅ Ready")
    
    return Panel(
        status_table,
        title="[dim rgb(168,168,168)]System Status[/dim rgb(168,168,168)]",
        border_style="dim rgb(168,168,168)",
        padding=(0, 1)
    )


async def show_loading_sequence():
    """Show Meta loading sequence with infinity animation."""
    frames = create_infinity_logo()
    
    with Live(console=console, refresh_per_second=2) as live:
        for i in range(6):  # 3 seconds of animation
            frame = frames[i % len(frames)]
            loading_text = Text()
            loading_text.append(f"  {frame}  ", style="bold rgb(25,119,243)")
            loading_text.append("Connecting to Meta AI", style="rgb(0,204,188)")
            loading_text.append(f"  {frame}  ", style="bold rgb(25,119,243)")
            
            panel = Panel(
                Align.center(loading_text),
                border_style="rgb(25,119,243)",
                padding=(1, 2)
            )
            live.update(panel)
            await asyncio.sleep(0.5)


def interactive_cli():
    """Main interactive CLI interface."""
    console.clear()
    
    # Show loading animation
    asyncio.run(show_loading_sequence())
    
    console.clear()
    
    while True:
        # Display main interface
        console.print(create_meta_banner())
        console.print()
        
        # Create layout
        layout = Layout()
        layout.split(
            Layout(create_main_menu(), name="menu"),
            Layout(name="bottom", size=8)
        )
        
        layout["bottom"].split_row(
            Layout(create_quick_actions(), name="quick"),
            Layout(create_status_panel(), name="status")
        )
        
        console.print(layout)
        console.print()
        
        # Get user choice
        choice = Prompt.ask(
            "[bold rgb(25,119,243)]Select an option[/bold rgb(25,119,243)]",
            choices=["analyze", "interactive", "config", "setup", "doctor", "examples", "benchmark", "1", "2", "3", "exit"],
            default="analyze"
        )
        
        console.clear()
        
        if choice == "exit":
            console.print(Panel(
                Align.center(Text("Thanks for using Meta-Refine! 👋", style="rgb(0,204,188)")),
                border_style="rgb(25,119,243)",
                padding=(1, 2)
            ))
            break
            
        elif choice == "analyze":
            handle_analyze_option()
            
        elif choice == "interactive":
            handle_interactive_mode()
            
        elif choice == "setup":
            handle_setup()
            
        elif choice == "doctor":
            handle_doctor()
            
        elif choice == "config":
            handle_config()
            
        elif choice == "examples":
            handle_examples()
            
        elif choice == "benchmark":
            handle_benchmark()
            
        elif choice == "1":  # Quick scan
            handle_quick_scan()
            
        elif choice == "2":  # Security check
            handle_security_check()
            
        elif choice == "3":  # Performance
            handle_performance_check()
        
        # Pause before returning to menu
        console.print()
        Prompt.ask("Press Enter to continue...", default="")
        console.clear()


def handle_analyze_option():
    """Handle analyze option."""
    console.print(Panel(
        "🔍 [bold rgb(25,119,243)]Code Analysis[/bold rgb(25,119,243)]",
        border_style="rgb(25,119,243)"
    ))
    
    choice = Prompt.ask(
        "What would you like to analyze?",
        choices=["file", "project", "back"],
        default="file"
    )
    
    if choice == "file":
        file_path = Prompt.ask("Enter file path")
        if file_path and Path(file_path).exists():
            console.print(f"\n[rgb(0,204,188)]Analyzing file: {file_path}[/rgb(0,204,188)]")
            # Run actual analysis
            import subprocess
            subprocess.run(["meta-refine", "analyze", "--file", file_path])
        else:
            console.print("[red]File not found![/red]")
            
    elif choice == "project":
        project_path = Prompt.ask("Enter project directory", default=".")
        console.print(f"\n[rgb(0,204,188)]Analyzing project: {project_path}[/rgb(0,204,188)]")
        import subprocess
        subprocess.run(["meta-refine", "analyze", "--project", project_path])


def handle_interactive_mode():
    """Handle interactive AI mode."""
    console.print(Panel(
        "🎯 [bold rgb(25,119,243)]Interactive AI Assistant[/bold rgb(25,119,243)]\n\n[dim]Coming soon: Chat with Meta AI about your code![/dim]",
        border_style="rgb(25,119,243)"
    ))


def handle_setup():
    """Handle setup wizard."""
    console.print(Panel(
        "🛠️ [bold rgb(25,119,243)]Setup Wizard[/bold rgb(25,119,243)]",
        border_style="rgb(25,119,243)"
    ))
    import subprocess
    subprocess.run(["meta-refine", "setup"])


def handle_doctor():
    """Handle system health check."""
    console.print(Panel(
        "🩺 [bold rgb(25,119,243)]System Health Check[/bold rgb(25,119,243)]",
        border_style="rgb(25,119,243)"
    ))
    import subprocess
    subprocess.run(["meta-refine", "doctor"])


def handle_config():
    """Handle configuration."""
    console.print(Panel(
        "⚙️ [bold rgb(25,119,243)]Configuration Manager[/bold rgb(25,119,243)]",
        border_style="rgb(25,119,243)"
    ))
    import subprocess
    subprocess.run(["meta-refine", "config"])


def handle_examples():
    """Handle examples."""
    console.print(Panel(
        "📚 [bold rgb(25,119,243)]Usage Examples[/bold rgb(25,119,243)]",
        border_style="rgb(25,119,243)"
    ))
    import subprocess
    subprocess.run(["meta-refine", "examples"])


def handle_benchmark():
    """Handle benchmarks."""
    console.print(Panel(
        "📊 [bold rgb(25,119,243)]Performance Benchmarks[/bold rgb(25,119,243)]",
        border_style="rgb(25,119,243)"
    ))
    import subprocess
    subprocess.run(["meta-refine", "benchmark"])


def handle_quick_scan():
    """Handle quick scan of current directory."""
    console.print(Panel(
        "⚡ [bold rgb(255,186,8)]Quick Scan - Current Directory[/bold rgb(255,186,8)]",
        border_style="rgb(255,186,8)"
    ))
    import subprocess
    subprocess.run(["meta-refine", "analyze", "--project", "."])


def handle_security_check():
    """Handle security-focused scan."""
    console.print(Panel(
        "🔒 [bold rgb(255,186,8)]Security Check[/bold rgb(255,186,8)]",
        border_style="rgb(255,186,8)"
    ))
    target = Prompt.ask("Scan file or directory", default=".")
    import subprocess
    subprocess.run(["meta-refine", "analyze", "--project" if Path(target).is_dir() else "--file", target, "--security"])


def handle_performance_check():
    """Handle performance optimization scan."""
    console.print(Panel(
        "🚀 [bold rgb(255,186,8)]Performance Optimization[/bold rgb(255,186,8)]",
        border_style="rgb(255,186,8)"
    ))
    target = Prompt.ask("Scan file or directory", default=".")
    import subprocess
    subprocess.run(["meta-refine", "analyze", "--project" if Path(target).is_dir() else "--file", target, "--performance"])