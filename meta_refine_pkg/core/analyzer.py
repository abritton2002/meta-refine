"""
Code Analysis Engine for Meta-Refine

Handles file parsing, language detection, code chunking, and analysis orchestration.
"""

import asyncio
import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import hashlib
import time

# Language-specific parsers
try:
    import libcst as cst
    HAS_LIBCST = True
except ImportError:
    HAS_LIBCST = False

from .config import AnalysisConfig
from .model import LlamaModelInterface

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Container for analysis results."""
    
    def __init__(self, file_path: Path, language: str):
        self.file_path = file_path
        self.language = language
        self.timestamp = time.time()
        self.issues = []
        self.suggestions = []
        self.performance_issues = []
        self.security_issues = []
        self.documentation_issues = []
        self.metadata = {}
        self.analysis_time = 0.0
        self.model_response = ""
    
    def add_issue(self, issue_type: str, severity: str, line: int, description: str, 
                  suggestion: str = "", impact: str = ""):
        """Add an issue to the results."""
        self.issues.append({
            "type": issue_type,
            "severity": severity,
            "line": line,
            "description": description,
            "suggestion": suggestion,
            "impact": impact,
            "timestamp": time.time()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis results."""
        severity_counts = {}
        for issue in self.issues:
            severity = issue.get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "file": str(self.file_path),
            "language": self.language,
            "total_issues": len(self.issues),
            "severity_breakdown": severity_counts,
            "analysis_time": self.analysis_time,
            "timestamp": self.timestamp
        }


