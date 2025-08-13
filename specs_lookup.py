import os
import pandas as pd
from typing import Optional, Dict, List
import json
import re


class SpecsLookup:
    """Loads any specs CSV file and exposes lookup by part number using LLM for dynamic column detection.

    The lookup is case-insensitive and uses LLM to determine the best columns for part numbers and specifications.
    """

    def __init__(self, csv_path: str, llm_client=None):
        self.csv_path = csv_path
        self.llm_client = llm_client
        self._df: Optional[pd.DataFrame] = None
        self._index: Dict[str, int] = {}
        self.column_mapping: Optional[Dict] = None
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.csv_path):
            # Defer failure to lookup time to allow non-specs runs
            return
        
        # Read CSV with proper encoding handling
        try:
            # Try UTF-8 first
            df = pd.read_csv(self.csv_path, dtype=str, keep_default_na=False, na_values=[], engine='python', encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Try with latin-1 if UTF-8 fails
                df = pd.read_csv(self.csv_path, dtype=str, keep_default_na=False, na_values=[], engine='python', encoding='latin-1')
            except Exception as e:
                # Final fallback with error handling
                df = pd.read_csv(self.csv_path, dtype=str, keep_default_na=False, na_values=[], engine='python', encoding='utf-8', errors='replace')
        
        # Normalize column names (strip spaces)
        df.columns = [c.strip() for c in df.columns]
        self._df = df
        
        # Use LLM to determine column mapping if available
        if self.llm_client:
            self._determine_column_mapping_with_llm()
        
        # Build index using detected or fallback part number columns
        self._build_index()

    def _determine_column_mapping_with_llm(self):
        """Use LLM to dynamically determine column mapping for specs CSV"""
        try:
            if not self.llm_client or self._df is None or self._df.empty:
                return
            
            # Get sample data for LLM analysis
            sample_data = self._df.head(3).to_dict('records')
            columns_info = {
                'columns': list(self._df.columns),
                'sample_data': sample_data,
                'total_rows': len(self._df)
            }
            
            # Create prompt for LLM to analyze specs CSV structure
            analysis_prompt = f"""
            Analyze this specifications CSV structure and determine the column mapping for product specifications lookup.
            
            CSV Columns: {columns_info['columns']}
            Sample Data (first 3 rows): {columns_info['sample_data']}
            Total Rows: {columns_info['total_rows']}
            
            Please identify:
            1. Part Number column (the unique identifier for each product)
            2. All other column
            
            Return your analysis in this exact JSON format:
            {{
                "part_number_column": "exact_column_name",
                "relevant_spec_columns": ["column1", "column2", "column3", ...],
                "reasoning": "brief explanation of your choices"
            }}
            
            """
            
            # Get LLM analysis
            analysis_result = self.llm_client._analyze_csv_structure(analysis_prompt)
            
            if analysis_result:
                self.column_mapping = analysis_result
                print(f"✅ LLM Specs Column Analysis:")
                print(f"  Part Number: {analysis_result.get('part_number_column', 'Not found')}")
                print(f"  Relevant Specs: {analysis_result.get('relevant_spec_columns', [])}")
                print(f"  Reasoning: {analysis_result.get('reasoning', 'No reasoning provided')}")
            else:
                print(f"⚠️ LLM analysis failed, using fallback column detection")
                self.column_mapping = None
                
        except Exception as e:
            print(f"⚠️ Error in LLM column analysis: {str(e)}")
            self.column_mapping = None

    def _build_index(self):
        """Build index using detected or fallback part number columns"""
        if self._df is None or self._df.empty:
            return
        
        self._index.clear()
        
        # Use LLM-detected part number column if available
        if self.column_mapping and 'part_number_column' in self.column_mapping:
            part_cols = [self.column_mapping['part_number_column']]
        else:
            # Fallback to common part number column patterns
            fallback_cols = ['Part Number', 'PartNumber', 'Part_Number', 'Item', 'ID', 'SKU']
            part_cols = [c for c in fallback_cols if c in self._df.columns]
            if not part_cols:
                # Final fallback to first column
                part_cols = [self._df.columns[0]]
        
        # Build index
        for idx, row in self._df.iterrows():
            for col in part_cols:
                if col in row.index:
                    value = str(row.get(col, '')).strip()
                    if value:
                        key = value.upper()
                        # Only set first occurrence
                        if key not in self._index:
                            self._index[key] = idx

    def has_data(self) -> bool:
        return self._df is not None and not self._df.empty

    def get_specs(self, part_number: str) -> Optional[Dict[str, str]]:
        """Return a compact dict of reliable specs for the given part number, or None if not found."""
        if self._df is None or self._df.empty or not part_number:
            return None
        
        key = str(part_number).strip().upper()
        idx = self._index.get(key)
        if idx is None:
            return None
        
        row = self._df.iloc[idx]
        specs: Dict[str, str] = {}

        # Use LLM-detected relevant spec columns if available
        if self.column_mapping and 'relevant_spec_columns' in self.column_mapping:
            relevant_columns = self.column_mapping['relevant_spec_columns']
        else:
            # Fallback to common spec column patterns
            relevant_columns = [
                'Voltage', 'Amperage', 'Poles', 'Phase', 'AIC', 'Rating',
                'Type', 'Size', 'Connection', 'Protection', 'Function'
            ]

        # Extract specs from relevant columns
        for field in relevant_columns:
            if field in row.index:
                value = str(row[field]).strip()
                if value and value.upper() not in {"N / A", "N/A", "NA", ""}:
                    specs[field] = value

        # Ensure the part number field is present for reference
        part_number_col = self.column_mapping.get('part_number_column', 'Part Number') if self.column_mapping else 'Part Number'
        specs.setdefault(part_number_col, part_number)
        
        return specs 