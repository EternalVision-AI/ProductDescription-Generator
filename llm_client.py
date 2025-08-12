import json
import time
import logging
from typing import Dict, Optional, Tuple
import requests
import ollama
from retry import retry
from config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with Ollama LLM"""
    
    def __init__(self, config: Config):
        self.config = config
        self._setup_client()
    
    def _setup_client(self):
        """Setup the Ollama client"""
        try:
            # The ollama library uses environment variables or direct API calls
            # We'll use the host from config for API calls
            logger.info(f"Ollama client configured with host: {self.config.OLLAMA_MODEL}")
        except Exception as e:
            logger.error(f"Error setting up Ollama client: {str(e)}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def generate_content(self, part_number: str, manufacturer: str, reliable_specs: Optional[Dict[str, str]] = None) -> Tuple[str, str]:
        """
        Generate title and description for a product
        
        Args:
            part_number: Product part number
            manufacturer: Product manufacturer
            reliable_specs: Optional dict of authoritative specs to include
            
        Returns:
            Tuple of (title, description)
        """
        try:
            # Prepare the prompt
            if reliable_specs:
                # Render specs as simple key: value lines to avoid hallucination
                specs_text = "\n".join([f"- {k} {v}" for k, v in reliable_specs.items()])
                prompt = self.config.PROMPT_TEMPLATE_WITH_SPECS.format(
                    part_number=part_number,
                    manufacturer=manufacturer,
                    reliable_specs=specs_text
                )
            else:
                prompt = self.config.PROMPT_TEMPLATE.format(
                    part_number=part_number,
                    manufacturer=manufacturer,
                    reliable_specs=""
                )
            
            # Make API call using ollama library
            try:
                response = ollama.chat(
                    model=self.config.OLLAMA_MODEL,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    options={
                        "temperature": self.config.TEMPERATURE,
                        "num_predict": 2500,
                        "top_p": self.config.TOP_P,
                        "repeat_penalty": self.config.REPEAT_PENALTY,
                        "seed": self.config.SEED
                    }
                )
            except Exception as chat_error:
                logger.error(f"Ollama chat failed for {part_number}: {str(chat_error)}")
                # Return fallback content for chat failures
                fallback_title = f"{part_number} - {manufacturer} Product"
                fallback_desc = f"Technical specifications and product details for {part_number} manufactured by {manufacturer}. Product information and specifications available upon request."
                return fallback_title, fallback_desc
            
            # Parse response
            try:
                content = response['message']['content']
                logger.debug(f"Raw response type: {type(content)}, length: {len(str(content)) if content else 0}")
                
                if content is None:
                    raise ValueError("Empty response from LLM")
                
                # Handle different content types and encoding
                if isinstance(content, bytes):
                    logger.debug(f"Content is bytes, attempting decode")
                    content = content.decode('utf-8', errors='replace')
                elif not isinstance(content, str):
                    logger.debug(f"Content is {type(content)}, converting to string")
                    content = str(content)
                
                # Clean the content thoroughly
                content = content.strip()
                logger.debug(f"Cleaned content length: {len(content)}")
                # Remove any problematic characters that might cause issues
                content = ''.join(char for char in content if ord(char) < 0x10000)
                logger.debug(f"Final content length: {len(content)}")
                
            except Exception as content_error:
                logger.error(f"Content processing failed for {part_number}: {str(content_error)}")
                # Return fallback content
                fallback_title = f"{part_number} - {manufacturer} Product"
                fallback_desc = f"Technical specifications and product details for {part_number} manufactured by {manufacturer}. Product information and specifications available upon request."
                return fallback_title, fallback_desc

            # Handle potential encoding issues
            
            title, description = self._parse_response(content)
            
            logger.info(f"Generated content for {part_number} - {manufacturer}")
            return title, description
            
        except Exception as e:
            logger.error(f"Error generating content for {part_number}: {str(e)}")
            # Return fallback content instead of crashing
            fallback_title = f"{part_number} - {manufacturer} Product"
            fallback_desc = f"Technical specifications and product details for {part_number} manufactured by {manufacturer}. Product information and specifications available upon request."
            logger.warning(f"Using fallback content for {part_number} due to error")
            return fallback_title, fallback_desc
    
    def _parse_response(self, content: str) -> Tuple[str, str]:
        """
        Parse the LLM response to extract title and description
        
        Args:
            content: Raw response from LLM
            
        Returns:
            Tuple of (title, description)
        """
        try:
            # Ensure content is a clean string
            if not isinstance(content, str):
                content = str(content)
            # Clean up any problematic characters
            content = content.encode('utf-8', errors='replace').decode('utf-8')

            lines = content.split('\n')
            title = ""
            description = ""
            in_description = False
            
            for line in lines:
                try:
                    line = line.strip()
                except (UnicodeDecodeError, AttributeError):
                    continue
                
                # Skip empty lines and introductory text
                if not line or line.startswith('Based on the inputs'):
                    continue
                
                # Handle both markdown and plain text formats for title
                if ('**Title:**' in line or 'Title:' in line) and not title:
                    # Extract title from various formats
                    if '**Title:**' in line:
                        title = line.split('**Title:**')[1].strip()
                    elif 'Title:' in line:
                        title = line.split('Title:')[1].strip()
                
                # Handle both markdown and plain text formats for description
                elif ('**Description:**' in line or 'Description:' in line) and not description:
                    in_description = True
                    # Extract description start from various formats
                    if '**Description:**' in line:
                        desc_part = line.split('**Description:**')[1].strip()
                        if desc_part:
                            description = desc_part
                    elif 'Description:' in line:
                        desc_part = line.split('Description:')[1].strip()
                        if desc_part:
                            description = desc_part
                
                # Continue description if we're in description mode
                elif in_description and line:
                    # Skip markdown formatting, notes, and metadata
                    if (not line.startswith('**') and 
                        not line.startswith('Note:') and 
                        not line.startswith('By ') and
                        not line.startswith('Error:') and
                        not line.startswith('The description has been')):
                        description += " " + line
            
            # Clean up the title (fix encoding issues)
            title = title.replace('‚Äì', '–').replace('â€"', '–')
            
            # Remove any remaining markdown formatting
            title = title.replace('**', '').replace('*', '')
            description = description.replace('**', '').replace('*', '')
            
            # Clean up extra whitespace
            title = title.strip()
            description = description.strip()
            
            if not title or not description:
                raise ValueError("Could not parse title or description from response")
            
            return title, description
            
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            logger.error(f"Raw content: {content}")
            raise
    
    def test_connection(self) -> bool:
        """Test the connection to the Ollama service"""
        try:
            # Test with a simple request
            response = ollama.chat(
                model=self.config.OLLAMA_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                options={
                    "temperature": self.config.TEMPERATURE,
                    "num_predict": 10,
                    "top_p": self.config.TOP_P,
                    "seed": self.config.SEED
                }
            )
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def list_models(self) -> list:
        """List available models"""
        try:
            models = ollama.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    def pull_model(self, model_name: str = None) -> bool:
        """Pull a model if it doesn't exist"""
        try:
            model_to_pull = model_name or self.config.OLLAMA_MODEL
            logger.info(f"Pulling model: {model_to_pull}")
            ollama.pull(model_to_pull)
            logger.info(f"Successfully pulled model: {model_to_pull}")
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_to_pull}: {str(e)}")
            return False 