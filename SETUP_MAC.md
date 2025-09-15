# Product Description Generator - Mac Auto Setup

This guide will help you automatically set up the Product Description Generator on macOS with all required dependencies.

## Quick Start

1. **Download the setup script:**
   ```bash
   # Make sure you're in the project directory
   chmod +x setup_mac.sh
   ```

2. **Run the auto setup:**
   ```bash
   ./setup_mac.sh
   ```

3. **Follow the prompts** - the script will automatically install everything you need!

## What Gets Installed

The setup script automatically installs:

- **Python 3.11** - The programming language runtime
- **Homebrew** - Package manager for macOS (if not already installed)
- **Python Dependencies** - All required packages from `requirements.txt`:
  - `pandas` - Data manipulation
  - `requests` - HTTP requests
  - `ollama` - AI model client
  - `customtkinter` - Modern GUI framework
  - `python-dotenv` - Environment variables
  - `tqdm` - Progress bars
  - `retry` - Retry logic
  - `colorama` - Colored terminal output
  - `Pillow` - Image processing
- **Ollama** - AI service for running local language models
- **gemma2:2b Model** - The AI model used for generating descriptions

## System Requirements

- **macOS 12 or higher** (recommended: macOS 12+)
- **Internet connection** (for downloading dependencies and AI model)
- **At least 16GB RAM** (recommended: 16GB+ for optimal AI performance)
- **At least 20GB free disk space** (for Python, dependencies, and AI model)

## Installation Process

The setup script performs these steps automatically:

1. **System Check** - Verifies macOS version and system requirements
2. **Homebrew Installation** - Installs or updates the Homebrew package manager
3. **Python Installation** - Installs Python 3.11 via Homebrew
4. **Dependencies Installation** - Installs all required Python packages
5. **Ollama Installation** - Downloads and installs Ollama from the official source
6. **AI Model Setup** - Downloads the gemma2:2b model (~4.7GB)
7. **Launcher Creation** - Creates convenient launcher scripts
8. **Desktop Shortcut** - Creates a desktop application shortcut
9. **Verification** - Tests that everything is working correctly

## After Installation

Once the setup is complete, you can run the application in several ways:

### Option 1: Command Line
```bash
./run_gui.sh
```

### Option 2: Direct Python
```bash
python3 gui.py
```

## File Requirements

**Important Note:**

Both an input file and a specification file are required.
Each file must contain two columns labeled "Part Number" and "Manufacturer", which will be used to map values between the files.

- **The input file** should include only the two columns: Part Number and Manufacturer.
- **The specification reference file** should include all specification columns, such as Part Number, Manufacturer, Phase, Voltage, Amperage, AIC Rating, Connection, etc.

## First-Time Setup

When you first run the application:

1. **Launch the GUI** using one of the methods above
2. **Click "Setup Ollama"** to verify the AI model is working
3. **Test with a single product** using the test section in the GUI
4. **Load your CSV file** and start generating descriptions!

## Troubleshooting

### Common Issues

#### "Command not found: python3"
- The setup script should have installed Python, but you may need to restart your terminal
- Try running: `source ~/.zprofile` or `source ~/.bash_profile`

#### "Ollama is not running"
- Start Ollama manually: `ollama serve`
- Or launch it from Applications: `open /Applications/Ollama.app`

#### "Model not found"
- Download the model manually: `ollama pull gemma2:2b`
- Check available models: `ollama list`

#### "Permission denied" errors
- Make sure the script is executable: `chmod +x setup_mac.sh`
- You may need to allow the script to run in System Preferences > Security & Privacy

#### "App can't be opened because it is from an unidentified developer"
- Right-click the app → "Open" → "Open" in the dialog
- Or go to System Preferences > Security & Privacy > General and allow the app

### Manual Installation Steps

If the auto setup fails, you can install components manually:

#### Install Python via Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11
```

#### Install Python Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

#### Install Ollama
1. Download from: https://ollama.ai/download
2. Install the downloaded DMG file
3. Add to PATH: `export PATH="/Applications/Ollama.app/Contents/Resources:$PATH"`

#### Download AI Model
```bash
ollama serve  # Start Ollama service
ollama pull gemma2:2b  # Download the model
```

## File Structure

After installation, your project directory will contain:

```
auto-generator/
├── setup_mac.sh                    # Auto setup script
├── run_gui.sh                      # Launcher script (created by setup)
├── Product Description Generator.app/  # Desktop shortcut (created by setup)
├── gui.py                          # Main GUI application
├── main.py                         # CLI version
├── config.py                       # Configuration
├── processor.py                    # Processing logic
├── llm_client.py                   # AI client
├── specs_lookup.py                 # Specifications lookup
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## Performance Tips

### For Better AI Performance
- **Close other applications** when running the AI model
- **Use SSD storage** for faster model loading
- **Ensure adequate RAM** (16GB+ recommended)
- **Keep Ollama running** in the background

### For Large CSV Files
- **Process in batches** using the batch size setting
- **Monitor system resources** during processing
- **Save progress frequently** to avoid data loss

## Security Notes

- The setup script downloads software from official sources only
- Ollama runs locally on your machine (no data sent to external servers)
- All AI processing happens on your local machine
- No personal data is transmitted to external services

## Support

If you encounter issues:

1. **Check the console output** for error messages
2. **Verify all components** are installed correctly
3. **Restart your terminal** and try again
4. **Check system requirements** are met
5. **Review the troubleshooting section** above

For additional help, refer to the main README.md file or check the project documentation.

## Uninstallation

To remove the Product Description Generator:

1. **Delete the project folder**
2. **Remove Python packages** (optional):
   ```bash
   pip3 uninstall -r requirements.txt
   ```
3. **Remove Ollama** (optional):
   - Delete `/Applications/Ollama.app`
   - Remove from PATH in `~/.zprofile` and `~/.bash_profile`
4. **Remove Homebrew** (optional):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)"
   ```

---

**Enjoy using your Product Description Generator! 🎉**
