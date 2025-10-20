"""
LLM Integration module

This module handles LLM initialization and integration logic.
"""

import logging
from typing import Optional, Any
from models.config import MCPClientConfig

logger = logging.getLogger(__name__)


class LLMIntegration:
    """Handles LLM initialization and integration"""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.llm_instance = None
        self._has_nail_llm = False
    
    async def initialize(self) -> None:
        """Initialize LLM instance"""
        try:
            # Try to import and initialize NailLLMLangchain
            from nail_client.flow import NailRAGFlow
            from nail_client.nail_llm import NailLLMLangchain
            
            logger.info("Initializing NailLLMLangchain...")
            rag_flow = NailRAGFlow()
            
            self.llm_instance = NailLLMLangchain(
                model_id=self.config.nail_model_id,
                temperature=self.config.nail_temperature,
                max_tokens=self.config.nail_max_tokens,
                api_key=rag_flow.access_token
            )
            
            self._has_nail_llm = True
            logger.info(f"✅ NailLLMLangchain initialized successfully with model: {self.config.nail_model_id}")
            
        except ImportError:
            logger.warning("NailLLMLangchain not available, falling back to GeminiLLMWrapper")
            try:
                from gemini_llm_wrapper import GeminiLLMWrapper
                
                self.llm_instance = GeminiLLMWrapper(
                    api_key=self.config.google_api_key,
                    model_id=self.config.gemini_model_id,
                    temperature=0.2,
                    max_tokens=600
                )
                self._has_nail_llm = False
                logger.info(f"✅ GeminiLLMWrapper initialized successfully with model: {self.config.gemini_model_id}")
                
            except Exception as e:
                logger.error(f"Failed to initialize GeminiLLMWrapper: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to initialize NailLLMLangchain: {e}")
            raise
    
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt"""
        if self.llm_instance is None:
            raise RuntimeError("LLM is not initialized")
        return self.llm_instance.invoke(prompt)
    
    @property
    def is_initialized(self) -> bool:
        """Check if LLM is initialized"""
        return self.llm_instance is not None
    
    @property
    def has_nail_llm(self) -> bool:
        """Check if using NailLLMLangchain"""
        return self._has_nail_llm
