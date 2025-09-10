#!/usr/bin/env python3
"""
GUI version of the Product Description Generator
Provides a graphical interface for the application using customtkinter
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import queue
import os
from pathlib import Path

from config import Config
from processor import ProductDescriptionProcessor

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ProductGeneratorGUI:
    """GUI for the Product Description Generator using customtkinter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Product Description Generator")
        self.root.geometry("1100x900")
        
        # Configuration
        self.config = Config()
        self.processor = None
        self.processing_queue = queue.Queue()
        
        # Setup UI
        self.setup_ui()
        
        # Start queue processing
        self.process_queue()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Product Description Generator", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Two-column container
        columns_frame = ctk.CTkFrame(main_frame)
        columns_frame.pack(fill="both", expand=True)
        columns_frame.grid_columnconfigure(0, weight=1)
        columns_frame.grid_columnconfigure(1, weight=1)
        columns_frame.grid_rowconfigure(0, weight=1)

        # Left and Right columns
        left_col = ctk.CTkFrame(columns_frame)
        right_col = ctk.CTkFrame(columns_frame)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_col.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # File selection frame
        file_frame = ctk.CTkFrame(left_col)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(file_frame, text="Input CSV File:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))
        
        file_input_frame = ctk.CTkFrame(file_frame)
        file_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.file_var = ctk.StringVar()
        file_entry = ctk.CTkEntry(file_input_frame, textvariable=self.file_var, height=35)
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            file_input_frame, 
            text="Browse", 
            command=self.browse_file,
            width=80,
            height=35
        ).pack(side="right")
        
        # Output file selection
        ctk.CTkLabel(file_frame, text="Output File (optional):", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))
        
        output_input_frame = ctk.CTkFrame(file_frame)
        output_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.output_var = ctk.StringVar()
        output_entry = ctk.CTkEntry(output_input_frame, textvariable=self.output_var, height=35)
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            output_input_frame, 
            text="Browse", 
            command=self.browse_output_file,
            width=80,
            height=35
        ).pack(side="right")

        # Key Specs settings
        specs_frame = ctk.CTkFrame(left_col)
        specs_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(specs_frame, text="Specifications CSV (optional):", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))

        specs_input_row = ctk.CTkFrame(specs_frame)
        specs_input_row.pack(fill="x", padx=10, pady=(0, 6))

        self.specs_path_var = ctk.StringVar(value=self.config.SPECS_CSV_PATH)
        specs_entry = ctk.CTkEntry(specs_input_row, textvariable=self.specs_path_var, height=35)
        specs_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            specs_input_row,
            text="Browse",
            command=self.browse_specs_file,
            width=80,
            height=35
        ).pack(side="right")

        self.use_specs_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(specs_frame, text="Use specifications CSV for enhanced descriptions", variable=self.use_specs_var).pack(anchor="w", padx=10, pady=(0, 10))
        
        # Test section
        test_frame = ctk.CTkFrame(left_col)
        test_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkLabel(test_frame, text="Test Single Product", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        test_input_frame = ctk.CTkFrame(test_frame)
        test_input_frame.pack(fill="x", padx=10, pady=10)
        
        # Part number
        ctk.CTkLabel(test_input_frame, text="Part Number:").pack(anchor="w", padx=10, pady=(10, 5))
        self.test_part_var = ctk.StringVar(value="C1F002CES")
        ctk.CTkEntry(
            test_input_frame, 
            textvariable=self.test_part_var, 
            height=35,
        ).pack(fill="x", padx=10, pady=(0, 10))
        
        # Manufacturer
        ctk.CTkLabel(test_input_frame, text="Manufacturer:").pack(anchor="w", padx=10, pady=(10, 5))
        self.test_manufacturer_var = ctk.StringVar(value="Hammond Power Services")
        ctk.CTkEntry(
            test_input_frame, 
            textvariable=self.test_manufacturer_var, 
            height=35,
        ).pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            test_input_frame, 
            text="Test Product", 
            command=self.test_product,
            height=35
        ).pack(pady=10)
        
        # Action buttons frame
        button_frame = ctk.CTkFrame(right_col)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # Buttons
        ctk.CTkButton(
            button_frame, 
            text="Setup Ollama", 
            command=self.setup_ollama,
            height=40
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Process CSV", 
            command=self.process_csv,
            height=40
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Test CSV", 
            command=self.test_csv_load,
            height=40
        ).pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Clear Log", 
            command=self.clear_log,
            height=40
        ).pack(side="left", padx=10, pady=10)
        
        # Progress bar
        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(right_col)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(right_col, textvariable=self.status_var, font=ctk.CTkFont(size=12))
        status_label.pack(pady=5)
        
        # Log area
        log_frame = ctk.CTkFrame(right_col)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="Log Output", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        self.log_text = ctk.CTkTextbox(log_frame, height=200)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Thread-safe UI helpers
        self._main_thread_id = threading.get_ident()
    
    def enqueue_message(self, message: str):
        """Thread-safe: place a log message into the processing queue."""
        try:
            self.processing_queue.put_nowait(message)
        except queue.Full:
            pass
 
    def browse_file(self):
        """Browse for input CSV file"""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
    
    def browse_output_file(self):
        """Browse for output CSV file"""
        filename = filedialog.asksaveasfilename(
            title="Save Output CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_var.set(filename)
    
    def browse_specs_file(self):
        """Browse for Key Specs CSV file"""
        filename = filedialog.askopenfilename(
            title="Select Specifications CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.specs_path_var.set(filename)
            # Force re-init of processor to pick up new path
            self.processor = None
    
    def log_message(self, message):
        """Add message to log area"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the log area"""
        self.log_text.delete("1.0", "end")
    
    def set_status(self, text: str):
        """Thread-safe: update status label from any thread."""
        self.root.after(0, self.status_var.set, text)
    
    def show_info(self, title: str, text: str):
        """Thread-safe: show info messagebox."""
        self.root.after(0, lambda: messagebox.showinfo(title, text))
    
    def show_error(self, title: str, text: str):
        """Thread-safe: show error messagebox."""
        self.root.after(0, lambda: messagebox.showerror(title, text))
    
    def setup_ollama(self):
        """Setup Ollama in a separate thread"""
        def setup_thread():
            self.set_status("Setting up Ollama...")
            self.enqueue_message("🔧 Setting up Ollama...")
            
            try:
                import subprocess
                import requests
                
                # Check if Ollama is installed
                try:
                    subprocess.run(['ollama', '--version'], check=True, capture_output=True)
                    self.enqueue_message("✅ Ollama is installed")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.enqueue_message("❌ Ollama is not installed")
                    self.enqueue_message("Please install Ollama from: https://ollama.ai/")
                    self.set_status("Setup failed - Ollama not installed")
                    return
                
                # Check if configured model exists, pull if missing
                try:
                    from llm_client import LLMClient
                    client = LLMClient(self.config)
                    
                    # Test connection
                    if not client.test_connection():
                        self.enqueue_message("❌ Cannot connect to Ollama")
                        self.set_status("Setup failed - Cannot connect to Ollama")
                        return
                    
                    model_name = self.config.OLLAMA_MODEL
                    models = client.list_models()
                    if model_name in models:
                        self.enqueue_message(f"✅ Model available: {model_name}")
                    else:
                        self.enqueue_message(f"📥 Downloading model: {model_name}...")
                        if client.pull_model(model_name):
                            self.enqueue_message("✅ Model downloaded successfully")
                        else:
                            self.enqueue_message("❌ Failed to download model")
                            self.set_status("Setup failed - Model download failed")
                            return
                    
                    self.enqueue_message("✅ Setup completed successfully!")
                    self.set_status("Setup completed")
                    
                except Exception as e:
                    self.enqueue_message(f"❌ Error setting up Ollama: {str(e)}")
                    self.set_status("Setup failed")
                    
            except Exception as e:
                self.enqueue_message(f"❌ Setup error: {str(e)}")
                self.set_status("Setup failed")
        
        threading.Thread(target=setup_thread, daemon=True).start()
    
    def test_product(self):
        """Test with a single product"""
        part_number = self.test_part_var.get().strip()
        manufacturer = self.test_manufacturer_var.get().strip()
        
        if not part_number or not manufacturer:
            messagebox.showerror("Error", "Please enter both part number and manufacturer")
            return
        
        def test_thread():
            self.set_status("Testing product...")
            self.enqueue_message(f"🧪 Testing: {part_number} - {manufacturer}")
            
            try:
                # Apply HPS settings and recreate processor to ensure fresh config
                self.config.SPECS_CSV_PATH = self.specs_path_var.get().strip() or self.config.SPECS_CSV_PATH
                self.processor = ProductDescriptionProcessor(self.config)
                # Wire UI callbacks
                self.processor.log_callback = self.enqueue_message
                if not self.use_specs_var.get():
                    # Disable specs by clearing lookup
                    self.processor.specs_lookup = None
                
                # Optional: preflight log whether specs exist
                if self.processor.specs_lookup and self.processor.specs_lookup.has_data():
                    specs = self.processor.specs_lookup.get_specs(part_number)
                    if specs:
                        self.enqueue_message("ℹ️ Specifications found; using enhanced specs for generation")
                    else:
                        self.enqueue_message("ℹ️ No specifications found for this part; using LLM analysis")

                title, description = self.processor.process_single_product(part_number, manufacturer)
                
                self.enqueue_message(f"\n✅ Generated Content:")
                self.enqueue_message(f"Title: {title}")
                self.enqueue_message(f"Description: {description}")
                self.set_status("Test completed")
                
            except Exception as e:
                self.enqueue_message(f"❌ Test failed: {str(e)}")
                self.set_status("Test failed")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def process_csv(self):
        """Process CSV file"""
        input_file = self.file_var.get().strip()
        output_file = self.output_var.get().strip() or None
        
        if not input_file:
            messagebox.showerror("Error", "Please select an input CSV file")
            return
        
        if not Path(input_file).exists():
            messagebox.showerror("Error", "Input file does not exist")
            return
        
        def process_thread():
            self.status_var.set("Processing CSV...")
            self.progress_bar.set(0)
            self.enqueue_message(f"🚀 Starting processing of {input_file}")
            
            try:
                # Ensure output directory exists with proper permissions
                self.enqueue_message("🔧 Ensuring output directory permissions...")
                if not self.config.ensure_output_dir():
                    self.enqueue_message("❌ Failed to create output directory with proper permissions")
                    self.set_status("Setup failed - Output directory issue")
                    return
                
                # Recreate processor so it picks up current HPS settings
                self.config.SPECS_CSV_PATH = self.specs_path_var.get().strip() or self.config.SPECS_CSV_PATH
                self.processor = ProductDescriptionProcessor(self.config)
                # Wire UI callbacks
                self.processor.log_callback = self.enqueue_message
                def _on_progress(done, total):
                    try:
                        ratio = 0 if total == 0 else float(done)/float(total)
                    except Exception:
                        ratio = 0
                    self.root.after(0, self.progress_bar.set, ratio)
                    self.root.after(0, self.status_var.set, f"Processing {done}/{total} ({int(ratio*100)}%)")
                self.processor.progress_callback = _on_progress
                if not self.use_specs_var.get():
                    self.processor.specs_lookup = None
                 
                output_file_path = self.processor.process_csv(input_file, output_file)
                
                self.enqueue_message(f"✅ Processing completed!")
                self.enqueue_message(f"📁 Results saved to: {output_file_path}")
                self.progress_bar.set(1.0)
                self.set_status("Processing completed")
                
                messagebox.showinfo("Success", f"Processing completed!\nResults saved to: {output_file_path}")
                
            except Exception as e:
                self.enqueue_message(f"❌ Processing failed: {str(e)}")
                self.set_status("Processing failed")
                messagebox.showerror("Error", f"Processing failed: {str(e)}")
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def test_csv_load(self):
        """Test CSV file loading and structure"""
        input_file = self.file_var.get().strip()
        
        if not input_file:
            messagebox.showerror("Error", "Please select an input CSV file")
            return
        
        if not Path(input_file).exists():
            messagebox.showerror("Error", "Input file does not exist")
            return
        
        def test_thread():
            self.status_var.set("Testing CSV...")
            self.enqueue_message(f"🧪 Testing CSV file: {input_file}")
            
            try:
                # Create processor for testing
                self.config.SPECS_CSV_PATH = self.specs_path_var.get().strip() or self.config.SPECS_CSV_PATH
                self.processor = ProductDescriptionProcessor(self.config)
                
                # Test CSV loading
                if self.processor.test_csv_load(input_file):
                    self.enqueue_message("✅ CSV test passed! File is ready for processing.")
                    self.set_status("CSV test passed")
                else:
                    self.enqueue_message("❌ CSV test failed! Check the file structure.")
                    self.set_status("CSV test failed")
                    
            except Exception as e:
                self.enqueue_message(f"❌ CSV test error: {str(e)}")
                self.set_status("CSV test error")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def process_queue(self):
        """Process the message queue"""
        try:
            while True:
                message = self.processing_queue.get_nowait()
                self.log_message(message)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)

def main():
    """Start the GUI application"""
    root = ctk.CTk()
    app = ProductGeneratorGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main() 