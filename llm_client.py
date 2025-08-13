import json
import time
import logging
from typing import Dict, Optional, Tuple
import requests
import ollama
from retry import retry
from config import Config
import re

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
    
    def _analyze_csv_structure(self, analysis_prompt: str) -> Optional[Dict]:
        """Use LLM to analyze CSV structure and determine column mapping"""
        try:
            # Use a simpler prompt for structure analysis
            response = ollama.chat(
                model=self.config.OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                options={
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "seed": self.config.SEED
                }
            )
            
            # Extract JSON from response
            content = response['message']['content']
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    pass
            
            # If JSON extraction failed, try to parse manually
            return self._parse_analysis_response(content)
            
        except Exception as e:
            logger.error(f"Error in CSV structure analysis: {str(e)}")
            return None
    
    def _format_specifications(self, specs_prompt: str) -> Optional[str]:
        """Use LLM to format specifications for product descriptions"""
        try:
            response = ollama.chat(
                model=self.config.OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": specs_prompt
                    }
                ],
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "seed": self.config.SEED
                }
            )
            
            content = response['message']['content']
            return content.strip()
            
        except Exception as e:
            logger.error(f"Error formatting specifications: {str(e)}")
            return None
    
    def _parse_analysis_response(self, content: str) -> Optional[Dict]:
        """Parse LLM response to extract column mapping information"""
        try:
            # Simple parsing for common patterns
            result = {}
            
            # Look for part number column
            part_match = re.search(r'part.*number.*column.*["\']([^"\']+)["\']', content, re.IGNORECASE)
            if part_match:
                result['part_number_column'] = part_match.group(1)
            
            # Look for manufacturer column
            mfr_match = re.search(r'manufacturer.*column.*["\']([^"\']+)["\']', content, re.IGNORECASE)
            if mfr_match:
                result['manufacturer_column'] = mfr_match.group(1)
            
            # Look for relevant spec columns
            spec_matches = re.findall(r'["\']([^"\']+)["\']', content)
            if spec_matches:
                result['relevant_spec_columns'] = spec_matches[:10]  # Limit to first 10
            
            return result if result else None
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return None
    
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
            
            # Helper to strip simple markdown emphasis
            def strip_md(s: str) -> str:
                s = s.strip()
                # strip surrounding ** or * and trailing ** or *
                if s.startswith('**') and s.endswith('**') and len(s) > 4:
                    s = s[2:-2].strip()
                if s.startswith('*') and s.endswith('*') and len(s) > 2:
                    s = s[1:-1].strip()
                # common broken encodings
                s = s.replace('‚Äì', '-').replace('â€“', '-').replace('â€”', '—').replace('â€"', '-')
                return s
 
            cleaned_lines = []
            for raw in lines:
                try:
                    line = raw.strip()
                except (UnicodeDecodeError, AttributeError):
                    continue
                if line:
                    cleaned_lines.append(line)
             
            # First pass: explicit markers
            for line in cleaned_lines:
                if ('**Title:**' in line or 'Title:' in line) and not title:
                    if '**Title:**' in line:
                        title = strip_md(line.split('**Title:**', 1)[1])
                    elif 'Title:' in line:
                        title = strip_md(line.split('Title:', 1)[1])
                    continue
                if ('**Description:**' in line or 'Description:' in line):
                    in_description = True
                    part = ''
                    if '**Description:**' in line:
                        part = strip_md(line.split('**Description:**', 1)[1])
                    elif 'Description:' in line:
                        part = strip_md(line.split('Description:', 1)[1])
                    if part:
                        description += ('' if not description else ' ') + part
                    continue
                if in_description:
                    # Skip markdown headings in description
                    if not line.startswith('**') and not line.startswith('#'):
                        description += ('' if not description else ' ') + strip_md(line)
             
            # Fallback: no explicit markers → first non-empty line is title, rest is description
            if not title:
                if cleaned_lines:
                    first = strip_md(cleaned_lines[0])
                    # If the first line looks like a sentence title, use it
                    title = first
                    body_lines = [strip_md(l) for l in cleaned_lines[1:]]
                    description = ' '.join(body_lines).strip()
             
            # Final cleanup
            title = title.replace('**', '').replace('*', '').strip()
            description = description.replace('**', '').replace('*', '').strip()
             
            if not title:
                raise ValueError("Could not parse title or description from response")
            if not description:
                # Build description from remaining content if empty
                remaining = '\n'.join(lines)
                description = remaining.strip() or f"Technical details for {title}."
             
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