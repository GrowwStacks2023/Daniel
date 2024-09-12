import os
import json
import pandas as pd
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

endpoint = "https://growwstacksdocumentreader.cognitiveservices.azure.com/"
api_key = "262c9eba736c409faa93659e5669cc58"


expected_headers = [
    "Description",
    "Maturity",
    "Quantity",
    "Price Per Unit",
    "Ending Market Value Accrued Interest (AI)",
    "Total Cost Basis",
    "Unrealized Gain/Loss",
    "Est. Annual Income (EAI)",
    "Coupon Rate"
]


document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(api_key)
)

def extract_all_pdf_content(file_path):

    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", document=f)

    result = poller.result()

    content = []
    tables_data = []
    
    for page in result.pages:
        page_content = []
        page_content.append(f"Page {page.page_number}:\n")

        for line in page.lines:
            page_content.append(line.content)

        if result.tables:
            for table in result.tables:
                table_rows = []
                for cell in table.cells:
                    row_index = cell.row_index
                    col_index = cell.column_index
                    
                 
                    if len(table_rows) <= row_index:
                        table_rows.append([])

                  
                    while len(table_rows[row_index]) <= col_index:
                        table_rows[row_index].append(None)

                 
                    table_rows[row_index][col_index] = cell.content

                tables_data.append({
                    'page_number': page.page_number,
                    'table': table_rows
                })

    return tables_data  # Return all tables

def save_to_json_file(data, output_file):
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {output_file}")

def parse_json_for_holdings(json_file, output_file):
  
    with open(json_file, "r") as f:
        data = json.load(f)

   
    holdings_tables = []
    for table_info in data:
        
        if table_info['table']:
            headers = table_info['table'][0]  
            if set(expected_headers).issubset(set(headers)):
                holdings_tables.append(table_info)

   
    save_to_json_file(holdings_tables, output_file)

# Example usage
file_path = "sample-new-fidelity-acnt-stmt.pdf"
all_pages_json = "all_pages_content.json"
holdings_json_output = "holdings_tables.json"

# Step 1: Extract all content and save to JSON
tables_data = extract_all_pdf_content(file_path)
save_to_json_file(tables_data, all_pages_json)

# Step 2: Parse the JSON to filter out Holdings tables and save to new JSON
parse_json_for_holdings(all_pages_json, holdings_json_output)
