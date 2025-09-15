# Product Description Generator

An automated Python application for generating SEO-friendly titles and technical descriptions for industrial products using local LLM (Ollama) with a modern GUI built with customtkinter. Features dynamic specification integration, streaming CSV processing, and intelligent title length enforcement.

## Features

- 🚀 **Local Processing**: Uses Ollama with gemma2:2b model for cost-effective processing
- 🎨 **Modern GUI**: Beautiful interface built with customtkinter with real-time progress tracking
- 📊 **Batch Processing**: Handles large CSV files with memory-efficient streaming output
- 🔄 **Dynamic Specs Integration**: Automatically detects and uses product specifications from CSV files
- 🧠 **LLM-Powered Column Detection**: Uses AI to dynamically identify part numbers, manufacturers, and relevant specifications
- 📏 **Title Length Enforcement**: Ensures all generated titles are ≤80 characters with smart abbreviations
- 🔍 **Robust Error Handling**: Comprehensive retry mechanism and graceful fallbacks
- 📈 **Real-Time Progress**: Live progress tracking with detailed logging in the GUI
- 🎯 **Consistent Output**: Maintains consistent tone and style across all descriptions
- 💾 **Streaming CSV Export**: Writes results row-by-row to avoid memory limitations
- 🔧 **Generic Design**: Works with any specifications CSV file, not limited to specific manufacturers

## Requirements

- Python 3.8+
- Ollama (for local processing)
- 8GB+ RAM (for gemma2:2b model)
- macOS, Windows, or Linux

## Installation

### Quick Setup (macOS)

For macOS users, we provide an automated setup script that installs everything you need:

```bash
# Make the setup script executable
chmod +x setup_mac.sh

# Run the automated setup
./setup_mac.sh
```

This will automatically install:
- Python 3.11
- All required dependencies
- Ollama AI service
- gemma2:2b model
- Create launcher scripts and desktop shortcuts

For detailed macOS setup instructions, see [SETUP_MAC.md](SETUP_MAC.md).

### Manual Installation

#### 1. Clone or Download the Project

```bash
# If you have git installed
git clone <repository-url>
cd auto-generator

# Or download and extract the ZIP file
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Ollama

Visit [https://ollama.ai/](https://ollama.ai/) and download the appropriate version for your operating system.

#### 4. Setup Ollama and Models

```bash
python main.py setup
```

This will:
- Check if Ollama is installed
- Download the gemma2:2b model
- Verify the setup

## Usage

### GUI Version (Recommended)

Launch the modern GUI application:

```bash
python gui.py
```

Or use the batch file on Windows:
```bash
run_gui.bat
```

The GUI provides:
- **Single Product Testing**: Test with individual part numbers and manufacturers
- **Batch CSV Processing**: Process entire product catalogs with progress tracking
- **Specifications Integration**: Optional integration with specifications CSV for enhanced descriptions
- **Real-Time Logging**: See detailed processing information as it happens
- **Progress Bar**: Visual progress indicator for batch operations

### Command Line Version

Test the system with a single product:

```bash
python main.py test "XJG104HDG" "Eaton Crouse-Hinds"
```

Process your entire product catalog:

```bash
python main.py process OPENAI.csv
```

Or specify an output file:

```bash
python main.py process OPENAI.csv --output results.csv
```

### CSV Format

Your input CSV file should have these columns:
- `Part Number`: The product part number (or similar column name)
- `Manufacturer`: The product manufacturer (or similar column name)

The system will automatically detect column names using AI, so variations like "Item", "SKU", "Brand", "Make", etc. are supported.

Example:
```csv
Part Number,Manufacturer
XJG104HDG,Eaton Crouse-Hinds
VHU364NSSGL,Square D
```

### Specifications CSV (Optional)

For enhanced descriptions, you can provide a specifications CSV file. The system will:
- Automatically detect the part number column and relevant specification columns
- Look up specifications for each product during processing
- Merge specifications with input data for comprehensive descriptions

Example specifications CSV:
```csv
Part Number,Voltage,Amperage,Poles,Type,Standards
XJG104HDG,600V,100A,3,Molded Case Circuit Breaker,UL/CSA
VHU364NSSGL,480V,30A,2,GFCI Breaker,UL Listed
```

## Configuration

### Environment Variables

Create a `.env` file to customize settings:

```env
# Ollama Configuration
OLLAMA_MODEL=gemma2:2b

# Processing Configuration
BATCH_SIZE=10
MAX_RETRIES=3
RETRY_DELAY=2
REQUEST_TIMEOUT=600

# Output Configuration
OUTPUT_DIR=output
LOG_LEVEL=INFO

