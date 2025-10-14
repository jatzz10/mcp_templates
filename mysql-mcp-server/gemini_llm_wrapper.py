#!/usr/bin/env python3
"""
Gemini LLM Wrapper for MCP Client

A wrapper class that mimics the NailLLMLangchain interface but uses Google's Gemini 2.5 Flash model.
This allows seamless integration with existing MCP client code while using a free Gemini model.

Usage:
    from gemini_llm_wrapper import GeminiLLMWrapper
    
    llm = GeminiLLMWrapper(
        model_id="gemini-2.0-flash-exp",
        temperature=0.2,
        max_tokens=600,
        api_key="your-google-api-key"
    )
    
    response = llm.invoke("Your prompt here")
"""

import os
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiLLMWrapper:
    """
    Gemini LLM Wrapper that mimics NailLLMLangchain interface.
    
    This class provides the same interface as NailLLMLangchain but uses Google's
    Gemini models instead. It's designed to be a drop-in replacement.
    """
    
    def __init__(
        self,
        model_id: str = "gemini-2.0-flash-exp",
        temperature: float = 0.2,
        max_tokens: int = 600,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gemini LLM Wrapper.
        
        Args:
            model_id: Gemini model ID (default: gemini-2.0-flash-exp)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            api_key: Google API key (if not provided, will use GOOGLE_API_KEY env var)
            **kwargs: Additional arguments (ignored for compatibility)
        """
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_id,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=0.8,
                    top_k=40,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            logger.info(f"Initialized Gemini model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke the Gemini model with a prompt.
        
        This method mimics the NailLLMLangchain.invoke() interface.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments (ignored for compatibility)
            
        Returns:
            Generated response as string
        """
        try:
            logger.debug(f"Invoking Gemini with prompt: {prompt[:100]}...")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.debug(f"Gemini response: {response.text[:100]}...")
                return response.text
            else:
                logger.warning("Gemini returned empty response")
                return ""
                
        except Exception as e:
            logger.error(f"Error invoking Gemini model: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Alternative method name for compatibility.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments
            
        Returns:
            Generated response as string
        """
        return self.invoke(prompt, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat interface for multi-turn conversations.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional arguments
            
        Returns:
            Generated response as string
        """
        try:
            # Convert messages to Gemini format
            chat = self.model.start_chat(history=[])
            
            # Process messages
            for message in messages:
                role = message.get('role', 'user')
                content = message.get('content', '')
                
                if role == 'user':
                    response = chat.send_message(content)
                elif role == 'assistant':
                    # Add assistant message to history
                    chat.history.append({
                        'role': 'user',
                        'parts': [content]
                    })
                    chat.history.append({
                        'role': 'model',
                        'parts': [content]
                    })
            
            # Get the last response
            if chat.history:
                last_response = chat.history[-1]
                if 'parts' in last_response:
                    return last_response['parts'][0]
            
            return ""
            
        except Exception as e:
            logger.error(f"Error in chat interface: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "provider": "google",
            "model_type": "gemini"
        }
    
    def update_config(self, **kwargs) -> None:
        """
        Update model configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        if 'temperature' in kwargs:
            self.temperature = kwargs['temperature']
        if 'max_tokens' in kwargs:
            self.max_tokens = kwargs['max_tokens']
        if 'model_id' in kwargs:
            self.model_id = kwargs['model_id']
            # Reinitialize model with new ID
            self.model = genai.GenerativeModel(
                model_name=self.model_id,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=0.8,
                    top_k=40,
                )
            )
        
        logger.info(f"Updated Gemini configuration: {self.get_model_info()}")


# Convenience function for easy initialization
def create_gemini_llm(
    model_id: str = "gemini-2.0-flash-exp",
    temperature: float = 0.2,
    max_tokens: int = 600,
    api_key: Optional[str] = None
) -> GeminiLLMWrapper:
    """
    Convenience function to create a Gemini LLM instance.
    
    Args:
        model_id: Gemini model ID
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        api_key: Google API key
        
    Returns:
        GeminiLLMWrapper instance
    """
    return GeminiLLMWrapper(
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key
    )


# Example usage
if __name__ == "__main__":
    # Example usage
    try:
        # Initialize with environment variable
        llm = GeminiLLMWrapper()
        
        # Test basic invocation
        response = llm.invoke("Hello, how are you?")
        print(f"Response: {response}")
        
        # Test model info
        print(f"Model info: {llm.get_model_info()}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set GOOGLE_API_KEY environment variable")
