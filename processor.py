import os
import pandas as pd
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from tqdm import tqdm
import time
from colorama import Fore, Style, init
import threading
import queue as _queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config
from llm_client import LLMClient
from specs_lookup import SpecsLookup

# Initialize colorama for colored output
init()

logger = logging.getLogger(__name__)

class ProductDescriptionProcessor:
    """Main processor for generating product descriptions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm_client = LLMClient(config)
        # Initialize specs lookup (optional if file missing)
        try:
            self.specs_lookup = SpecsLookup(self.config.SPECS_CSV_PATH, self.llm_client)
            if self.specs_lookup.has_data():
                print(f"{Fore.GREEN}✅ Loaded specs from: {self.config.SPECS_CSV_PATH}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ Specs file not available or empty: {self.config.SPECS_CSV_PATH}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not load specs file: {str(e)}{Style.RESET_ALL}")
            self.specs_lookup = None
        self.stats = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
        # Optional UI hooks (set by GUI)
        self.log_callback = None
        self.progress_callback = None
        
        # Create output directory if it doesn't exist with proper permissions
        self._ensure_output_directory()

    def _ensure_output_directory(self):
        """Ensure output directory exists with proper permissions (Mac-compatible)"""
        try:
            output_dir = self.config.OUTPUT_DIR
            
            # Remove existing directory if it has permission issues
            if os.path.exists(output_dir):
                try:
                    # Test write permissions
                    test_file = os.path.join(output_dir, f"test_write_{os.getpid()}.tmp")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    print(f"{Fore.GREEN}✅ Output directory permissions OK{Style.RESET_ALL}")
                    return
                except (PermissionError, OSError):
                    print(f"{Fore.YELLOW}⚠️ Output directory has permission issues, recreating...{Style.RESET_ALL}")
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
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"{Fore.GREEN}✅ Output directory created with proper permissions{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Cannot write to output directory: {str(e)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}💡 Try running: chmod 755 {output_dir}{Style.RESET_ALL}")
                raise
                
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to create output directory: {str(e)}{Style.RESET_ALL}")
            raise

    def _log(self, message: str):
        try:
            if self.log_callback:
                self.log_callback(message)
        except Exception:
            pass
        # Always print to console too
        print(message)

    def _emit_progress(self, done: int, total: int):
        try:
            if self.progress_callback:
                self.progress_callback(done, total)
        except Exception:
            pass

    def _is_specs_available(self) -> bool:
        """Safely check if specs lookup is available and has data"""
        try:
            return (hasattr(self, 'specs_lookup') and 
                   self.specs_lookup is not None and 
                   self.specs_lookup.has_data())
        except Exception:
            return False
    
    def _analyze_csv_structure(self, df: pd.DataFrame):
        """Analyze CSV structure to help identify manufacturer columns"""
        print(f"\n{Fore.CYAN}CSV Structure Analysis:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Look for potential manufacturer-related columns
        manufacturer_keywords = ['manufacturer', 'brand', 'family', 'make', 'company', 'vendor', 'supplier']
        potential_manufacturer_cols = []
        
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in manufacturer_keywords:
                if keyword in col_lower:
                    potential_manufacturer_cols.append(col)
                    break
        
        if potential_manufacturer_cols:
            print(f"{Fore.GREEN}Potential manufacturer columns found:{Style.RESET_ALL}")
            for col in potential_manufacturer_cols:
                non_empty_count = df[col].dropna().shape[0]
                unique_values = df[col].dropna().unique()
                print(f"  - {col}: {non_empty_count} non-empty values, {len(unique_values)} unique values")
                if len(unique_values) <= 10:
                    print(f"    Sample values: {list(unique_values)}")
        else:
            print(f"{Fore.YELLOW}No obvious manufacturer columns found{Style.RESET_ALL}")
        
        # Show column types and non-null counts
        print(f"\n{Fore.CYAN}Column Summary:{Style.RESET_ALL}")
        for col in df.columns:
            non_null_count = df[col].count()
            null_count = df[col].isnull().sum()
            print(f"  {col}: {non_null_count} non-null, {null_count} null")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
    
    def validate_csv_structure(self, df: pd.DataFrame) -> bool:
        """Validate that the CSV has the required structure for processing"""
        try:
            # Check for required columns
            if 'Part Number' not in df.columns:
                print(f"{Fore.RED}❌ Missing required column: 'Part Number'{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Available columns: {list(df.columns)}{Style.RESET_ALL}")
                return False
            
            # Check for data
            if len(df) == 0:
                print(f"{Fore.RED}❌ CSV file is empty{Style.RESET_ALL}")
                return False
            
            # Check for non-empty part numbers
            valid_parts = df['Part Number'].dropna()
            if len(valid_parts) == 0:
                print(f"{Fore.RED}❌ No valid part numbers found in CSV{Style.RESET_ALL}")
                return False
            
            print(f"{Fore.GREEN}✅ CSV structure validation passed{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Found {len(valid_parts)} valid part numbers{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ CSV validation error: {str(e)}{Style.RESET_ALL}")
            return False
    
    def process_csv(self, input_file: str, output_file: str = None) -> str:
        """
        Process a CSV file and generate descriptions for all products
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            
        Returns:
            Path to the output file
        """
        self.stats['start_time'] = datetime.now()
        
        print(f"{Fore.CYAN}Starting product description generation...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Input file: {input_file}{Style.RESET_ALL}")
        
        # Load CSV file
        try:
            # Try different encodings for CSV reading
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_file, encoding='latin-1')
                except Exception as e:
                    # Final fallback with error handling
                    df = pd.read_csv(input_file, encoding='utf-8', errors='replace')
            
            # Remove unnamed columns (columns that start with 'Unnamed:')
            unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed:')]
            if unnamed_cols:
                print(f"{Fore.YELLOW}Removing {len(unnamed_cols)} unnamed columns{Style.RESET_ALL}")
                df = df.drop(columns=unnamed_cols)
            
            print(f"{Fore.GREEN}Loaded {len(df)} products from CSV{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error loading CSV file: {str(e)}{Style.RESET_ALL}")
            raise
        
        # Validate CSV structure
        # Dynamic: do not hard-require fixed column names here; rely on LLM mapping later
        if 'Manufacturer' in df.columns:
            non_empty_manufacturers = df['Manufacturer'].dropna()
            if len(non_empty_manufacturers) > 0:
                print(f"{Fore.GREEN}Found {len(non_empty_manufacturers)} products with manufacturer info{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Sample manufacturers: {list(non_empty_manufacturers.unique())[:5]}{Style.RESET_ALL}")
 
        # Debug: Show column names and first few rows
        print(f"{Fore.CYAN}Available columns: {list(df.columns)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}First row sample: {dict(df.iloc[0]) if len(df) > 0 else 'No data'}{Style.RESET_ALL}")
        
        # Analyze CSV structure for potential manufacturer columns
        self._analyze_csv_structure(df)
        
        # Use LLM to dynamically determine column mapping and relevant specs
        if self._is_specs_available():
            self._determine_column_mapping_with_llm(df)
        
        # If we still don't know the part number column and 'Part Number' is absent, fail fast
        if ((not hasattr(self, 'column_mapping')) or (not self.column_mapping) or (not self.column_mapping.get('part_number_column'))) and ('Part Number' not in df.columns):
            raise ValueError("Unable to determine Part Number column dynamically. Ensure the first rows include a part number-like column.")
        
        # Test LLM connection
        print(f"{Fore.CYAN}Testing LLM connection...{Style.RESET_ALL}")
        if not self.llm_client.test_connection():
            print(f"{Fore.RED}Failed to connect to LLM service. Please check your setup.{Style.RESET_ALL}")
            raise ConnectionError("LLM service not available")
        print(f"{Fore.GREEN}LLM connection successful!{Style.RESET_ALL}")
        
        # Ensure output directory exists with proper permissions
        self._ensure_output_directory()
        
        # Generate output filename
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                self.config.OUTPUT_DIR, 
                f"processed_{timestamp}.csv"
            )
        
        # Process products and save results one by one
        self._process_products_streaming(df, output_file)
        
        self.stats['end_time'] = datetime.now()
        self._print_summary(output_file)
        
        return output_file
    
    def _process_products_streaming(self, df: pd.DataFrame, output_file: str):
        """
        Process all products in the DataFrame and save results one by one to CSV
        
        Args:
            df: DataFrame containing product data
            output_file: Path to output CSV file
        """
        # Determine part number column dynamically
        part_col = None
        if hasattr(self, 'column_mapping') and self.column_mapping:
            part_col = self.column_mapping.get('part_number_column')
        if not part_col and 'Part Number' in df.columns:
            part_col = 'Part Number'
        
        # Filter out rows missing part number if we identified the column
        valid_df = df.copy()
        if part_col and part_col in df.columns:
            valid_df = df[df[part_col].astype(str).str.strip() != '']
        skipped_count = len(df) - len(valid_df)
        if skipped_count > 0:
            print(f"{Fore.YELLOW}Skipped {skipped_count} rows with missing data{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}Processing {len(valid_df)} products...{Style.RESET_ALL}")
        self._log(f"Processing {len(valid_df)} products...")
        
        # Create output CSV file with headers (with Mac permission handling)
        output_columns = list(valid_df.columns) + ['WEB TITLE', 'WEB DESCRIPTION']
        
        # Ensure output directory exists before creating file
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            self._ensure_output_directory()
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                import csv
                writer = csv.writer(csvfile)
                writer.writerow(output_columns)
        except PermissionError as e:
            print(f"{Fore.RED}Permission denied creating CSV file: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Trying to fix permissions...{Style.RESET_ALL}")
            
            # Try to fix permissions and retry
            try:
                import stat
                os.chmod(output_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    writer.writerow(output_columns)
                print(f"{Fore.GREEN}✅ Permission fixed, file created successfully{Style.RESET_ALL}")
            except Exception as retry_e:
                print(f"{Fore.RED}❌ Still cannot create file after permission fix: {str(retry_e)}{Style.RESET_ALL}")
                raise
        
        # Process in parallel batches for better performance
        total_count = len(valid_df)
        done_count = 0
        self._emit_progress(done_count, total_count)
        
        # Use parallel processing for better performance
        max_workers = min(4, len(valid_df))  # Limit to 4 workers to avoid overwhelming the system
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches for parallel processing
            future_to_batch = {}
            for i in range(0, len(valid_df), self.config.BATCH_SIZE):
                batch = valid_df.iloc[i:i + self.config.BATCH_SIZE]
                future = executor.submit(self._process_batch_streaming, batch, output_file)
                future_to_batch[future] = batch
            
            # Process completed batches
            for future in as_completed(future_to_batch):
                try:
                    processed_in_batch = future.result()
                    done_count += processed_in_batch
                    self._emit_progress(done_count, total_count)
                except Exception as e:
                    print(f"{Fore.RED}❌ Batch processing error: {str(e)}{Style.RESET_ALL}")
                    self._log(f"Batch processing error: {str(e)}")
                    # Still count the batch as processed to avoid hanging
                    done_count += len(future_to_batch[future])
                    self._emit_progress(done_count, total_count)
        
        print(f"{Fore.GREEN}All results saved to: {output_file}{Style.RESET_ALL}")
        self._log(f"All results saved to: {output_file}")
    
    def _process_batch_streaming(self, batch_df: pd.DataFrame, output_file: str) -> int:
        """
        Process a batch of products and save results directly to CSV with parallel processing
        
        Args:
            batch_df: DataFrame containing a batch of products
            output_file: Path to output CSV file
        """
        processed_rows = 0
        
        # Process products in parallel within the batch
        max_workers = min(2, len(batch_df))  # Limit workers per batch
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all products in the batch for parallel processing
            future_to_row = {}
            for idx, row in batch_df.iterrows():
                future = executor.submit(self._process_single_product, row, output_file)
                future_to_row[future] = (idx, row)
            
            # Collect results as they complete
            for future in as_completed(future_to_row):
                try:
                    result = future.result()
                    if result:
                        processed_rows += 1
                except Exception as e:
                    idx, row = future_to_row[future]
                    part_num = str(row.get('Part Number', 'UNKNOWN')) if 'Part Number' in row else 'UNKNOWN'
                    print(f"{Fore.RED}✗ Failed: {part_num} - {str(e)}{Style.RESET_ALL}")
                    self._log(f"Failed: {part_num} → {str(e)}")
                    # Write error row to CSV
                    self._write_row_to_csv(row, "ERROR", f"Failed to generate: {str(e)}", output_file)
                    self.stats['failed'] += 1
                    processed_rows += 1
        
        return processed_rows

    def _process_single_product(self, row: pd.Series, output_file: str) -> bool:
        """
        Process a single product
        
        Args:
            row: DataFrame row containing product data
            output_file: Path to output CSV file
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Use dynamic column mapping if available
            if hasattr(self, 'column_mapping') and self.column_mapping:
                part_number_col = self.column_mapping.get('part_number_column', 'Part Number')
                manufacturer_col = self.column_mapping.get('manufacturer_column', 'Manufacturer')
            else:
                part_number_col = 'Part Number'
                manufacturer_col = 'Manufacturer'
            
            # Resolve part number robustly
            part_number = ''
            if part_number_col in row and pd.notna(row[part_number_col]):
                part_number = str(row[part_number_col]).strip()
            elif 'Part Number' in row and pd.notna(row['Part Number']):
                part_number = str(row['Part Number']).strip()
            else:
                # Try any column that looks like a PN
                for col in row.index:
                    val = str(row[col]).strip()
                    if val and any(c.isalpha() for c in val) and any(c.isdigit() for c in val):
                        part_number = val
                        break
            if not part_number:
                print(f"{Fore.YELLOW}Skipping row with empty part number{Style.RESET_ALL}")
                # Write row with error message
                self._write_row_to_csv(row, "SKIPPED", "Empty part number", output_file)
                return True
            
            # Get manufacturer from detected column
            manufacturer = 'Unknown Manufacturer'
            if manufacturer_col in row and pd.notna(row[manufacturer_col]):
                manufacturer = str(row[manufacturer_col]).strip()
                if not manufacturer:
                    manufacturer = 'Unknown Manufacturer'
            else:
                manufacturer = 'Unknown Manufacturer'
            
            if not manufacturer or manufacturer == 'Unknown Manufacturer':
                print(f"{Fore.YELLOW}Warning: No manufacturer found for {part_number}, using default{Style.RESET_ALL}")
                self._log(f"No manufacturer found for {part_number}, using default")
            else:
                print(f"{Fore.CYAN}Using manufacturer: {manufacturer} for {part_number}{Style.RESET_ALL}")
                self._log(f"Using manufacturer: {manufacturer} for {part_number}")
             
            # Prefer specs from the dedicated specs CSV (dynamic via LLM) if available
            reliable_specs: Dict[str, str] = {}
            if self._is_specs_available():
                csv_specs = self.specs_lookup.get_specs(part_number)
                if csv_specs:
                    reliable_specs.update(csv_specs)
                    print(f"{Fore.CYAN}Found specs in specs CSV for {part_number}: {len(csv_specs)} fields{Style.RESET_ALL}")
                    self._log(f"Found specs in specs CSV for {part_number}: {len(csv_specs)} fields")

            # Always merge ALL non-empty input row columns as specs (user requirement)
            row_specs: Dict[str, str] = {}
            for col in row.index:
                try:
                    val = row[col]
                    if pd.notna(val):
                        sval = str(val).strip()
                        if sval and not col.startswith('Unnamed:') and col not in ('WEB TITLE', 'WEB DESCRIPTION'):
                            row_specs[col] = sval
                except Exception:
                    continue
            if row_specs:
                reliable_specs.update(row_specs)
                print(f"{Fore.CYAN}Merged {len(row_specs)} input columns for {part_number}{Style.RESET_ALL}")
                self._log(f"Merged {len(row_specs)} input columns for {part_number}")

            # Generate new content
            title, description = self.llm_client.generate_content(
                part_number,
                manufacturer,
                reliable_specs=reliable_specs
            )
            
            self.stats['processed'] += 1
            
            # Print progress for first few items
            if self.stats['processed'] <= 5:
                print(f"{Fore.GREEN}✓ Generated: {part_number} - {manufacturer}{Style.RESET_ALL}")
                self._log(f"Generated: {part_number} - {manufacturer}")

            # Enforce title length <= 80
            title = self._limit_title_length(title, 80)

            # Write result directly to CSV
            self._write_row_to_csv(row, title, description, output_file)
            return True
            
        except Exception as e:
            part_num = str(row.get('Part Number', 'UNKNOWN')) if 'Part Number' in row else 'UNKNOWN'
            logger.error(f"Failed to process {part_num}: {str(e)}")
            # Write error row to CSV
            self._write_row_to_csv(row, "ERROR", f"Failed to generate: {str(e)}", output_file)
            self.stats['failed'] += 1
            return False
    
    def _write_row_to_csv(self, row: pd.Series, title: str, description: str, output_file: str):
        """Write a single row with generated content to CSV file with Mac permission handling"""
        try:
            import csv
            
            # Ensure output directory exists before writing
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                self._ensure_output_directory()
            
            # Try to write with proper error handling
            try:
                with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write original row data plus generated content
                    row_data = list(row.values) + [title, description]
                    writer.writerow(row_data)
            except PermissionError as e:
                print(f"{Fore.RED}Permission denied writing to CSV: {str(e)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}💡 Trying to fix permissions...{Style.RESET_ALL}")
                
                # Try to fix permissions and retry
                try:
                    import stat
                    os.chmod(output_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        row_data = list(row.values) + [title, description]
                        writer.writerow(row_data)
                    print(f"{Fore.GREEN}✅ Permission fixed, write successful{Style.RESET_ALL}")
                except Exception as retry_e:
                    print(f"{Fore.RED}❌ Still cannot write after permission fix: {str(retry_e)}{Style.RESET_ALL}")
                    raise
                    
        except Exception as e:
            print(f"{Fore.RED}Error writing to CSV: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Failed to write row to CSV: {str(e)}")
            # Don't re-raise to avoid stopping the entire process

    def _limit_title_length(self, title: str, max_len: int) -> str:
        if not title:
            return title
        if len(title) <= max_len:
            return title
        # Abbreviation passes
        replacements = {
            'Ampere': 'Amp', 'Amperes': 'Amp', 'Amps': 'Amp',
            'Voltage': 'V', 'Volt': 'V',
            'Ground Fault Circuit Interrupter (GFCI)': 'GFCI',
            'Ground Fault Circuit Interrupter': 'GFCI',
            'Molded Case Circuit Breaker': 'MCCB',
            'Circuit Breaker': 'Breaker',
            'Solid-State Protection': 'Solid-State',
            'Solid State Protection': 'Solid-State',
            'Bolt-On Connections': 'Bolt-On',
            '2-Pole': '2P', '3-Pole': '3P', '4-Pole': '4P',
            '  ': ' '
        }
        shortened = title
        for src, dst in replacements.items():
            shortened = shortened.replace(src, dst)
        shortened = ' '.join(shortened.split())  # normalize spaces
        if len(shortened) <= max_len:
            return shortened
        # Hard cap
        return shortened[:max_len].rstrip()
    
    def _determine_column_mapping_with_llm(self, df: pd.DataFrame):
        """Use LLM to dynamically determine column mapping and relevant specs from CSV structure"""
        try:
            print(f"{Fore.CYAN}Using LLM to analyze input CSV structure and determine column mapping...{Style.RESET_ALL}")
            
            # Get first few rows as sample data
            sample_data = df.head(3).to_dict('records')
            columns_info = {
                'columns': list(df.columns),
                'sample_data': sample_data,
                'total_rows': len(df)
            }
            
            # Create prompt for LLM to analyze CSV structure
            analysis_prompt = f"""
            Analyze this CSV structure and determine the column mapping for product specifications.
            
            CSV Columns: {columns_info['columns']}
            Sample Data (first 3 rows): {columns_info['sample_data']}
            Total Rows: {columns_info['total_rows']}
            
            Please identify:
            1. Part Number column (the unique identifier for each product)
            2. Manufacturer column (the company that makes the product)
            3. All other columns
            
            Return your analysis in this exact JSON format:
            {{
                "part_number_column": "exact_column_name",
                "manufacturer_column": "exact_column_name", 
                "relevant_spec_columns": ["column1", "column2", "column3", ...],
                "reasoning": "brief explanation of your choices"
            }}
            
            """
            
            # Get LLM analysis
            analysis_result = self.llm_client._analyze_csv_structure(analysis_prompt)
            
            if analysis_result:
                # Store the column mapping for use in processing
                self.column_mapping = analysis_result
                print(f"{Fore.GREEN}✅ LLM Column Analysis:{Style.RESET_ALL}")
                print(f"  Part Number: {analysis_result.get('part_number_column', 'Not found')}")
                print(f"  Manufacturer: {analysis_result.get('manufacturer_column', 'Not found')}")
                print(f"  Relevant Specs: {analysis_result.get('relevant_spec_columns', [])}")
                print(f"  Reasoning: {analysis_result.get('reasoning', 'No reasoning provided')}")
            else:
                print(f"{Fore.YELLOW}⚠️ LLM analysis failed, using default column detection{Style.RESET_ALL}")
                self.column_mapping = None
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error in LLM column analysis: {str(e)}{Style.RESET_ALL}")
            self.column_mapping = None
    
    def _determine_input_csv_mapping_with_llm(self, df: pd.DataFrame):
        """Use LLM to determine column mapping for input CSV when no specs file is available"""
        try:
            print(f"{Fore.CYAN}Using LLM to analyze input CSV structure...{Style.RESET_ALL}")
            
            # Get first few rows as sample data
            sample_data = df.head(3).to_dict('records')
            columns_info = {
                'columns': list(df.columns),
                'sample_data': sample_data,
                'total_rows': len(df)
            }
            
            # Create prompt for LLM to analyze input CSV structure
            analysis_prompt = f"""
            Analyze this input CSV structure and determine the column mapping for product processing.
            
            CSV Columns: {columns_info['columns']}
            Sample Data (first 3 rows): {columns_info['sample_data']}
            Total Rows: {columns_info['total_rows']}
            
            Please identify:
            1. Part Number column (the unique identifier for each product)
            2. Manufacturer column (the company that makes the product)
            3. All other columns 
            
            Return your analysis in this exact JSON format:
            {{
                "part_number_column": "exact_column_name",
                "manufacturer_column": "exact_column_name", 
                "additional_spec_columns": ["column1", "column2", "column3", ...],
                "reasoning": "brief explanation of your choices"
            }}
            """
            
            # Get LLM analysis
            analysis_result = self.llm_client._analyze_csv_structure(analysis_prompt)
            
            if analysis_result:
                # Store the column mapping for use in processing
                self.column_mapping = analysis_result
                print(f"{Fore.GREEN}✅ LLM Input CSV Analysis:{Style.RESET_ALL}")
                print(f"  Part Number: {analysis_result.get('part_number_column', 'Not found')}")
                print(f"  Manufacturer: {analysis_result.get('manufacturer_column', 'Not found')}")
                print(f"  Additional Specs: {analysis_result.get('additional_spec_columns', [])}")
                print(f"  Reasoning: {analysis_result.get('reasoning', 'No reasoning provided')}")
            else:
                print(f"{Fore.YELLOW}⚠️ LLM analysis failed, using default column detection{Style.RESET_ALL}")
                self.column_mapping = None
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error in LLM input CSV analysis: {str(e)}{Style.RESET_ALL}")
            self.column_mapping = None
    
    def _get_dynamic_specs(self, row: pd.Series, part_number: str) -> Dict[str, str]:
        """Get relevant specs dynamically using LLM analysis"""
        if not hasattr(self, 'column_mapping') or not self.column_mapping:
            return None
        
        try:
            # Get relevant spec columns from LLM analysis
            relevant_columns = (
                self.column_mapping.get('relevant_spec_columns', []) + 
                self.column_mapping.get('additional_spec_columns', [])
            )
            
            # Extract specs from the row as a dict
            specs: Dict[str, str] = {}
            for col in relevant_columns:
                if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                    value = str(row[col]).strip()
                    if value and value.upper() not in {"N / A", "N/A", "NA", ""}:
                        specs[col] = value
            
            return specs if specs else None
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error getting dynamic specs: {str(e)}{Style.RESET_ALL}")
            return None
    
    def _print_summary(self, output_file: str):
        """Print processing summary"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}PROCESSING SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Successfully processed: {self.stats['processed']}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗ Failed: {self.stats['failed']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⏭ Skipped: {self.stats['skipped']}{Style.RESET_ALL}")
        print(f"⏱ Duration: {duration}")
        print(f"📁 Output file: {output_file}")
        
        # Calculate performance metrics
        if duration.total_seconds() > 0:
            items_per_second = self.stats['processed'] / duration.total_seconds()
            print(f"⚡ Processing speed: {items_per_second:.2f} items/second")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    def process_single_product(self, part_number: str, manufacturer: str) -> Tuple[str, str]:
        """
        Process a single product for testing
        
        Args:
            part_number: Product part number
            manufacturer: Product manufacturer
            
        Returns:
            Tuple of (title, description)
        """
        print(f"{Fore.CYAN}Testing with single product: {part_number} - {manufacturer}{Style.RESET_ALL}")
        
        # Fast-fail if LLM is not available
        if not self.llm_client.test_connection():
            raise ConnectionError("LLM service not available. Please run Setup and ensure the model is installed.")

        try:
            reliable_specs = None
            if self._is_specs_available():
                reliable_specs = self.specs_lookup.get_specs(part_number)

            print(f"{Fore.CYAN}Generating content...{Style.RESET_ALL}")
            self._log(f"Generating content for {part_number}...")

            result_queue: _queue.Queue = _queue.Queue(maxsize=1)

            def _worker():
                try:
                    title, description = self.llm_client.generate_content(
                        part_number,
                        manufacturer,
                        reliable_specs=reliable_specs
                    )
                    title = self._limit_title_length(title, 80)
                    result_queue.put((title, description))
                except Exception as e:  # propagate exception through queue
                    result_queue.put(e)

            thread = threading.Thread(target=_worker, daemon=True)
            thread.start()
            thread.join(timeout=self.config.REQUEST_TIMEOUT)

            if thread.is_alive():
                raise TimeoutError("LLM generation timed out. Ensure the model is downloaded (Setup), the Ollama service is running, or try a smaller model.")

            result = result_queue.get()
            if isinstance(result, Exception):
                raise result
            title, description = result
            
            self.stats['processed'] += 1
            
            print(f"\n{Fore.GREEN}Generated Content:{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Title:{Style.RESET_ALL} {title}")
            print(f"{Fore.YELLOW}Description:{Style.RESET_ALL} {description}")
            self._log(f"Title: {title}")
            self._log(f"Description: {description[:200]}...")
            
            return title, description
            
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            self._log(f"Error: {str(e)}")
            raise 
    
    def test_csv_load(self, input_file: str) -> bool:
        """Test if a CSV file can be loaded and has the right structure"""
        try:
            print(f"{Fore.CYAN}Testing CSV file: {input_file}{Style.RESET_ALL}")
            
            # Try to load the CSV
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_file, encoding='latin-1')
                except Exception as e:
                    df = pd.read_csv(input_file, encoding='utf-8', errors='replace')
            
            print(f"{Fore.GREEN}✅ CSV loaded successfully: {len(df)} rows{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Columns: {list(df.columns)}{Style.RESET_ALL}")
            
            # Validate structure
            if self.validate_csv_structure(df):
                print(f"{Fore.GREEN}✅ CSV structure is valid{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ CSV structure validation failed{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ CSV test failed: {str(e)}{Style.RESET_ALL}")
            return False 
    
    def test_specs_lookup(self, part_number: str = None) -> bool:
        """Test the specs lookup functionality"""
        try:
            if not self._is_specs_available():
                print(f"{Fore.YELLOW}⚠️ Specs lookup not available{Style.RESET_ALL}")
                return False
            
            if part_number:
                specs = self.specs_lookup.get_specs(part_number)
                if specs:
                    print(f"{Fore.GREEN}✅ Found specs for {part_number}: {len(specs)} fields{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}Sample specs: {dict(list(specs.items())[:3])}{Style.RESET_ALL}")
                    return True
                else:
                    print(f"{Fore.YELLOW}⚠️ No specs found for {part_number}{Style.RESET_ALL}")
                    return False
            else:
                # Test with first available part number
                if hasattr(self.specs_lookup, '_index') and self.specs_lookup._index:
                    test_part = list(self.specs_lookup._index.keys())[0]
                    return self.test_specs_lookup(test_part)
                else:
                    print(f"{Fore.YELLOW}⚠️ No part numbers indexed in specs{Style.RESET_ALL}")
                    return False
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Specs lookup test failed: {str(e)}{Style.RESET_ALL}")
            return False 