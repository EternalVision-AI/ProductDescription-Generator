import os
import pandas as pd
from typing import Optional, Dict, List


class SpecsLookup:
    """Loads any specs CSV file and exposes lookup by part number.

    The lookup is case-insensitive and tries common part number columns present in any specs file.
    """

    DEFAULT_PART_COLUMNS: List[str] = [
        'Summary_Part Number',
        'Details_Part Number:',
        'Summary_Item:',
        'Part Number',
        'Part Number',
        'Internal ID'
    ]

    # Prefer concise, reliable summary fields for prompting
    PREFERRED_FIELDS: List[str] = [
        # Identity
        'Summary_Part Number', 'Summary_Product Line:', 'Summary_Item:',
        'Part Number', 'Brand', 'Family', 'Manufacturer', 'Item Category', 'Item Subcategory',
        # Electrical core
        'Summary_Phase:', 'Summary_Standard kVA:', 'Summary_Primary Voltage:',
        'Summary_Secondary Voltage:', 'Summary_Vector Configuration:',
        'Summary_Frequency:', 'Summary_Temperature Rise:', 'Summary_Material:',
        'Phase', 'Voltage', 'Amperage', 'AIC rating', 'Connection', 'Poles',
        # Construction / enclosure
        'Summary_Enclosure Type:', 'Summary_Enclosure Grade:', 'Summary_Sound Level:',
        'Summary_Electrostatic Shield:', 'Summary_Efficiency Regulation:',
        'Protection', 'Functions', 'Panel Type', 'Breaker Type', 'Frame Size',
        # Seismic / compliance
        'Summary_Seismic Compliance:', 'Summary_Seismic Standard Value:',
        'Summary_Seismic OSHPD:', 'Summary_Seismic IP:', 'Summary_Seismic ZH:',
        'Summary_Seismic SDS Value:',
        # Connections
        'Summary_Primary Connection:', 'Summary_Secondary Connection:',
        # Other potentially helpful
        'Summary_Connection:', 'Summary_System Voltage:', 'Summary_Rated Current:',
        'Summary_Cable Length:', 'Temp Rating', 'Wire', 'Standards', 'Terminal Connection', 
        'Certification', 'Configuration', 'Switch Style', 'Weight', 'Dimensions'
    ]

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None
        self._index: Dict[str, int] = {}
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
        # Build index by best-effort part number columns
        self._index.clear()
        part_cols = [c for c in self.DEFAULT_PART_COLUMNS if c in df.columns]
        if not part_cols:
            # Fall back to first column if unknown
            part_cols = [df.columns[0]]
        for idx, row in df.iterrows():
            for col in part_cols:
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

        # Pull preferred fields if present and non-empty
        for field in self.PREFERRED_FIELDS:
            if field in row.index:
                value = str(row[field]).strip()
                if value and value.upper() not in {"N / A", "N/A", "NA"}:
                    specs[field] = value

        # Ensure the part number field is present for reference
        specs.setdefault('Summary_Part Number', part_number)
        return specs 