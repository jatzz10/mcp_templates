#!/usr/bin/env python3
"""
Gemini LLM Wrapper for JIRA MCP Server

A wrapper class that provides a consistent interface for using Google's Gemini LLM
with the JIRA MCP server. This wrapper mimics the NailLLMLangchain interface
while using Google's Generative AI library internally.

Usage:
    from gemini_llm_wrapper import GeminiLLMWrapper
    
    llm = GeminiLLMWrapper(
        model_id="gemini-2.0-flash-exp",
        temperature=0.2,
        max_tokens=600,
        api_key="your_google_api_key"
    )
    
    response = llm.invoke("Your prompt here")
"""

import os
import google.generativeai as genai
from typing import Optional, Dict, Any


class GeminiLLMWrapper:
    """
    A wrapper class for Google's Gemini LLM that provides a consistent interface
    for JIRA MCP operations.
    """
    
    def __init__(self, model_id: str, temperature: float, max_tokens: int, api_key: str):
        """
        Initialize the Gemini LLM wrapper.
        
        Args:
            model_id: The Gemini model ID to use (e.g., "gemini-2.0-flash-exp")
            temperature: Temperature for response generation (0.0 to 1.0)
            max_tokens: Maximum number of tokens in the response
            api_key: Google API key for authentication
        """
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable")
        
        # Configure the Google Generative AI library
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(model_id=model_id)
        
        # Set generation configuration
        self.generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke the Gemini model with the given prompt.
        
        Args:
            prompt: The input prompt for the model
            **kwargs: Additional arguments (for compatibility with NailLLMLangchain)
        
        Returns:
            The model's response as a string
        """
        try:
            # Generate content using the configured model
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                **kwargs
            )
            
            # Return the text content
            return response.text
            
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Gemini LLM error: {str(e)}"
            print(f"Error in GeminiLLMWrapper.invoke(): {error_msg}")
            return error_msg
    
    def get_model_info(self) -> str:
        """
        Get information about the current model configuration.
        
        Returns:
            A string describing the model configuration
        """
        return f"Gemini Model: {self.model_id} (temp: {self.temperature}, max_tokens: {self.max_tokens})"
    
    def update_config(self, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
        """
        Update the generation configuration.
        
        Args:
            temperature: New temperature value (0.0 to 1.0)
            max_tokens: New maximum tokens value
        """
        if temperature is not None:
            self.temperature = temperature
            self.generation_config.temperature = temperature
        
        if max_tokens is not None:
            self.max_tokens = max_tokens
            self.generation_config.max_output_tokens = max_tokens
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            A dictionary containing the current configuration
        """
        return {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the wrapper
    try:
        # Get API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set")
            exit(1)
        
        # Initialize the wrapper
        llm = GeminiLLMWrapper(
            model_id="gemini-2.0-flash-exp",
            temperature=0.2,
            max_tokens=600,
            api_key=api_key
        )
        
        print(f"Initialized: {llm.get_model_info()}")
        
        # Test with a simple prompt
        test_prompt = "Show me open issues in the project"
        response = llm.invoke(test_prompt)
        
        print(f"\nTest prompt: {test_prompt}")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error testing GeminiLLMWrapper: {e}")
