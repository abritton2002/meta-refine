"""
Remote Client for Meta-Refine

Connects to a remote Meta-Refine server (like running on Colab)
and provides the same interface as the local model.
"""

import asyncio
import logging
import requests
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class RemoteModelInterface:
    """Client interface that connects to remote Meta-Refine server."""
    
    def __init__(self, server_url: str):
        """Initialize remote client."""
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 300  # 5 minute timeout for analysis
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to remote server."""
        try:
            response = self.session.get(f"{self.server_url}/health")
            response.raise_for_status()
            
            health = response.json()
            if health['status'] != 'healthy':
                raise RuntimeError(f"Server not ready: {health}")
            
            logger.info(f"✅ Connected to remote Meta-Refine server")
            
        except Exception as e:
            raise RuntimeError(f"Failed to connect to server {self.server_url}: {e}")
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        analysis_type: str = "comprehensive",
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Analyze code using remote server.
        
        Args:
            code: Source code to analyze
            language: Programming language
            analysis_type: Type of analysis (comprehensive, security, performance)
            context: Additional context about the code
            **kwargs: Additional generation parameters
            
        Returns:
            Analysis results as formatted text
        """
        try:
            payload = {
                'code': code,
                'language': language,
                'filename': f'temp.{self._get_extension(language)}',
                'options': {
                    'suggestions': analysis_type in ['comprehensive', 'suggestions'],
                    'performance': analysis_type in ['comprehensive', 'performance'],
                    'security': analysis_type in ['comprehensive', 'security'],
                    'cache': kwargs.get('cache', True)
                }
            }
            
            logger.debug(f"Sending analysis request to {self.server_url}/analyze")
            start_time = time.time()
            
            response = self.session.post(
                f"{self.server_url}/analyze",
                json=payload
            )
            response.raise_for_status()
            
            analysis_time = time.time() - start_time
            logger.info(f"Remote analysis completed in {analysis_time:.2f}s")
            
            result = response.json()
            
            # Convert back to string format for compatibility
            issues = result.get('issues', [])
            if not issues:
                return "No significant issues found."
            
            # Format issues as structured text
            formatted_response = ""
            for issue in issues:
                formatted_response += f"""
SEVERITY: {issue['severity']}
LINE: {issue['line']}
ISSUE: {issue['description']}
IMPACT: {issue.get('impact', 'Unknown impact')}
SOLUTION: {issue.get('suggestion', 'No solution provided')}

"""
            
            return formatted_response.strip()
            
        except Exception as e:
            logger.error(f"Error during remote analysis: {e}")
            return f"Error during analysis: {str(e)}"
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rs'
        }
        return extensions.get(language, 'txt')
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the remote model."""
        try:
            response = self.session.get(f"{self.server_url}/model-info")
            response.raise_for_status()
            
            info = response.json()
            info['connection'] = 'remote'
            info['server_url'] = self.server_url
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"status": "Error retrieving remote model info", "error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.session.close()
            logger.info("Remote client cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


class RemoteAnalyzer:
    """Analyzer that works with remote model interface."""
    
    def __init__(self, model_interface: RemoteModelInterface, config):
        self.model = model_interface
        self.config = config
        logger.info("Remote analyzer initialized")
    
    async def analyze_file(
        self,
        file_path: Path,
        language: Optional[str] = None,
        include_suggestions: bool = True,
        include_performance: bool = True,
        include_security: bool = True,
        cache: bool = True,
        **kwargs
    ):
        """Analyze a single file using remote server."""
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        except Exception as e:
            raise RuntimeError(f"Could not read file {file_path}: {e}")
        
        # Detect language if not provided
        if not language:
            language = self._detect_language(file_path)
        
        # Send to remote server
        payload = {
            'code': code,
            'language': language,
            'filename': file_path.name,
            'options': {
                'suggestions': include_suggestions,
                'performance': include_performance,
                'security': include_security,
                'cache': cache
            }
        }
        
        try:
            response = self.model.session.post(
                f"{self.model.server_url}/analyze",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Convert to local AnalysisResult format
            from meta_refine_pkg.core.analyzer import AnalysisResult
            analysis_result = AnalysisResult(file_path, language)
            analysis_result.issues = result.get('issues', [])
            analysis_result.metadata = result.get('metadata', {})
            analysis_result.analysis_time = result.get('analysis_time', 0)
            analysis_result.timestamp = result.get('timestamp', time.time())
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            # Return empty result on error
            from meta_refine_pkg.core.analyzer import AnalysisResult
            analysis_result = AnalysisResult(file_path, language)
            analysis_result.add_issue(
                "error", "HIGH", 1,
                f"Remote analysis failed: {str(e)}",
                "Check connection to remote server"
            )
            return analysis_result
    
    async def analyze_project(
        self,
        project_path: Path,
        include_suggestions: bool = True,
        include_performance: bool = True,
        include_security: bool = True,
        cache: bool = True,
        **kwargs
    ):
        """Analyze multiple files in a project."""
        
        # Find all supported files
        supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'}
        files_to_analyze = []
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                files_to_analyze.append(file_path)
        
        logger.info(f"Found {len(files_to_analyze)} files to analyze")
        
        # Analyze each file
        results = []
        for file_path in files_to_analyze:
            try:
                result = await self.analyze_file(
                    file_path,
                    include_suggestions=include_suggestions,
                    include_performance=include_performance,
                    include_security=include_security,
                    cache=cache
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                continue
        
        return results
    
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
            '.rs': 'rust'
        }
        
        return extension_map.get(file_path.suffix.lower(), 'text')