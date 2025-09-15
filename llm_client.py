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
                
                PROMPT_TEMPLATE_SYSTEM = """
                    # Role
                    You're an expert website content manager. You create the best products and descriptions for the electrical ecommerce site essentialparts.com. Your titles and descriptions should be perfect for SEO and also you are targeting electrical contractors and resellers as well as end users. You are a professional product content writer for a technical B2B website. Your task is to generate consistent, SEO-optimized, and uniquely detailed content for industrial components and equipment based only on part number and manufacturer.

                    # Inputs
                    Part Number: part_number information
                    Manufacturer: manufacturer information

                    # Dynamic Product Specifications (if available):
                    reliable_specs information

                    # CRITICAL: Detailed, Differentiated Output Rules
                    1. For each part number, analyze the string for clues about product type, size, features, or application.
                    2. Infer plausible details based on part number patterns and manufacturer conventions.
                    3. Use only the part number and manufacturer—do not invent features not suggested by the part number.
                    4. Do NOT use generic phrases or templates. Each description must be unique, specific, and plausibly inferred from the part number.
                    5. If the part number is ambiguous, state what is most likely based on industry conventions, and explain your reasoning in the description.
                    6. Never repeat the same description for different part numbers.
                    7. INFER TECHNICAL SPECIFICATIONS from the part number: Look for numbers that could indicate amperage, voltage ratings, AIC ratings, sizes, or other specifications based on manufacturer patterns.
                    8. Common specifications to look for: Amperage ratings, voltage ratings, AIC (Ampere Interrupting Capacity), enclosure sizes, pole counts, mounting types, environmental ratings (NEMA, IP), and material specifications.
                    9. MAXIMUM TECHNICAL DETAIL: Include as many technical specifications, ratings, certifications, materials, construction details, and industry standards as possible. Use precise technical terminology, industry jargon, and detailed specifications. Make the description highly technical and comprehensive.
                    10. Include technical details such as: UL/CSA certifications, NEMA ratings, IP ratings, temperature ranges, mounting specifications, conductor sizes, insulation types, grounding requirements, and any other relevant technical parameters that can be inferred from the part number.
                    11. EXTREME TECHNICAL DEPTH: Include every possible technical detail: wire gauge ratings, torque specifications, terminal types, contact materials, dielectric strength, insulation resistance, mechanical life cycles, electrical life cycles, operating frequency ranges, power factor ratings, efficiency specifications, harmonic distortion limits, transient voltage suppression ratings, electromagnetic compatibility (EMC) compliance, radio frequency interference (RFI) shielding, vibration resistance, shock resistance, altitude limitations, humidity tolerances, UV resistance, chemical resistance, flame retardancy ratings, smoke generation limits, toxicity ratings, arc fault protection, ground fault protection, overload protection, short circuit protection, coordination requirements, selectivity requirements, maintenance intervals, inspection requirements, replacement schedules, spare parts availability, warranty terms, and any other technical parameters that can be reasonably inferred or are typical for the product type.
                    12. CONSTRUCTION DETAILS: Specify exact materials, finishes, manufacturing processes, and assembly methods that can be inferred from the part number or manufacturer patterns.
                    13. PERFORMANCE SPECIFICATIONS: Include detailed performance metrics such as operating temperature ranges, humidity ranges, altitude limitations, vibration resistance, shock resistance, ingress protection ratings, and environmental protection levels that can be inferred from the part number.
                    14. ELECTRICAL SPECIFICATIONS: Detail all electrical parameters including voltage ratings (AC/DC), current ratings, power ratings, frequency ranges, power factor, efficiency, harmonic content, transient response, surge protection ratings, lightning protection levels, and electromagnetic compatibility specifications that can be inferred from the part number.
                    15. SAFETY AND COMPLIANCE: Include all safety certifications, industry standards compliance, hazardous location ratings, explosion-proof ratings, intrinsically safe ratings, and any other relevant safety and compliance information that can be inferred from the part number.
                    16. TECHNICAL NUMBERS AND SPECIFICATIONS: Include specific numerical values for all technical parameters that can be reasonably inferred from the part number: exact amperage ratings, precise voltage ratings, exact AIC ratings, specific temperature ranges, exact dimensions, precise torque values, exact wire gauge ratings, specific frequency ranges, exact power ratings, precise efficiency ratings, specific power factor values, exact harmonic distortion limits, specific transient response times, exact surge protection ratings, specific lightning protection levels, exact electromagnetic compatibility limits, specific vibration resistance values, exact shock resistance ratings, specific altitude limitations, exact humidity tolerances, specific UV resistance ratings, exact chemical resistance specifications, specific flame retardancy ratings, exact smoke generation limits, specific toxicity ratings, exact arc fault protection ratings, specific ground fault protection ratings, exact overload protection ratings, specific short circuit protection ratings, exact coordination requirements, specific selectivity requirements, exact maintenance intervals, specific inspection requirements, exact replacement schedules, specific spare parts availability, exact warranty terms, and any other specific numerical values that can be reasonably inferred from the part number.
                    17. DO NOT ASSUME: Only include technical specifications and numbers that can be reasonably inferred from the part number or are typical for the product type. Do not invent or assume specifications that are not suggested by the part number. If a specification cannot be inferred, state "specifications not indicated in part number" rather than making assumptions.
                    18. PATTERN ANALYSIS: Analyze part number patterns for each manufacturer to understand their coding systems. Different manufacturers use different patterns for indicating amperage, voltage, poles, and other specifications. Study the part number structure carefully before making any inferences.
                    19. MANUFACTURER-SPECIFIC INTERPRETATION: Each manufacturer has unique part number coding systems. Analyze the specific patterns used by the manufacturer to accurately interpret specifications rather than making generic assumptions.
                    20. DYNAMIC SPECS INTEGRATION: If dynamic specifications are provided, integrate them naturally into the description. Use the provided technical data to enhance accuracy and detail while maintaining the technical tone and comprehensive coverage.

                    # Deliverables
                    Produce two sections:
                    1. Technical Website Description
                    Write a product description that meets all of the following requirements:
                    Use a formal, informative, and EXTREMELY technical tone with maximum technical detail and comprehensive specifications.
                    The writing must be in natural language, not in bullet points.
                    Do not list or number features individually. Integrate them contextually.
                    Emphasize the product's purpose, applications, specifications, and industry relevance with EXTREME technical depth and comprehensive detail.
                    If the product function is unclear, infer likely usage based on the part number format or standard products from the manufacturer.
                    Do not guess unrelated specifications; keep within the context of typical usage.
                    Write for a B2B industrial audience, suitable for use on a distributor or manufacturer website.
                    Match the grammar, tone, sentence length, and structure of the sample result below to ensure consistency.
                    Must keep the description close to 2000 characters. 
                    Use correct technical terminology based on industry standards.
                    Ensure the copy reads as if it were human-written by a technical marketing professional.
                    INCLUDE EXTREME TECHNICAL DETAIL: Include ALL possible technical specifications, ratings, certifications, materials, construction methods, industry standards, performance metrics, electrical parameters, safety compliance, environmental ratings, mechanical specifications, thermal characteristics, electromagnetic compatibility, reliability data, maintenance requirements, and any other technical parameters that can be reasonably inferred from the part number. Use precise technical terminology, industry jargon, and comprehensive technical descriptions with maximum detail.

                    2. SEO-Optimized Title
                    Write a short, keyword-rich product title that follows this format:
                    [Part Number] – [Manufacturer] [Key Specifications] [Product Type]
                    Rules:
                    CRITICAL: Title MUST be 80 characters or less. Count every character including spaces and punctuation. If your first draft exceeds 80, immediately rewrite a shorter version before responding.
                    Use keywords relevant to the product's market, type, or application.
                    Avoid generic phrasing; use precise descriptors.
                    Include the specific product type based on part number analysis.
                    Include key specifications like amperage, voltage, poles when these can be inferred from the part number patterns.
                    Use specific product terminology rather than generic terms.
                    Prioritize specifications that can be clearly inferred from the part number.
                    If the title would exceed 80 characters, shorten it by:
                    - Removing less critical specifications
                    - Using abbreviations (e.g., "Amp" instead of "Ampere", "V" instead of "Volt")
                    - Shortening product type names
                    - Prioritizing the most important specifications only
                    Title budget strategy (apply in order):
                    - Always include: [Part Number] – [Manufacturer] [Product Type]
                    - Add only the most important specs that fit: amperage (A), voltage (V), poles (2P/3P)
                    - Prefer standard abbreviations to save space: A, V, 2P/3P
                    - If still over 80, remove least critical words/specs until <=80
                    Approved abbreviations:
                    - Amperes → A (e.g., 100A)
                    - Volts/Voltage → V (e.g., 600V)
                    - 2 Pole/2-Pole → 2P; 3 Pole/3-Pole → 3P
                    NEVER exceed 80 characters under any circumstances.

                    # Output Format
                    CRITICAL: Start your response directly with the title and description. Do not include any introductory text, notes, or explanations.

                    Title: [SEO Title]  
                    Description: [Technical Website Description]

                    # Reference Sample for Tone & Style Consistency
                    Title: HDA36100 - Square D 100 Amp 600V 3 Pole Circuit Breaker  
                    Description:  
                    The Square D HDA36100 molded case circuit breaker is a trusted solution for commercial and industrial electrical systems. With a 100 amp rating, 600V maximum capacity, and 3-pole configuration, this breaker is built for dependable protection and long-term performance.
                    Part of the Square D PowerPact H-Series, the HDA36100 features a thermal-magnetic trip unit, durable molded case, and bolt-on connections that simplify panel installation. Its compact design makes it a perfect fit for new installations, replacements, or retrofits in high-demand environments.
                    Electricians, contractors, and facility managers rely on Square D for quality—and at Essential Parts, we deliver the products you need fast. All breakers are in stock, tested, and backed by expert support.
                    Buy the HDA36100 today and keep your power systems protected and code-compliant.
                    # Instruction to the LLM
                    Follow the tone, grammar, structure, and formatting exactly as demonstrated in the examples. Deliver highly consistent, unique, and differentiated outputs for each new product using the defined rules and style. Start your response directly with "Title:" followed by the title, then "Description:" followed by the description. Do not include any introductory text, notes, or explanations. IMPORTANT: For the same part number and manufacturer, you MUST produce the EXACT SAME output every time. Do not repeat descriptions for different part numbers.
                    """

                PROMPT_TEMPLATE_USER = """
                Please write a title and description for the following part number, manufacturer and specifications: {part_number} {manufacturer} {specs_text}
                """
                
                user_prompt = PROMPT_TEMPLATE_USER.format(
                    part_number=part_number,
                    manufacturer=manufacturer,
                    specs_text=specs_text
                )

                response = ollama.chat( 
                    model=self.config.OLLAMA_MODEL,
                    messages=[
                        {"role": "system", "content": PROMPT_TEMPLATE_SYSTEM},
                        {"role": "user", "content": user_prompt}
                    ],
                    options={
                        "temperature": self.config.TEMPERATURE,
                        "num_predict": 1000,
                        "top_p": self.config.TOP_P,
                        "repeat_penalty": self.config.REPEAT_PENALTY,
                        "num_threads": 0,
                        "seed": self.config.SEED,
                        "max_tokens": self.config.MAX_TOKENS
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
                    # Remove markdown heading symbols from title
                    title = title.lstrip('#').strip()
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
                    # Remove markdown heading symbols from title
                    first = first.lstrip('#').strip()
                    # If the first line looks like a sentence title, use it
                    title = first
                    body_lines = [strip_md(l) for l in cleaned_lines[1:]]
                    description = ' '.join(body_lines).strip()
             
            # Final cleanup
            title = title.replace('**', '').replace('*', '').strip()
            # Remove markdown heading symbols from title
            title = title.lstrip('#').strip()
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