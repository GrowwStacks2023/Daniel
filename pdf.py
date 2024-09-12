from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential
import json

# Replace these with your actual endpoint and API key
endpoint = "https://growwstacksdocumentreader.cognitiveservices.azure.com/"
api_key = "262c9eba736c409faa93659e5669cc58"

# Initialize the Form Recognizer client
client = FormRecognizerClient(endpoint, AzureKeyCredential(api_key))

def analyze_document(file_path):
    # Open the PDF file
    with open(file_path, "rb") as f:
        # Use the method to recognize content
        poller = client.begin_recognize_content(form=f)
        result = poller.result()

    # Convert results to structured JSON
    structured_result = {
        "documentType": "General",
        "pages": []
    }

    for page_result in result:
        page_data = {
            "pageNumber": page_result.page_number,
            "lines": [
                {
                    "text": line.text,
                    "boundingBox": line.bounding_box
                }
                for line in page_result.lines
            ],
            "tables": [
                {
                    "rows": [
                        [
                            cell.text for cell in row.cells
                        ]
                        for row in table.rows
                    ]
                }
                for table in page_result.tables
            ]
        }
        structured_result["pages"].append(page_data)

    return structured_result

# Path to your PDF file
file_path = "sample-new-fidelity-acnt-stmt.pdf"

# Analyze the document
result = analyze_document(file_path)

# Path to the output JSON file
output_file_path = "result.json"

# Save the structured JSON result to a file
with open(output_file_path, "w") as json_file:
    json.dump(result, json_file, indent=4)

