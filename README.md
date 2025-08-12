# Product Description Generator

An automated Python application for generating SEO-friendly titles and technical descriptions for industrial products using local LLM (Ollama) with a modern GUI built with customtkinter.

## Features

- 🚀 **Local Processing**: Uses Ollama with Llama3.1:8b model for cost-effective processing
- 🎨 **Modern GUI**: Beautiful interface built with customtkinter
- 📊 **Batch Processing**: Handles large CSV files with progress tracking
- 🔄 **Error Handling**: Robust retry mechanism and error recovery
- 📈 **Progress Tracking**: Real-time progress with colored output
- 🎯 **Consistent Output**: Maintains consistent tone and style across all descriptions
- 💾 **CSV Export**: Outputs results in CSV format for easy integration

## Requirements

- Python 3.8+
- Ollama (for local processing)
- 8GB+ RAM (for Llama3.1:8b model)
- macOS, Windows, or Linux

## Installation

### 1. Clone or Download the Project

```bash
# If you have git installed
git clone <repository-url>
cd auto-generator

# Or download and extract the ZIP file
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama

Visit [https://ollama.ai/](https://ollama.ai/) and download the appropriate version for your operating system.

### 4. Setup Ollama and Models

```bash
python main.py setup
```

This will:
- Check if Ollama is installed
- Download the Llama3.1:8b model
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
- `Part Number`: The product part number
- `Manufacturer`: The product manufacturer

Example:
```csv
Part Number,Manufacturer
XJG104HDG,Eaton Crouse-Hinds
VHU364NSSGL,Square D
```

## Configuration

### Environment Variables

Create a `.env` file to customize settings:

```env
# Ollama Configuration
OLLAMA_MODEL=llama3.1:8b

# Processing Configuration
BATCH_SIZE=10
MAX_RETRIES=3
RETRY_DELAY=2
REQUEST_TIMEOUT=60

# Output Configuration
OUTPUT_DIR=output
LOG_LEVEL=INFO
```

## Output

The application generates:

1. **SEO-Optimized Title**: Format: `[Part Number] – [Manufacturer] [Descriptive Product Type]`
2. **Technical Description**: Professional, technical description suitable for B2B websites

Example output:
```
Title: XJG104HDG – Eaton Crouse‑Hinds Expansion Coupling
Description: The Eaton Crouse‑Hinds XJG104HDG is a heavy‑duty expansion coupling engineered to accommodate longitudinal movement in rigid metal or intermediate metal conduit systems...
```

## Performance

- **Processing Speed**: ~10-20 products per minute (depending on hardware)
- **Memory Usage**: ~4-8GB RAM for Llama3.1:8b model
- **Batch Size**: Configurable (default: 10 products per batch)

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
ollama pull llama3.1:8b
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

## File Structure

```
auto-generator/
├── main.py                 # Main application entry point
├── gui.py                  # GUI application using customtkinter
├── config.py              # Configuration settings
├── llm_client.py          # Ollama LLM client
├── processor.py           # Main processing logic
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── Prompt.md             # Prompt template
├── OPENAI.csv            # Sample input file
├── run_gui.bat           # Windows GUI launcher
├── run_cli.bat           # Windows CLI launcher
├── install.bat           # Windows installation script
├── .env.example          # Environment variables example
├── output/               # Generated output files
└── product_generator.log # Application logs
```

## Logging

The application logs all activities to `product_generator.log`. Check this file for detailed error information if issues occur.

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the log file: `product_generator.log`
3. Test with a single product first: `python main.py test "PART_NUMBER" "MANUFACTURER"`

## License

This project is provided as-is for the specific use case described in the conversation.