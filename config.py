import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the Product Description Generator"""
    
    # Ollama Configuration
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
    # OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'ALIENTELLIGENCE/electricalengineerv2')
    
    # LLM Parameters for consistency
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.0'))  # 0.0 = completely deterministic
    TOP_P = float(os.getenv('TOP_P', '0.9'))  # Focused sampling
    REPEAT_PENALTY = float(os.getenv('REPEAT_PENALTY', '1.1'))  # Reduce repetition
    SEED = int(os.getenv('SEED', '42'))  # Fixed seed for deterministic results
    
    # Processing Configuration
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '600'))
    
    # Output Configuration
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def ensure_output_dir(cls):
        """Ensure output directory exists with proper permissions (Mac-compatible)"""
        try:
            output_dir = cls.OUTPUT_DIR
            
            # Remove existing directory if it has permission issues
            if os.path.exists(output_dir):
                try:
                    # Test write permissions
                    test_file = os.path.join(output_dir, f"test_write_{os.getpid()}.tmp")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    return True
                except (PermissionError, OSError):
                    import shutil
                    shutil.rmtree(output_dir, ignore_errors=True)
            
            # Create directory with proper permissions
            os.makedirs(output_dir, mode=0o755, exist_ok=True)
            
            # Set proper permissions (Mac-specific)
            try:
                import stat
                os.chmod(output_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            except Exception:
                pass
            
            # Test write permissions
            test_file = os.path.join(output_dir, f"test_write_{os.getpid()}.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
                
        except Exception as e:
            print(f"❌ Failed to create output directory: {str(e)}")
            return False

    # Key Specs Data Configuration
    SPECS_CSV_PATH = os.getenv('SPECS_CSV_PATH', 'specifications.csv')

    # Prompt Configuration
    PROMPT_TEMPLATE = """
# Role
You're an expert website content manager. You create the best products and descriptions for the electrical ecommerce site essentialparts.com. Your titles and descriptions should be perfect for SEO and also you are targeting electrical contractors and resellers as well as end users. You are a professional product content writer for a technical B2B website. Your task is to generate consistent, SEO-optimized, and uniquely detailed content for industrial components and equipment based only on part number and manufacturer.

# Inputs
Part Number: {part_number}
Manufacturer: {manufacturer}

# Dynamic Product Specifications (if available):
{reliable_specs}

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

    # When reliable specs are available from HPS, include them explicitly
    PROMPT_TEMPLATE_WITH_SPECS = PROMPT_TEMPLATE