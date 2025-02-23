import base64
import pandas as pd
from backend.schemas.schemas import FileBytes

def process_excel_bytes(bytes: FileBytes):
    tables_strings = []
    bytes = base64.b64decode(bytes.bytes_data)
    xls = pd.ExcelFile(bytes)
    for sheet_name in xls.sheet_names:
        sheet_string = pd.read_excel(xls, sheet_name).to_markdown()
        table_identifier = f"# Tabellenname: {sheet_name}"
        tables_strings.append(table_identifier)
        tables_strings.append(' '.join(sheet_string.split()))
    tables_strings_combined = "\n".join(tables_strings)
    return tables_strings_combined