# Specifications Configuration
SPECS_CSV_PATH=specifications.csv
```

## Output

The application generates:

1. **SEO-Optimized Title**: Format: `[Part Number] – [Manufacturer] [Key Specifications] [Product Type]`
   - **Strict 80-character limit** with intelligent abbreviations
   - Uses standard abbreviations: A (Amperes), V (Volts), 2P/3P (Poles)
   - Prioritizes most important specifications

2. **Technical Description**: Professional, technical description suitable for B2B websites
   - Integrates specifications from both input CSV and specifications CSV
   - Uses all available data for comprehensive descriptions
   - Maintains consistent technical tone and depth

Example output:
```
Title: XJG104HDG – Eaton Crouse-Hinds 100A 600V 3P Circuit Breaker
Description: The Eaton Crouse-Hinds XJG104HDG molded case circuit breaker is engineered for commercial and industrial electrical systems requiring reliable overcurrent protection...
```

## Key Features Explained

### Dynamic Column Detection
The system uses AI to automatically identify:
- Part number columns (Part Number, Item, SKU, etc.)
- Manufacturer columns (Manufacturer, Brand, Make, etc.)
- Relevant specification columns (Voltage, Amperage, Poles, etc.)

### Streaming CSV Processing
- Processes and writes results row-by-row to avoid memory limitations
- Suitable for large CSV files with thousands of products
- Provides real-time progress updates

### Title Length Enforcement
- **Hard 80-character limit** with post-processing
- Smart abbreviations: Amperes→A, Volts→V, 2-Pole→2P
- Prioritizes essential information when space is limited

### Specifications Integration
- Automatically merges specifications from dedicated CSV files
- Uses all available data from input rows
- Provides fallback content when specifications are unavailable

## Performance

- **Processing Speed**: ~10-20 products per minute (depending on hardware)
- **Memory Usage**: ~32GB RAM for gemma2:2b model
- **Batch Size**: Configurable (default: 10 products per batch)
- **Memory Efficiency**: Streaming processing handles unlimited file sizes

## Troubleshooting

### Ollama Not Running

```bash
# Start Ollama
ollama serve

# In another terminal, check if it's running
ollama list
```

### Model Not Found

```bash
# Pull the required model
ollama pull gemma2:2b
```

### Memory Issues

If you encounter memory issues:

1. Reduce batch size in `.env`:
```env
BATCH_SIZE=5
```

2. Use a smaller model:
```env
OLLAMA_MODEL=llama3.1:3b
```

### Connection Errors

1. Check if Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

2. Restart Ollama:
```bash
# Stop Ollama
pkill ollama

# Start Ollama
ollama serve
```

### CSV Encoding Issues

If you encounter encoding errors:
- The system automatically tries UTF-8, Latin-1, and UTF-8 with error replacement
- Ensure your CSV files are saved with proper encoding
- Check the log file for specific encoding error details

### Title Length Issues

If titles are still too long:
- The system enforces a hard 80-character limit
- Check the log for specific products that may need manual review
- The system will truncate titles if necessary while preserving essential information

## File Structure

```
auto-generator/
├── main.py                 # Main application entry point
├── gui.py                  # GUI application using customtkinter
├── config.py              # Configuration settings and prompt templates
├── llm_client.py          # Ollama LLM client with robust parsing
├── processor.py           # Main processing logic with streaming support
├── specs_lookup.py        # Dynamic specifications lookup and column detection
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── Prompt.md             # Prompt template documentation
├── OPENAI.csv            # Sample input file
├── specifications.csv     # Sample specifications file
├── run_gui.bat           # Windows GUI launcher
├── run_cli.bat           # Windows CLI launcher
├── install.bat           # Windows installation script
├── setup_mac.sh          # macOS automated setup script
├── test_setup.sh         # macOS setup verification script
├── verify_installation.sh # Installation verification script
├── run_gui.sh            # macOS GUI launcher (created by setup)
├── Product Description Generator.app/ # macOS desktop shortcut (created by setup)
├── SETUP_MAC.md          # macOS setup documentation
├── .env.example          # Environment variables example
├── output/               # Generated output files
└── product_generator.log # Application logs
```

## Logging

The application provides comprehensive logging:
- **File Logging**: All activities logged to `product_generator.log`
- **GUI Logging**: Real-time logs displayed in the GUI interface
- **Progress Tracking**: Live progress updates for batch operations
- **Error Details**: Detailed error information for troubleshooting

## Recent Improvements

- **Dynamic Column Detection**: AI-powered identification of CSV structure
- **Streaming CSV Processing**: Memory-efficient processing for large files
- **Title Length Enforcement**: Strict 80-character limit with smart abbreviations
- **Enhanced Error Handling**: Robust parsing and fallback mechanisms
- **Real-Time UI Updates**: Live progress and detailed logging in GUI
- **Generic Specifications Support**: Works with any specifications CSV file
- **Comprehensive Data Integration**: Uses all available data for descriptions

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the log file: `product_generator.log`
3. Test with a single product first: `python main.py test "PART_NUMBER" "MANUFACTURER"`
4. Check the GUI logs for detailed processing information

## License

This project is provided as-is for the specific use case described in the conversation.