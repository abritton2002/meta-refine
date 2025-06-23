"""
Llama 3.1 Model Interface for Meta-Refine

Handles model loading, prompt engineering, and inference for code analysis.
"""

import logging
import time
from typing import Dict, List, Optional, Union, Any
try:
    import torch
    from transformers import (
        AutoTokenizer, 
        AutoModelForCausalLM, 
        BitsAndBytesConfig,
        pipeline
    )
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None
from huggingface_hub import login
import warnings

from .config import ModelConfig

warnings.filterwarnings("ignore", category=UserWarning)
logger = logging.getLogger(__name__)


class LlamaModelInterface:
    """Interface for Meta's Llama 3.1-8B-Instruct model."""
    
    def __init__(self, config: ModelConfig):
        """Initialize the model interface with configuration."""
        if not HAS_TORCH:
            raise RuntimeError("PyTorch not available. For remote inference, set REMOTE_SERVER_URL in .env")
        
        self.config = config
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._device = self._determine_device()
        
        logger.info(f"Initializing Llama model on device: {self._device}")
        self._load_model()
    
    def _determine_device(self) -> str:
        """Determine the best available device."""
        if self.config.device != "auto":
            return self.config.device
        
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _create_quantization_config(self):
        """Create quantization configuration if needed."""
        if not HAS_TORCH:
            return None
            
        try:
            if self.config.load_in_4bit:
                logger.info("Enabling 4-bit quantization to reduce memory usage")
                return BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif self.config.load_in_8bit:
                logger.info("Enabling 8-bit quantization to reduce memory usage")
                return BitsAndBytesConfig(load_in_8bit=True)
        except Exception as e:
            logger.warning(f"Quantization setup failed: {e}")
            logger.info("Falling back to full precision (may require more memory)")
        return None
    
    def _load_model(self):
        """Load the Llama model and tokenizer."""
        try:
            # Login to Hugging Face if token is provided
            if hasattr(self.config, 'huggingface_token') and self.config.huggingface_token:
                login(token=self.config.huggingface_token)
            
            logger.info(f"Loading model: {self.config.model_name}")
            logger.debug(f"Model config details: {self.config}")
            
            # Optimize download with progress tracking and resume capability
            import os
            os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'  # Use faster hf-transfer
            
            # Load tokenizer first (smaller download)
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=True,
                use_fast=True
            )
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Configure model loading parameters with download optimizations
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": self._get_torch_dtype(),
                "device_map": "auto",  # Always use auto device mapping for efficiency
                "low_cpu_mem_usage": True,
                "resume_download": True,  # Resume interrupted downloads
                "local_files_only": False,  # Allow downloads from HuggingFace
                "cache_dir": None,  # Use default cache location
                "offload_folder": "/tmp/meta_refine_offload",  # Offload to disk if needed
            }
            
            # Add quantization config if specified
            quantization_config = self._create_quantization_config()
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
                logger.info("Using quantization to reduce memory usage")
            
            # Load model with progress indication
            logger.info(f"Loading model weights... This may take several minutes for first download.")
            logger.info(f"Model will be cached at: ~/.cache/huggingface/hub/")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                **model_kwargs
            )
            
            # Device mapping is handled automatically by device_map="auto"
            # No need to manually move to device
            
            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self._device == "cuda" else -1,
                torch_dtype=self._get_torch_dtype(),
                do_sample=self.config.do_sample,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_new_tokens=1024,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def _get_torch_dtype(self):
        """Get the appropriate torch dtype."""
        if not HAS_TORCH:
            return None
            
        if self.config.torch_dtype == "float16":
            return torch.float16
        elif self.config.torch_dtype == "bfloat16":
            return torch.bfloat16
        elif self.config.torch_dtype == "auto":
            return torch.float16 if self._device == "cuda" else torch.float32
        else:
            return torch.float32
    
    def _create_analysis_prompt(
        self, 
        code: str, 
        language: str, 
        analysis_type: str = "comprehensive",
        context: Optional[str] = None
    ) -> str:
        """Create a specialized prompt for code analysis."""
        
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
    
    def _create_security_prompt(self, code: str, language: str) -> str:
        """Create a specialized prompt for security analysis."""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a cybersecurity expert specializing in secure code review. Analyze the provided {language} code for security vulnerabilities and provide specific remediation steps.

