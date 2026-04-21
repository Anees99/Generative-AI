"""
Cost Tracker Module - Token Counting & USD Cost Estimation

This module provides transparent cost tracking for LLM API calls
using tiktoken for precise token counting.

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Tracks and estimates costs for LLM API usage.
    
    Features:
    - Precise token counting with tiktoken
    - USD cost estimation per model
    - Session-wide cost accumulation
    - Detailed logging for transparency
    """
    
    # Cost per million tokens (USD) - Updated regularly
    # Source: Official provider pricing pages
    MODEL_COSTS = {
        # OpenAI models
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-4': {'input': 30.00, 'output': 60.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
        
        # Google Gemini models (approximate)
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
        'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
        'gemini-pro': {'input': 0.50, 'output': 1.50},
    }
    
    def __init__(self, default_model: str = 'gpt-4o-mini'):
        """
        Initialize the cost tracker.
        
        Args:
            default_model: Default model to use for cost calculations
        """
        self.default_model = default_model
        self.session_costs = []
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        
        logger.info(f"CostTracker initialized with default model: {default_model}")
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in a text string using tiktoken.
        
        Args:
            text: Text to tokenize
            model: Model to use for tokenization (uses default if not specified)
            
        Returns:
            Number of tokens
        """
        model = model or self.default_model
        
        try:
            import tiktoken
            
            # Try to get encoding for the model
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base for unknown models (works for most GPT-4/GPT-3.5)
                encoding = tiktoken.get_encoding('cl100k_base')
                logger.debug(f"Using fallback encoding for model: {model}")
            
            token_count = len(encoding.encode(text))
            logger.debug(f"Token count for {len(text)} chars: {token_count} tokens")
            return token_count
            
        except ImportError:
            logger.warning("tiktoken not installed, using character-based estimation")
            # Fallback: estimate 1 token ≈ 4 characters
            return len(text) // 4
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback estimation
            return len(text) // 4
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """
        Calculate USD cost for a given number of tokens.
        
        Args:
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            model: Model name for pricing
            
        Returns:
            Cost in USD
        """
        model = model or self.default_model
        
        # Get pricing for model
        pricing = self.MODEL_COSTS.get(model)
        if not pricing:
            # Try to find similar model
            for key in self.MODEL_COSTS:
                if model.startswith(key.split('-')[0]):
                    pricing = self.MODEL_COSTS[key]
                    break
            
            if not pricing:
                logger.warning(f"Unknown model '{model}', using gpt-4o-mini pricing")
                pricing = self.MODEL_COSTS['gpt-4o-mini']
        
        # Calculate cost
        input_cost = (input_tokens * pricing['input']) / 1_000_000
        output_cost = (output_tokens * pricing['output']) / 1_000_000
        total_cost = input_cost + output_cost
        
        logger.debug(
            f"Cost calculation for {model}: "
            f"{input_tokens} input + {output_tokens} output = ${total_cost:.6f}"
        )
        
        return total_cost
    
    def track_api_call(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None,
        endpoint: str = '',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track an API call and accumulate costs.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model used
            endpoint: API endpoint called
            metadata: Additional metadata
            
        Returns:
            Dictionary with cost details
        """
        model = model or self.default_model
        cost = self.calculate_cost(input_tokens, output_tokens, model)
        total_tokens = input_tokens + output_tokens
        
        # Create tracking record
        record = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'endpoint': endpoint,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'cost_usd': cost,
            'metadata': metadata or {}
        }
        
        # Accumulate totals
        self.session_costs.append(record)
        self.total_tokens += total_tokens
        self.total_cost_usd += cost
        
        logger.info(
            f"API call tracked: {model} - {total_tokens} tokens - ${cost:.6f}"
        )
        
        return record
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked API calls in current session.
        
        Returns:
            Dictionary with session statistics
        """
        # Group by model
        model_breakdown = {}
        for record in self.session_costs:
            model = record['model']
            if model not in model_breakdown:
                model_breakdown[model] = {
                    'calls': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            model_breakdown[model]['calls'] += 1
            model_breakdown[model]['tokens'] += record['total_tokens']
            model_breakdown[model]['cost'] += record['cost_usd']
        
        return {
            'total_calls': len(self.session_costs),
            'total_tokens': self.total_tokens,
            'total_cost_usd': round(self.total_cost_usd, 6),
            'model_breakdown': {
                model: {
                    'calls': data['calls'],
                    'tokens': data['tokens'],
                    'cost': round(data['cost'], 6)
                }
                for model, data in model_breakdown.items()
            },
            'average_cost_per_call': round(
                self.total_cost_usd / max(len(self.session_costs), 1), 6
            )
        }
    
    def estimate_analysis_cost(
        self,
        job_description_length: int,
        resume_length: int,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost for analyzing a job posting before making API call.
        
        Args:
            job_description_length: Length of job description in characters
            resume_length: Length of resume in characters
            model: Model to use for estimation
            
        Returns:
            Dictionary with cost estimate
        """
        model = model or self.default_model
        
        # Estimate tokens (rough approximation)
        prompt_tokens = self.count_tokens(
            'x' * (job_description_length + resume_length),
            model
        )
        
        # Estimate output tokens (typically 500-1500 for analysis)
        estimated_output_tokens = 1000
        
        # Calculate estimated cost
        estimated_cost = self.calculate_cost(
            prompt_tokens,
            estimated_output_tokens,
            model
        )
        
        return {
            'estimated_input_tokens': prompt_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'estimated_total_tokens': prompt_tokens + estimated_output_tokens,
            'estimated_cost_usd': round(estimated_cost, 6),
            'model': model
        }
    
    def reset_session(self):
        """Reset session tracking."""
        self.session_costs = []
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        logger.info("CostTracker session reset")
    
    def get_pricing_info(self) -> Dict[str, Dict[str, float]]:
        """Get current pricing information for all supported models."""
        return self.MODEL_COSTS.copy()


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    tracker = CostTracker()
    
    # Test token counting
    sample_text = "This is a sample job description for testing purposes."
    tokens = tracker.count_tokens(sample_text)
    print(f"Tokens in sample text: {tokens}")
    
    # Test cost calculation
    cost = tracker.calculate_cost(1000, 500, 'gpt-4o-mini')
    print(f"Cost for 1000 input + 500 output tokens: ${cost:.6f}")
    
    # Test estimation
    estimate = tracker.estimate_analysis_cost(5000, 3000)
    print(f"Estimated analysis cost: ${estimate['estimated_cost_usd']:.6f}")
    
    # Track some calls
    tracker.track_api_call(1000, 500, 'gpt-4o-mini', '/analyze')
    tracker.track_api_call(800, 400, 'gpt-4o-mini', '/tailor')
    
    # Get summary
    summary = tracker.get_session_summary()
    print(f"Session summary: {summary}")
