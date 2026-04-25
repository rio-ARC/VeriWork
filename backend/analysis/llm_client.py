"""
LLM Client - AI Integration
Contribution Truth

Handles all communication with the Groq API.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from groq import AsyncGroq, Groq

# Load environment variables from .env file
load_dotenv()


class LLMClient:
    """
    Client for interacting with the Groq API.
    
    Handles long-context reasoning and structured output parsing.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM client."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Set it as an environment variable or pass it to the constructor."
            )
            
        self.async_client = AsyncGroq(api_key=self.api_key)
        self.sync_client = Groq(api_key=self.api_key)
    
    async def analyze(self, prompt: str, context: str = "") -> str:
        """
        Send a prompt to the LLM for analysis.
        
        Args:
            prompt: The analysis prompt
            context: Additional context (evidence data)
        
        Returns:
            LLM's response text
        """
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n---\n\n{prompt}"
            
        messages = [
            {
                "role": "user",
                "content": full_prompt,
            }
        ]
        
        try:
            response = await self.async_client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.3,
                max_tokens=8192,
                top_p=0.95,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API error: {e}")
            raise
    
    def analyze_sync(self, prompt: str, context: str = "") -> str:
        """
        Synchronous version of analyze for simpler use cases.
        """
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n---\n\n{prompt}"
            
        messages = [
            {
                "role": "user",
                "content": full_prompt,
            }
        ]
        
        try:
            response = self.sync_client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.3,
                max_tokens=8192,
                top_p=0.95,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API error: {e}")
            raise
    
    async def structured_analysis(
        self,
        task: str,
        evidence: str,
        output_format: str
    ) -> str:
        """
        Perform analysis with structured output format.
        
        Args:
            task: What to analyze or verify
            evidence: The evidence data to analyze
            output_format: Description of expected output format (e.g., JSON schema)
        
        Returns:
            LLM's response in the requested format
        """
        prompt = f"""Task: {task}

Evidence Data:
{evidence}

Output Format:
{output_format}

Provide your analysis in the exact format specified above. Be thorough and cite specific evidence."""

        return await self.analyze(prompt)


# Singleton instance for easy access
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the LLM client singleton."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def is_llm_configured() -> bool:
    """Check if LLM API is configured."""
    return bool(os.environ.get("GROQ_API_KEY"))