Focus specifically on:
- SQL injection vulnerabilities
- Cross-site scripting (XSS) 
- Authentication and authorization flaws
- Input validation issues
- Cryptographic weaknesses
- Race conditions and concurrency issues
- Memory safety issues
- Secrets and credentials exposure
- Path traversal vulnerabilities
- Denial of service vulnerabilities

For each security issue:
- Specify exact location and vulnerable code
- Explain the attack vector and potential impact
- Provide secure alternative implementation
- Rate severity using CVSS-like scale (CRITICAL/HIGH/MEDIUM/LOW)

Be thorough but focus only on actual security concerns.<|eot_id|><|start_header_id|>user<|end_header_id|>

Analyze this {language} code for security vulnerabilities:

```{language}
{code}
```<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    def _create_performance_prompt(self, code: str, language: str) -> str:
        """Create a specialized prompt for performance analysis."""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a performance optimization expert. Analyze the provided {language} code for performance bottlenecks and optimization opportunities.

Focus on:
- Algorithmic complexity (Big O analysis)
- Memory usage optimization
- Database query efficiency
- Caching opportunities
- Unnecessary computations
- Loop optimizations
- Data structure choices
- I/O optimization
- Concurrency and parallelization opportunities

For each optimization:
- Identify the performance issue
- Estimate current complexity/performance impact
- Suggest specific optimization with expected improvement
- Provide optimized code example where helpful

Be specific about measurable performance gains.<|eot_id|><|start_header_id|>user<|end_header_id|>

Analyze this {language} code for performance optimization opportunities:

```{language}
{code}
```<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        analysis_type: str = "comprehensive",
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Analyze code using the Llama model.
        
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
            # Create appropriate prompt based on analysis type
            if analysis_type == "security":
                prompt = self._create_security_prompt(code, language)
            elif analysis_type == "performance":
                prompt = self._create_performance_prompt(code, language)
            else:
                prompt = self._create_analysis_prompt(code, language, analysis_type, context)
            
            # Log prompt for debugging
            logger.debug(f"Generated prompt for {analysis_type} analysis")
            
            # Generate response
            start_time = time.time()
            
            response = self.pipeline(
                prompt,
                max_new_tokens=kwargs.get('max_tokens', 1024),
                temperature=kwargs.get('temperature', self.config.temperature),
                top_p=kwargs.get('top_p', self.config.top_p),
                top_k=kwargs.get('top_k', self.config.top_k),
                do_sample=kwargs.get('do_sample', self.config.do_sample),
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
                length_penalty=1.0,
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Analysis completed in {generation_time:.2f}s")
            
            # Extract generated text
            if isinstance(response, list) and len(response) > 0:
                generated_text = response[0].get('generated_text', '')
                # Remove the prompt from the response
                assistant_response = generated_text.split('<|start_header_id|>assistant<|end_header_id|>')[-1]
                return assistant_response.strip()
            
            return "Error: No response generated"
            
        except Exception as e:
            logger.error(f"Error during code analysis: {e}")
            return f"Error during analysis: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.model:
            return {"status": "Model not loaded"}
        
        try:
            model_size = sum(p.numel() for p in self.model.parameters())
            
            return {
                "model_name": self.config.model_name,
                "device": self._device,
                "dtype": str(self.model.dtype) if hasattr(self.model, 'dtype') else "unknown",
                "parameters": f"{model_size:,}",
                "memory_usage": self._get_memory_usage(),
                "quantization": {
                    "4bit": self.config.load_in_4bit,
                    "8bit": self.config.load_in_8bit,
                },
                "config": {
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                    "top_k": self.config.top_k,
                    "max_length": self.config.max_length,
                }
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"status": "Error retrieving model info", "error": str(e)}
    
    def _get_memory_usage(self) -> str:
        """Get current memory usage."""
        try:
            if self._device == "cuda" and torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                cached = torch.cuda.memory_reserved() / 1024**3  # GB
                return f"GPU: {allocated:.2f}GB allocated, {cached:.2f}GB cached"
            else:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024**2
                return f"RAM: {memory_mb:.2f}MB"
        except Exception:
            return "Unknown"
    
    def cleanup(self):
        """Clean up model resources."""
        try:
            if self.model:
                del self.model
            if self.tokenizer:
                del self.tokenizer
            if self.pipeline:
                del self.pipeline
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info("Model resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 