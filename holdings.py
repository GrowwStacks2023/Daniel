import os
import json  
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from bs4 import BeautifulSoup

# Replace with your actual endpoint and API key
endpoint = "https://growwstacksdocumentreader.cognitiveservices.azure.com/"
api_key = "262c9eba736c409faa93659e5669cc58"

# Initialize DocumentAnalysisClient
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(api_key)
)

def extract_pdf_content(file_path):
    # Read the PDF file
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", document=f)

    # Get the result
    result = poller.result()

    # Extract the content in a structured way (tables, paragraphs, etc.)
    content = []
    tables_data = []
    for page in result.pages:
        page_content = []
        page_content.append(f"Page {page.page_number}:\n")

        # Extract paragraphs
        for line in page.lines:
            page_content.append(line.content)

        # Check if the word "Holdings" is present in the page
        if any("Holdings" in line.content for line in page.lines):
            content.append("\n".join(page_content))  # Save the entire page if "Holdings" is found

            # Extract tables
            if result.tables:
                for table in result.tables:
                    table_rows = []
                    for cell in table.cells:
                        row_index = cell.row_index
                        col_index = cell.column_index
                        
                        # Ensure the row list has enough space for this row
                        if len(table_rows) <= row_index:
                            table_rows.append([])

                        # Ensure each row has enough columns
                        while len(table_rows[row_index]) <= col_index:
                            table_rows[row_index].append(None)

                        # Insert the cell content at the right place
                        table_rows[row_index][col_index] = cell.content

                    # Append table data
                    tables_data.append({
                        'page_number': page.page_number,
                        'table': table_rows
                    })

    return "\n\n".join(content), tables_data  # Join all the pages with "Holdings" and return tables
structure_array = {header:"values" ,test:"Test" , col2:"col2"}

def save_to_text_file(content, output_file):
    # Save the extracted content to a text file
    with open(output_file, "w") as f:
        f.write(content)
    print(f"Content saved to {output_file}")

def save_to_json_file(tables_data, output_file):
    # Save the extracted tables data to a JSON file
    with open(output_file, "w") as f:
        json.dump(tables_data, f, indent=4)
    print(f"Tables data saved to {output_file}")

# Example usage
file_path = "sample-new-fidelity-acnt-stmt.pdf"
text_output_file = "holdings_content.txt"
json_output_file = "holdings_tables.json"

pdf_content, tables_data = extract_pdf_content(file_path)
if pdf_content:
    print("Extracted PDF Content:\n", pdf_content)
    # Save the content to a text file
    save_to_text_file(pdf_content, text_output_file)
    
    # Save the tables to a JSON file
    if tables_data:
        save_to_json_file(tables_data, json_output_file)
else:
    print("No content related to 'Holdings' was found.")


