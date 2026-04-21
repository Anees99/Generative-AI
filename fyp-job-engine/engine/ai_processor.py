"""
AI Processor Module - LLM Scoring & Resume Tailoring

This module handles communication with LLM providers (OpenAI/Google Gemini)
for job matching, scoring, and resume tailoring suggestions.

Supports switching between providers via LLM_PROVIDER environment variable.

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIProcessor:
    """
    AI-powered job analysis and resume tailoring processor.
    
    Supports:
    - OpenAI (gpt-4o-mini)
    - Google Gemini (gemini-1.5-flash)
    
    Provider is selected via LLM_PROVIDER environment variable.
    """
    
    # Cost per million tokens (approximate, as of 2024)
    COSTS = {
        'openai': {
            'gpt-4o-mini': {'input': 0.15, 'output': 0.60}
        },
        'google': {
            'gemini-1.5-flash': {'input': 0.075, 'output': 0.30}
        }
    }
    
    def __init__(self):
        """Initialize the AI processor with configured provider."""
        self.provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        self.api_key = None
        self.model = None
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider."""
        if self.provider == 'openai':
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAI client with model: {self.model}")
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
                
        elif self.provider == 'google':
            self.api_key = os.getenv('GOOGLE_API_KEY')
            self.model = os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash')
            if not self.api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
                logger.info(f"Initialized Google Gemini client with model: {self.model}")
            except ImportError:
                raise ImportError("Please install google-generativeai: pip install google-generativeai")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'openai' or 'google'")
    
    def analyze_job(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Analyze job description against resume and provide match score and suggestions.
        
        Args:
            job_description: Full text of the job posting
            resume_text: User's current resume text
            
        Returns:
            Dictionary containing:
            - match_score: 0-100 compatibility score
            - key_skills: List of important skills from job posting
            - missing_skills: Skills user lacks
            - tailored_bullets: Suggested resume bullet points
            - token_count: Total tokens used
            - cost_usd: Estimated cost in USD
        """
        from config.prompts import ANALYSIS_PROMPT
        
        prompt = ANALYSIS_PROMPT.format(
            job_description=job_description,
            resume_text=resume_text
        )
        
        logger.info(f"Sending job analysis request to {self.provider}/{self.model}")
        
        if self.provider == 'openai':
            response_data = self._call_openai(prompt)
        else:  # google
            response_data = self._call_gemini(prompt)
        
        # Parse the JSON response
        try:
            result = json.loads(response_data['text'])
            result['token_count'] = response_data['token_count']
            result['cost_usd'] = response_data['cost_usd']
            
            # Validate required fields
            required_fields = ['match_score', 'key_skills', 'tailored_bullets']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing field in AI response: {field}")
                    result[field] = [] if isinstance(result.get(field), list) else ''
            
            logger.info(f"Analysis complete - Score: {result.get('match_score', 'N/A')}, "
                       f"Tokens: {result['token_count']}, Cost: ${result['cost_usd']:.4f}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {response_data['text']}")
            # Return fallback structure
            return {
                'match_score': 50,
                'key_skills': [],
                'missing_skills': [],
                'tailored_bullets': [],
                'summary': response_data['text'],
                'token_count': response_data['token_count'],
                'cost_usd': response_data['cost_usd']
            }
    
    def tailor_resume(self, job_description: str, resume_text: str) -> Dict[str, Any]:
        """
        Generate a tailored version of the resume for the specific job.
        
        Args:
            job_description: Full text of the job posting
            resume_text: User's current resume text
            
        Returns:
            Dictionary containing:
            - tailored_resume: Complete tailored resume text
            - changes_made: Summary of modifications
            - token_count: Total tokens used
            - cost_usd: Estimated cost in USD
        """
        from config.prompts import TAILORING_PROMPT
        
        prompt = TAILORING_PROMPT.format(
            job_description=job_description,
            resume_text=resume_text
        )
        
        logger.info(f"Sending resume tailoring request to {self.provider}/{self.model}")
        
        if self.provider == 'openai':
            response_data = self._call_openai(prompt)
        else:  # google
            response_data = self._call_gemini(prompt)
        
        # Parse the JSON response
        try:
            result = json.loads(response_data['text'])
            result['token_count'] = response_data['token_count']
            result['cost_usd'] = response_data['cost_usd']
            
            logger.info(f"Tailoring complete - Tokens: {result['token_count']}, "
                       f"Cost: ${result['cost_usd']:.4f}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Return fallback
            return {
                'tailored_resume': response_data['text'],
                'changes_made': 'Automatic tailoring failed, using raw response',
                'token_count': response_data['token_count'],
                'cost_usd': response_data['cost_usd']
            }
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI API and return response with token/cost info.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Dictionary with text, token_count, and cost_usd
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career advisor and resume writer. "
                                  "Respond ONLY with valid JSON. No markdown, no explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            text = response.choices[0].message.content.strip()
            
            # Get token counts
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost_info = self.COSTS['openai'].get(self.model, self.COSTS['openai']['gpt-4o-mini'])
            cost_usd = (input_tokens * cost_info['input'] + output_tokens * cost_info['output']) / 1_000_000
            
            return {
                'text': text,
                'token_count': total_tokens,
                'cost_usd': cost_usd
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """
        Call Google Gemini API and return response with token/cost info.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Dictionary with text, token_count, and cost_usd
        """
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": 0.3,
                "max_output_tokens": 2000,
            }
            
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            text = response.text.strip()
            
            # Estimate tokens (Gemini doesn't always provide exact counts)
            # Rough estimate: 1 token ≈ 4 characters
            estimated_tokens = len(text) // 4 + len(prompt) // 4
            
            # Calculate cost
            cost_info = self.COSTS['google'].get(self.model, self.COSTS['google']['gemini-1.5-flash'])
            cost_usd = estimated_tokens * cost_info['input'] / 1_000_000  # Simplified: use input rate for both
            
            return {
                'text': text,
                'token_count': estimated_tokens,
                'cost_usd': cost_usd
            }
            
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            raise
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current provider configuration."""
        return {
            'provider': self.provider,
            'model': self.model,
            'costs': str(self.COSTS.get(self.provider, {}))
        }


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Check if API key is configured
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
        print("No API key configured. Set OPENAI_API_KEY or GOOGLE_API_KEY in .env file.")
    else:
        processor = AIProcessor()
        print(f"Provider: {processor.get_provider_info()}")
        
        # Test with sample data
        job_desc = "Software Engineer position requiring Python, JavaScript, and React experience."
        resume = "Experienced developer with 5 years in Python and web development."
        
        try:
            result = processor.analyze_job(job_desc, resume)
            print(f"\nMatch Score: {result['match_score']}")
            print(f"Key Skills: {result['key_skills']}")
            print(f"Cost: ${result['cost_usd']:.4f}")
        except Exception as e:
            print(f"Error during analysis: {e}")
