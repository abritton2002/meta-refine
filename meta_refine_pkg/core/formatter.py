"""
Output Formatting for Meta-Refine

Handles formatting analysis results into various output formats including
console, JSON, HTML, and Markdown reports.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax
from rich.markdown import Markdown

from .analyzer import AnalysisResult
from .config import OutputConfig

logger = logging.getLogger(__name__)


class ResultFormatter:
    """Formats analysis results into various output formats."""
    
    def __init__(self, config: OutputConfig):
        self.config = config
        self.console = Console()
        
        # Severity icons and colors
        self.severity_styles = {
            'CRITICAL': {'icon': '🚨', 'color': 'red', 'style': 'bold red'},
            'HIGH': {'icon': '⚠️', 'color': 'orange3', 'style': 'bold orange3'},
            'MEDIUM': {'icon': '⚡', 'color': 'yellow', 'style': 'bold yellow'},
            'LOW': {'icon': '💡', 'color': 'blue', 'style': 'bold blue'},
            'INFO': {'icon': 'ℹ️', 'color': 'green', 'style': 'green'},
        }
    
    def format_results(
        self,
        results: Union[AnalysisResult, List[AnalysisResult]],
        format: str = "console",
        severity: str = "all",
        output_file: Optional[Path] = None,
        **kwargs
    ) -> str:
        """
        Format analysis results in the specified format.
        
        Args:
            results: Single result or list of results to format
            format: Output format (console, json, html, markdown)
            severity: Minimum severity to include (critical, high, medium, low, all)
            output_file: File to save output to (optional)
            
        Returns:
            Formatted output as string
        """
        # Normalize to list
        if isinstance(results, AnalysisResult):
            results = [results]
        
        # Filter by severity
        filtered_results = self._filter_by_severity(results, severity)
        
        # Format based on type
        if format == "console":
            output = self._format_console(filtered_results)
        elif format == "json":
            output = self._format_json(filtered_results)
        elif format == "html":
            output = self._format_html(filtered_results)
        elif format == "markdown":
            output = self._format_markdown(filtered_results)
        elif format == "xml":
            output = self._format_xml(filtered_results)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save to file if specified
        if output_file:
            self._save_to_file(output, output_file, format)
        
        return output
    
    def _filter_by_severity(
        self, 
        results: List[AnalysisResult], 
        severity: str
    ) -> List[AnalysisResult]:
        """Filter results by minimum severity level."""
        if severity == "all":
            return results
        
        severity_levels = {
            'critical': ['CRITICAL'],
            'high': ['CRITICAL', 'HIGH'],
            'medium': ['CRITICAL', 'HIGH', 'MEDIUM'],
            'low': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        }
        
        allowed_severities = severity_levels.get(severity.lower(), [])
        
        filtered_results = []
        for result in results:
            filtered_issues = [
                issue for issue in result.issues 
                if issue.get('severity', 'LOW') in allowed_severities
            ]
            if filtered_issues:
                # Create a copy with filtered issues
                filtered_result = AnalysisResult(result.file_path, result.language)
                filtered_result.issues = filtered_issues
                filtered_result.metadata = result.metadata
                filtered_result.analysis_time = result.analysis_time
                filtered_result.timestamp = result.timestamp
                filtered_results.append(filtered_result)
        
        return filtered_results
    
    def _format_console(self, results: List[AnalysisResult]) -> str:
        """Format results for console output with Rich formatting."""
        if not results:
            return self._create_no_issues_panel()
        
        output_parts = []
        
        # Summary
        total_issues = sum(len(r.issues) for r in results)
        total_files = len(results)
        
        summary_text = f"📊 Analysis Summary: {total_issues} issues found in {total_files} files"
        output_parts.append(Panel(summary_text, style="bold blue", title="🔍 Meta-Refine Analysis"))
        
        # Results for each file
        for result in results:
            if result.issues:
                output_parts.append(self._format_file_console(result))
        
        # Overall statistics
        output_parts.append(self._create_statistics_table(results))
        
        # Render all parts
        console = Console(file=None, width=120)
        with console.capture() as capture:
            for part in output_parts:
                console.print(part)
                console.print()  # Add spacing
        
        return capture.get()
    
    def _create_no_issues_panel(self) -> Panel:
        """Create a panel for when no issues are found."""
        return Panel(
            "✅ No issues found! Your code looks great.",
            style="bold green",
            title="🎉 Clean Analysis"
        )
    
    def _format_file_console(self, result: AnalysisResult) -> Panel:
        """Format a single file's results for console."""
        # Create file header
        file_info = f"📁 [bold cyan]{result.file_path}[/bold cyan] ({result.language})"
        
        if result.metadata:
            metrics = result.metadata
            file_info += f"\n📊 {metrics.get('total_lines', 0)} lines, "
            file_info += f"{metrics.get('function_count', 0)} functions, "
            file_info += f"complexity: {metrics.get('complexity_estimate', 0)}"
        
        # Group issues by severity
        issues_by_severity = {}
        for issue in result.issues:
            severity = issue.get('severity', 'LOW')
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        # Create issue tree
        tree = Tree(file_info)
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            if severity in issues_by_severity:
                issues = issues_by_severity[severity]
                style_info = self.severity_styles.get(severity, self.severity_styles['INFO'])
                
                severity_branch = tree.add(
                    f"{style_info['icon']} [bold]{severity}[/bold] ({len(issues)} issues)",
                    style=style_info['style']
                )
                
                for issue in issues:
                    line_info = f"Line {issue.get('line', '?')}"
                    description = issue.get('description', 'No description')
                    
                    issue_text = f"[dim]{line_info}:[/dim] {description}"
                    issue_branch = severity_branch.add(issue_text)
                    
                    # Add suggestion if available
                    suggestion = issue.get('suggestion', '').strip()
                    if suggestion:
                        issue_branch.add(f"💡 [green]{suggestion}[/green]")
        
        return Panel(tree, title=f"🔍 Analysis Results", border_style="blue")
    
    def _create_statistics_table(self, results: List[AnalysisResult]) -> Table:
        """Create a statistics table."""
        table = Table(title="📈 Analysis Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Calculate statistics
        total_files = len(results)
        total_issues = sum(len(r.issues) for r in results)
        total_time = sum(r.analysis_time for r in results)
        
        # Severity breakdown
        severity_counts = {}
        for result in results:
            for issue in result.issues:
                severity = issue.get('severity', 'LOW')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Language breakdown
        language_counts = {}
        for result in results:
            lang = result.language
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # Add rows
        table.add_row("Total Files Analyzed", str(total_files))
        table.add_row("Total Issues Found", str(total_issues))
        table.add_row("Average Issues per File", f"{total_issues/total_files:.1f}" if total_files > 0 else "0")
        table.add_row("Total Analysis Time", f"{total_time:.2f}s")
        table.add_row("Average Time per File", f"{total_time/total_files:.2f}s" if total_files > 0 else "0s")
        
        table.add_section()
        table.add_row("Critical Issues", str(severity_counts.get('CRITICAL', 0)))
        table.add_row("High Priority Issues", str(severity_counts.get('HIGH', 0)))
        table.add_row("Medium Priority Issues", str(severity_counts.get('MEDIUM', 0)))
        table.add_row("Low Priority Issues", str(severity_counts.get('LOW', 0)))
        
        if language_counts:
            table.add_section()
            for lang, count in sorted(language_counts.items()):
                table.add_row(f"{lang.title()} Files", str(count))
        
        return table
    
    def _format_json(self, results: List[AnalysisResult]) -> str:
        """Format results as JSON."""
        json_data = {
            "meta_refine_analysis": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "summary": self._generate_summary(results),
                "files": []
            }
        }
        
        for result in results:
            file_data = {
                "file_path": str(result.file_path),
                "language": result.language,
                "analysis_time": result.analysis_time,
                "timestamp": result.timestamp,
                "metadata": result.metadata,
                "issues": result.issues,
                "summary": result.get_summary()
            }
            json_data["meta_refine_analysis"]["files"].append(file_data)
        
        return json.dumps(json_data, indent=2, default=str)
    
    def _format_html(self, results: List[AnalysisResult]) -> str:
        """Format results as HTML report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meta-Refine Analysis Report</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { background: #e3f2fd; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
        .file-result { margin-bottom: 30px; border: 1px solid #ddd; border-radius: 8px; }
        .file-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }
        .issue { padding: 10px; border-left: 4px solid; margin: 5px 0; }
        .critical { border-left-color: #f44336; background: #ffebee; }
        .high { border-left-color: #ff9800; background: #fff3e0; }
        .medium { border-left-color: #ffeb3b; background: #fffde7; }
        .low { border-left-color: #2196f3; background: #e3f2fd; }
        .severity-badge { padding: 2px 8px; border-radius: 4px; color: white; font-size: 12px; font-weight: bold; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Meta-Refine Analysis Report</h1>
            <p>Generated on {timestamp}</p>
        </div>
        
        <div class="summary">
            <h2>📊 Summary</h2>
            <div class="stats-grid">
                {summary_stats}
            </div>
        </div>
        
        {file_results}
    </div>
</body>
</html>
        """
        
        # Generate summary stats
        total_files = len(results)
        total_issues = sum(len(r.issues) for r in results)
        severity_counts = {}
        for result in results:
            for issue in result.issues:
                severity = issue.get('severity', 'LOW')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary_stats = ""
        summary_stats += f'<div class="stat-card"><h3>{total_files}</h3><p>Files Analyzed</p></div>'
        summary_stats += f'<div class="stat-card"><h3>{total_issues}</h3><p>Total Issues</p></div>'
        summary_stats += f'<div class="stat-card"><h3>{severity_counts.get("CRITICAL", 0)}</h3><p>Critical Issues</p></div>'
        summary_stats += f'<div class="stat-card"><h3>{severity_counts.get("HIGH", 0)}</h3><p>High Priority</p></div>'
        
        # Generate file results
        file_results = ""
        for result in results:
            if result.issues:
                file_results += self._format_file_html(result)
        
        return html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary_stats=summary_stats,
            file_results=file_results
        )
    
    def _format_file_html(self, result: AnalysisResult) -> str:
        """Format a single file's results as HTML."""
        html = f"""
        <div class="file-result">
            <div class="file-header">
                <h3>📁 {result.file_path}</h3>
                <p><strong>Language:</strong> {result.language} | 
                   <strong>Issues:</strong> {len(result.issues)} | 
                   <strong>Analysis Time:</strong> {result.analysis_time:.2f}s</p>
            </div>
            <div class="file-issues">
        """
        
        for issue in result.issues:
            severity = issue.get('severity', 'LOW').lower()
            severity_badge = f'<span class="severity-badge" style="background-color: {self._get_severity_color(severity)}">{severity.upper()}</span>'
            
            html += f"""
            <div class="issue {severity}">
                <div>
                    {severity_badge}
                    <strong>Line {issue.get('line', '?')}:</strong> {issue.get('description', 'No description')}
                </div>
                """
            
            suggestion = issue.get('suggestion', '').strip()
            if suggestion:
                html += f'<div style="margin-top: 8px; color: #28a745;"><strong>💡 Suggestion:</strong> {suggestion}</div>'
            
            html += "</div>"
        
        html += "</div></div>"
        return html
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            'critical': '#f44336',
            'high': '#ff9800',
            'medium': '#ffeb3b',
            'low': '#2196f3',
            'info': '#4caf50'
        }
        return colors.get(severity, '#6c757d')
    
    def _format_markdown(self, results: List[AnalysisResult]) -> str:
        """Format results as Markdown."""
        md_content = []
        
        # Header
        md_content.append("# 🚀 Meta-Refine Analysis Report")
        md_content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        md_content.append("")
        
        # Summary
        summary = self._generate_summary(results)
        md_content.append("## 📊 Summary")
        md_content.append("")
        md_content.append(f"- **Files Analyzed:** {summary['total_files']}")
        md_content.append(f"- **Total Issues:** {summary['total_issues']}")
        md_content.append(f"- **Critical Issues:** {summary['severity_breakdown'].get('CRITICAL', 0)}")
        md_content.append(f"- **High Priority Issues:** {summary['severity_breakdown'].get('HIGH', 0)}")
        md_content.append(f"- **Analysis Time:** {summary['total_analysis_time']:.2f}s")
        md_content.append("")
        
        # File results
        for result in results:
            if result.issues:
                md_content.extend(self._format_file_markdown(result))
        
        return "\n".join(md_content)
    
    def _format_file_markdown(self, result: AnalysisResult) -> List[str]:
        """Format a single file's results as Markdown."""
        md_lines = []
        
        md_lines.append(f"## 📁 {result.file_path}")
        md_lines.append("")
        md_lines.append(f"**Language:** {result.language} | **Issues:** {len(result.issues)} | **Analysis Time:** {result.analysis_time:.2f}s")
        md_lines.append("")
        
        # Group by severity
        issues_by_severity = {}
        for issue in result.issues:
            severity = issue.get('severity', 'LOW')
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            if severity in issues_by_severity:
                icon = self.severity_styles[severity]['icon']
                md_lines.append(f"### {icon} {severity} Issues")
                md_lines.append("")
                
                for issue in issues_by_severity[severity]:
                    md_lines.append(f"- **Line {issue.get('line', '?')}:** {issue.get('description', 'No description')}")
                    suggestion = issue.get('suggestion', '').strip()
                    if suggestion:
                        md_lines.append(f"  - 💡 *Suggestion: {suggestion}*")
                
                md_lines.append("")
        
        return md_lines
    
    def _format_xml(self, results: List[AnalysisResult]) -> str:
        """Format results as XML."""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<meta_refine_analysis>')
        xml_lines.append(f'  <timestamp>{datetime.now().isoformat()}</timestamp>')
        xml_lines.append('  <summary>')
        
        summary = self._generate_summary(results)
        xml_lines.append(f'    <total_files>{summary["total_files"]}</total_files>')
        xml_lines.append(f'    <total_issues>{summary["total_issues"]}</total_issues>')
        xml_lines.append('  </summary>')
        
        xml_lines.append('  <files>')
        for result in results:
            xml_lines.append('    <file>')
            xml_lines.append(f'      <path>{result.file_path}</path>')
            xml_lines.append(f'      <language>{result.language}</language>')
            xml_lines.append('      <issues>')
            
            for issue in result.issues:
                xml_lines.append('        <issue>')
                xml_lines.append(f'          <severity>{issue.get("severity", "LOW")}</severity>')
                xml_lines.append(f'          <line>{issue.get("line", 1)}</line>')
                xml_lines.append(f'          <description><![CDATA[{issue.get("description", "")}]]></description>')
                xml_lines.append(f'          <suggestion><![CDATA[{issue.get("suggestion", "")}]]></suggestion>')
                xml_lines.append('        </issue>')
            
            xml_lines.append('      </issues>')
            xml_lines.append('    </file>')
        
        xml_lines.append('  </files>')
        xml_lines.append('</meta_refine_analysis>')
        
        return '\n'.join(xml_lines)
    
    def _generate_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_files = len(results)
        total_issues = sum(len(r.issues) for r in results)
        total_time = sum(r.analysis_time for r in results)
        
        severity_breakdown = {}
        language_breakdown = {}
        
        for result in results:
            # Count by severity
            for issue in result.issues:
                severity = issue.get('severity', 'LOW')
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
            
            # Count by language
            lang = result.language
            language_breakdown[lang] = language_breakdown.get(lang, 0) + 1
        
        return {
            'total_files': total_files,
            'total_issues': total_issues,
            'total_analysis_time': total_time,
            'average_issues_per_file': total_issues / total_files if total_files > 0 else 0,
            'average_time_per_file': total_time / total_files if total_files > 0 else 0,
            'severity_breakdown': severity_breakdown,
            'language_breakdown': language_breakdown,
        }
    
    def _save_to_file(self, content: str, file_path: Path, format: str):
        """Save formatted output to file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Results saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save results to {file_path}: {e}")
            raise 