class CodeAnalyzer:
    """Main code analysis engine."""
    
    def __init__(self, model: LlamaModelInterface, config: AnalysisConfig):
        self.model = model
        self.config = config
        self.cache = {}  # Simple in-memory cache
        
        logger.info("Code analyzer initialized")
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.cs': 'csharp',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, 'unknown')
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if a file should be analyzed based on patterns."""
        file_str = str(file_path)
        
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if self._matches_pattern(file_str, pattern):
                return False
        
        # Check include patterns
        for pattern in self.config.include_patterns:
            if self._matches_pattern(file_str, pattern):
                return True
        
        return False
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file matches a glob-like pattern."""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)
    
    def _chunk_code(self, code: str, language: str) -> List[Tuple[str, int]]:
        """Split large code files into analyzable chunks with intelligent context preservation."""
        lines = code.split('\n')
        
        # For smaller files, analyze as single chunk
        if len(lines) <= self.config.chunk_size:
            return [(code, 1)]
        
        # Use AST-based chunking for Python
        if language == 'python':
            return self._chunk_python_ast(code)
        
        # Fallback to line-based chunking for other languages
        return self._chunk_by_lines(lines)
    
    def _chunk_python_ast(self, code: str) -> List[Tuple[str, int]]:
        """Chunk Python code using AST analysis for better semantic boundaries."""
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            chunks = []
            
            # Extract top-level nodes (classes, functions, imports)
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno
                    end_line = getattr(node, 'end_lineno', start_line + 20)  # Fallback
                    
                    # Add some context before and after
                    context_before = max(1, start_line - 5)
                    context_after = min(len(lines), end_line + 5)
                    
                    chunk_lines = lines[context_before-1:context_after]
                    chunk_content = '\n'.join(chunk_lines)
                    
                    if len(chunk_content.strip()) > 0:
                        chunks.append((chunk_content, context_before))
            
            # If no major structures found, fall back to line chunking
            if not chunks:
                return self._chunk_by_lines(lines)
            
            return chunks
            
        except SyntaxError:
            # Fall back to line-based chunking if AST parsing fails
            return self._chunk_by_lines(lines)
    
    def _chunk_by_lines(self, lines: List[str]) -> List[Tuple[str, int]]:
        """Chunk code by lines with logical boundaries."""
        chunks = []
        current_chunk = []
        chunk_start_line = 1
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_line = i + 1
            
            # Check if we should create a chunk
            should_break = (
                len(current_chunk) >= self.config.chunk_size or 
                self._is_logical_break(line, lines, i)
            )
            
            if should_break and len(current_chunk) > 10:  # Minimum chunk size
                chunk_content = '\n'.join(current_chunk)
                chunks.append((chunk_content, chunk_start_line))
                
                # Prepare for next chunk with overlap
                if self.config.chunk_overlap > 0:
                    overlap_start = max(0, len(current_chunk) - self.config.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:]
                    chunk_start_line = current_line - self.config.chunk_overlap + 1
                else:
                    current_chunk = []
                    chunk_start_line = current_line + 1
        
        # Add remaining lines as final chunk
        if current_chunk:
            chunks.append(('\n'.join(current_chunk), chunk_start_line))
        
        return chunks if chunks else [(('\n'.join(lines)), 1)]
    
    def _is_logical_break(self, line: str, all_lines: List[str], index: int) -> bool:
        """Determine if this is a good place to break for Python code."""
        stripped = line.strip()
        
        # Class or function definitions
        if stripped.startswith(('class ', 'def ', 'async def ')):
            return True
        
        # Empty lines followed by class/def
        if not stripped and index + 1 < len(all_lines):
            next_line = all_lines[index + 1].strip()
            if next_line.startswith(('class ', 'def ', 'async def ')):
                return True
        
        return False
    
    def _parse_python_ast(self, code: str) -> Optional[ast.AST]:
        """Parse Python code to AST for deeper analysis."""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Python syntax error: {e}")
            return None
    
    def _extract_code_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Extract basic code metrics."""
        lines = code.split('\n')
        
        metrics = {
            "total_lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "comment_lines": self._count_comment_lines(lines, language),
            "function_count": self._count_functions(code, language),
            "class_count": self._count_classes(code, language),
            "complexity_estimate": self._estimate_complexity(code, language)
        }
        
        return metrics
    
    def _count_comment_lines(self, lines: List[str], language: str) -> int:
        """Count comment lines based on language."""
        comment_chars = {
            'python': '#',
            'javascript': '//',
            'typescript': '//',
            'java': '//',
            'cpp': '//',
            'c': '//',
            'go': '//',
            'rust': '//',
            'php': '//',
            'ruby': '#',
        }
        
        char = comment_chars.get(language, '#')
        return len([l for l in lines if l.strip().startswith(char)])
    
    def _count_functions(self, code: str, language: str) -> int:
        """Count function definitions."""
        if language == 'python':
            return len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
        elif language in ['javascript', 'typescript']:
            return len(re.findall(r'function\s+\w+|=>\s*{|^\s*\w+\s*:\s*function', code, re.MULTILINE))
        elif language == 'java':
            return len(re.findall(r'^\s*public\s+.*?\s+\w+\s*\(|^\s*private\s+.*?\s+\w+\s*\(', code, re.MULTILINE))
        else:
            return 0
    
    def _count_classes(self, code: str, language: str) -> int:
        """Count class definitions."""
        if language == 'python':
            return len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
        elif language == 'java':
            return len(re.findall(r'^\s*public\s+class\s+\w+|^\s*class\s+\w+', code, re.MULTILINE))
        elif language in ['javascript', 'typescript']:
            return len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
        else:
            return 0
    
    def _estimate_complexity(self, code: str, language: str) -> int:
        """Rough cyclomatic complexity estimate."""
        complexity_keywords = {
            'python': ['if', 'elif', 'while', 'for', 'except', 'and', 'or'],
            'javascript': ['if', 'else if', 'while', 'for', 'catch', '&&', '||'],
            'java': ['if', 'else if', 'while', 'for', 'catch', '&&', '||'],
        }
        
        keywords = complexity_keywords.get(language, ['if', 'while', 'for'])
        complexity = 1  # Base complexity
        
        for keyword in keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', code))
        
        return complexity
    
    def _generate_cache_key(self, code: str, language: str, analysis_options: Dict) -> str:
        """Generate a cache key for the analysis."""
        content = f"{code}{language}{str(sorted(analysis_options.items()))}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def analyze_file(
        self,
        file_path: Path,
        language: Optional[str] = None,
        include_suggestions: bool = True,
        include_performance: bool = True,
        include_security: bool = True,
        cache: bool = True,
        **kwargs
    ) -> AnalysisResult:
        """
        Analyze a single code file.
        
        Args:
            file_path: Path to the code file
            language: Programming language (auto-detected if None)
            include_suggestions: Include improvement suggestions
            include_performance: Include performance analysis
            include_security: Include security analysis
            cache: Use caching for results
            
        Returns:
            AnalysisResult containing all findings
        """
        start_time = time.time()
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Detect language
            if not language:
                language = self._detect_language(file_path)
            
            if language not in self.config.supported_languages:
                logger.warning(f"Unsupported language: {language}")
                # Create empty result
                result = AnalysisResult(file_path, language)
                result.analysis_time = time.time() - start_time
                return result
            
            # Check file size
            if len(code.encode('utf-8')) > self.config.max_file_size:
                logger.warning(f"File too large: {file_path}")
                result = AnalysisResult(file_path, language)
                result.add_issue(
                    "size", "HIGH", 1, 
                    f"File exceeds maximum size limit ({self.config.max_file_size} bytes)",
                    "Consider splitting into smaller modules"
                )
                result.analysis_time = time.time() - start_time
                return result
            
            # Create result container
            result = AnalysisResult(file_path, language)
            
            # Extract basic metrics
            result.metadata = self._extract_code_metrics(code, language)
            
            # Check cache
            analysis_options = {
                'suggestions': include_suggestions,
                'performance': include_performance,
                'security': include_security
            }
            cache_key = self._generate_cache_key(code, language, analysis_options)
            
            if cache and cache_key in self.cache:
                logger.info(f"Using cached analysis for {file_path}")
                cached_result = self.cache[cache_key]
                cached_result.file_path = file_path  # Update path
                cached_result.analysis_time = time.time() - start_time
                return cached_result
            
            # Chunk code if necessary
            chunks = self._chunk_code(code, language)
            logger.info(f"Analyzing {len(chunks)} chunks for {file_path}")
            
            # Analyze each chunk
            for chunk_code, start_line in chunks:
                chunk_result = await self._analyze_chunk(
                    chunk_code, language, start_line,
                    include_suggestions, include_performance, include_security
                )
                
                # Merge results
                result.issues.extend(chunk_result.get('issues', []))
                result.model_response += chunk_result.get('response', '') + "\n\n"
            
            # Post-process results
            self._deduplicate_issues(result)
            self._sort_issues_by_severity(result)
            
            # Limit suggestions per file
            if len(result.issues) > self.config.max_suggestions_per_file:
                result.issues = result.issues[:self.config.max_suggestions_per_file]
            
            result.analysis_time = time.time() - start_time
            
            # Cache result
            if cache:
                self.cache[cache_key] = result
            
            logger.info(f"Analysis complete for {file_path}: {len(result.issues)} issues found")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            result = AnalysisResult(file_path, language or 'unknown')
            result.add_issue(
                "error", "HIGH", 1,
                f"Analysis failed: {str(e)}",
                "Check file syntax and accessibility"
            )
            result.analysis_time = time.time() - start_time
            return result
    
    async def _analyze_chunk(
        self, 
        code: str, 
        language: str, 
        start_line: int,
        include_suggestions: bool,
        include_performance: bool,
        include_security: bool
    ) -> Dict[str, Any]:
        """Analyze a single code chunk."""
        try:
            # Comprehensive analysis
            response = await self.model.analyze_code(
                code, language, "comprehensive"
            )
            
            logger.debug(f"Model response: {response[:200]}...")  # Log first 200 chars
            
            issues = self._parse_model_response(response, start_line)
            
            logger.debug(f"Parsed {len(issues)} issues from response")
            
            return {
                'issues': issues,
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Error analyzing chunk: {e}")
            return {
                'issues': [],
                'response': f"Analysis error: {str(e)}"
            }
    
    def _parse_model_response(self, response: str, line_offset: int = 0) -> List[Dict]:
        """Parse the model's response to extract structured issues."""
        issues = []
        
        # Handle "No significant issues found" response
        if "no significant issues found" in response.lower() or "no issues found" in response.lower():
            return issues
        
        # Parse structured format: SEVERITY:, LINE:, ISSUE:, IMPACT:, SOLUTION:
        issue_blocks = re.split(r'(?=SEVERITY:)', response, flags=re.IGNORECASE | re.MULTILINE)
        
        for block in issue_blocks:
            if not block.strip():
                continue
                
            issue = self._parse_issue_block(block, line_offset)
            if issue:
                issues.append(issue)
        
        # Fallback to legacy parsing if structured format not found
        if not issues:
            issues = self._parse_legacy_response(response, line_offset)
        
        return issues
    
    def _parse_issue_block(self, block: str, line_offset: int = 0) -> Optional[Dict]:
        """Parse a single issue block in structured format."""
        try:
            issue = {}
            
            # Extract severity
            severity_match = re.search(r'SEVERITY:\s*([A-Z]+)', block, re.IGNORECASE)
            if severity_match:
                issue['severity'] = severity_match.group(1).upper()
            else:
                return None
            
            # Extract line number
            line_match = re.search(r'LINE:\s*(\d+)', block, re.IGNORECASE)
            if line_match:
                issue['line'] = int(line_match.group(1)) + line_offset
            else:
                issue['line'] = 1 + line_offset
            
            # Extract issue description
            issue_match = re.search(r'ISSUE:\s*(.+?)(?=IMPACT:|SOLUTION:|$)', block, re.IGNORECASE | re.DOTALL)
            if issue_match:
                issue['description'] = issue_match.group(1).strip()
            else:
                issue['description'] = 'Unknown issue'
            
            # Extract impact
            impact_match = re.search(r'IMPACT:\s*(.+?)(?=SOLUTION:|$)', block, re.IGNORECASE | re.DOTALL)
            if impact_match:
                issue['impact'] = impact_match.group(1).strip()
            else:
                issue['impact'] = 'Unknown impact'
            
            # Extract solution
            solution_match = re.search(r'SOLUTION:\s*(.+?)$', block, re.IGNORECASE | re.DOTALL)
            if solution_match:
                issue['suggestion'] = solution_match.group(1).strip()
            else:
                issue['suggestion'] = 'No solution provided'
            
            # Determine issue type based on content
            issue['type'] = self._categorize_issue(issue['description'])
            issue['timestamp'] = time.time()
            
            return issue
            
        except Exception as e:
            logger.warning(f"Error parsing issue block: {e}")
            return None
    
    def _categorize_issue(self, description: str) -> str:
        """Categorize issue based on description keywords."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ['security', 'sql injection', 'xss', 'vulnerability', 'authentication', 'authorization']):
            return 'security'
        elif any(keyword in description_lower for keyword in ['performance', 'slow', 'inefficient', 'optimize', 'memory', 'cpu']):
            return 'performance'
        elif any(keyword in description_lower for keyword in ['bug', 'error', 'exception', 'crash', 'null', 'undefined']):
            return 'bug'
        elif any(keyword in description_lower for keyword in ['style', 'naming', 'convention', 'format']):
            return 'style'
        elif any(keyword in description_lower for keyword in ['documentation', 'comment', 'docstring']):
            return 'documentation'
        else:
            return 'general'
    
    def _parse_legacy_response(self, response: str, line_offset: int = 0) -> List[Dict]:
        """Legacy parsing for unstructured responses."""
        issues = []
        lines = response.split('\n')
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for severity indicators
            severity_match = re.search(r'\b(CRITICAL|HIGH|MEDIUM|LOW)\b', line, re.IGNORECASE)
            if severity_match:
                if current_issue:
                    issues.append(current_issue)
                current_issue = {
                    'severity': severity_match.group(1).upper(),
                    'description': line,
                    'line': self._extract_line_number(line) + line_offset,
                    'type': 'general',
                    'suggestion': '',
                    'impact': ''
                }
            
            # Look for line numbers
            line_match = re.search(r'line\s+(\d+)', line, re.IGNORECASE)
            if line_match and current_issue:
                current_issue['line'] = int(line_match.group(1)) + line_offset
            
            # Accumulate description
            if current_issue and line and not severity_match:
                if 'suggestion' in line.lower() or 'fix' in line.lower():
                    current_issue['suggestion'] += ' ' + line
                else:
                    current_issue['description'] += ' ' + line
        
        # Add final issue
        if current_issue:
            issues.append(current_issue)
        
        return issues
    
    def _extract_line_number(self, text: str) -> int:
        """Extract line number from text."""
        match = re.search(r'line\s+(\d+)', text, re.IGNORECASE)
        return int(match.group(1)) if match else 1
    
    def _deduplicate_issues(self, result: AnalysisResult):
        """Remove duplicate issues from results."""
        seen = set()
        unique_issues = []
        
        for issue in result.issues:
            key = (issue.get('line', 0), issue.get('type', ''), issue.get('description', ''))
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        result.issues = unique_issues
    
    def _sort_issues_by_severity(self, result: AnalysisResult):
        """Sort issues by severity level."""
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        
        result.issues.sort(key=lambda x: (
            severity_order.get(x.get('severity', 'INFO'), 4),
            x.get('line', 0)
        ))
    
    async def analyze_project(
        self,
        project_path: Path,
        language: Optional[str] = None,
        include_suggestions: bool = True,
        include_performance: bool = True,
        include_security: bool = True,
        parallel: bool = True,
        cache: bool = True,
        **kwargs
    ) -> List[AnalysisResult]:
        """
        Analyze an entire project directory.
        
        Args:
            project_path: Path to the project directory
            language: Target language filter (None for all)
            include_suggestions: Include improvement suggestions
            include_performance: Include performance analysis
            include_security: Include security analysis
            parallel: Use parallel processing
            cache: Use caching for results
            
        Returns:
            List of AnalysisResult objects for each analyzed file
        """
        logger.info(f"Starting project analysis: {project_path}")
        
        # Find files to analyze
        files_to_analyze = []
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and self._should_analyze_file(file_path):
                if not language or self._detect_language(file_path) == language:
                    files_to_analyze.append(file_path)
        
        logger.info(f"Found {len(files_to_analyze)} files to analyze")
        
        if not files_to_analyze:
            logger.warning("No files found to analyze")
            return []
        
        # Analyze files
        if parallel and len(files_to_analyze) > 1:
            # Parallel analysis
            tasks = [
                self.analyze_file(
                    file_path, language, include_suggestions,
                    include_performance, include_security, cache
                )
                for file_path in files_to_analyze
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = [r for r in results if isinstance(r, AnalysisResult)]
            logger.info(f"Completed parallel analysis of {len(valid_results)} files")
            return valid_results
        else:
            # Sequential analysis
            results = []
            for file_path in files_to_analyze:
                result = await self.analyze_file(
                    file_path, language, include_suggestions,
                    include_performance, include_security, cache
                )
                results.append(result)
            
            logger.info(f"Completed sequential analysis of {len(results)} files")
            return results 