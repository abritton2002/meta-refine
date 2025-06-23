"""
Hugging Face Inference API Client for Meta-Refine
Uses HF's serverless inference API for Meta Llama models
"""

import os
import logging
import requests
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HFInferenceClient:
    """Client for Hugging Face Inference API."""
    
    def __init__(self, model_name: str, hf_token: str):
        """Initialize HF Inference client."""
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info(f"Initialized HF Inference API for {model_name}")
    
    def _wait_for_model(self, max_wait: int = 300) -> bool:
        """Wait for model to be ready (cold start can take time)."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Send a simple test request
                response = self.session.post(
                    self.api_url,
                    json={
                        "inputs": "Hello",
                        "parameters": {"max_new_tokens": 1}
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info("Model is ready!")
                    return True
                elif response.status_code == 503:
                    # Model loading
                    logger.info("Model loading, waiting...")
                    time.sleep(20)
                    continue
                else:
                    logger.warning(f"Unexpected response: {response.status_code}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Waiting for model: {e}")
                time.sleep(10)
        
        return False
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        analysis_type: str = "comprehensive",
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Analyze code using HF Inference API."""
        try:
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(code, language, analysis_type, context)
            
            # Prepare request
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": kwargs.get('max_tokens', 1024),
                    "temperature": kwargs.get('temperature', 0.3),
                    "top_p": kwargs.get('top_p', 0.9),
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            logger.info("Sending request to HF Inference API...")
            start_time = time.time()
            
            # Make request with retries for cold start
            for attempt in range(3):
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    logger.info(f"Model loading (attempt {attempt + 1}/3), waiting...")
                    if not self._wait_for_model():
                        return "Error: Model failed to load after waiting"
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return f"API Error: {response.status_code}"
            
            analysis_time = time.time() - start_time
            logger.info(f"Analysis completed in {analysis_time:.2f}s")
            
            # Parse response
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                return generated_text.strip()
            else:
                return "No response generated"
                
        except Exception as e:
            logger.error(f"HF Inference API error: {e}")
            return f"Error during analysis: {str(e)}"
    
    def _create_analysis_prompt(
        self,
        code: str,
        language: str,
        analysis_type: str = "comprehensive",
        context: Optional[str] = None
    ) -> str:
        """Create analysis prompt for Llama model."""
        
        base_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are Claude Code, an expert AI programming assistant. You provide comprehensive code analysis with the precision and depth that developers expect from professional code review tools.

ANALYSIS REQUIREMENTS:
1. **Identify Real Issues**: Don't report style preferences as bugs. Focus on actual problems.
2. **Be Specific**: Reference exact line numbers and code sections.
3. **Provide Context**: Explain WHY something is an issue and what could go wrong.
4. **Actionable Solutions**: Give concrete, implementable fixes.
5. **Proper Severity**: Use CRITICAL for security/crashes, HIGH for bugs, MEDIUM for maintainability, LOW for style.

FOCUS AREAS:
• **Bugs & Logic Errors**: Null pointer exceptions, type errors, logic flaws, edge cases
• **Security Vulnerabilities**: SQL injection, XSS, authentication bypass, data exposure
• **Performance Issues**: Inefficient algorithms, memory leaks, unnecessary operations
• **Code Quality**: Dead code, code smells, architectural issues, maintainability
• **Best Practices**: Language-specific conventions, error handling, testing gaps

OUTPUT FORMAT:
For each issue, provide:
```
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
LINE: [specific line number or range]
ISSUE: [clear description of the problem]
IMPACT: [what could go wrong]
SOLUTION: [specific fix or improvement]
```

IMPORTANT: Only report actual issues. If code is well-written, say "No significant issues found."<|eot_id|><|start_header_id|>user<|end_header_id|>

Analyze this {language} code for bugs, security vulnerabilities, performance issues, and code quality problems:

```{language}
{code}
```

{f"Context: {context}" if context else ""}

Provide a thorough analysis following the format above.<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return base_prompt
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "api_url": self.api_url,
            "deployment": "Hugging Face Inference API",
            "status": "Connected"
        }