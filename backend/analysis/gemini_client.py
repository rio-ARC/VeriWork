"""
Gemini Client - AI Integration
Contribution Truth

Handles all communication with Google's Gemini API.
"""

import os
from typing import Optional

import google.generativeai as genai


class GeminiClient:
    """
    Client for interacting with Google's Gemini API.
    
    Handles long-context reasoning and structured output parsing.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini client."""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it as an environment variable or pass it to the constructor."
            )
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.0 Flash for fast, capable analysis
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": 0.3,  # Lower for more deterministic analysis
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
    
    async def analyze(self, prompt: str, context: str = "") -> str:
        """
        Send a prompt to Gemini for analysis.
        
        Args:
            prompt: The analysis prompt
            context: Additional context (evidence data)
        
        Returns:
            Gemini's response text
        """
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n---\n\n{prompt}"
        
        try:
            response = await self.model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise
    
    def analyze_sync(self, prompt: str, context: str = "") -> str:
        """
        Synchronous version of analyze for simpler use cases.
        """
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n---\n\n{prompt}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
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
            Gemini's response in the requested format
        """
        prompt = f"""Task: {task}

Evidence Data:
{evidence}

Output Format:
{output_format}

Provide your analysis in the exact format specified above. Be thorough and cite specific evidence."""

        return await self.analyze(prompt)


# Singleton instance for easy access
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


def is_gemini_configured() -> bool:
    """Check if Gemini API is configured."""
    return bool(os.environ.get("GEMINI_API_KEY"))
