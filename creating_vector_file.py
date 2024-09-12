from flask import Flask, request, render_template_string, jsonify
import os
import time
import pickle
from werkzeug.utils import secure_filename
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

app = Flask(__name__)

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CSV Embedding Processor</title>
        </head>
        <body>
            <h1>Upload CSV and Process</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <label for="file">Select CSV file:</label>
                <input type="file" name="file" id="file" required><br><br>
                <label for="folder_name">Folder Name:</label>
                <input type="text" name="folder_name" id="folder_name" required><br><br>
                <input type="submit" value="Upload and Process">
            </form>
        </body>
        </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'folder_name' not in request.form:
        return jsonify({'error': 'File or folder name missing'}), 400
    
    file = request.files['file']
    folder_name = request.form['folder_name']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and folder_name:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process the CSV file
        folder_path = os.path.join(PROCESSED_FOLDER, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Try loading CSV and processing
        try:
            loader = CSVLoader(file_path, encoding="latin-1")
            documents = loader.load()

            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                return jsonify({'error': 'OpenAI API key not found'}), 500
            
            embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

            batch_size = 100
            if documents:
                first_batch = documents[:batch_size]
                vectorstore = FAISS.from_documents(first_batch, embeddings)

                for i in range(batch_size, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    vectorstore.add_documents(batch)
                    time.sleep(1)

                # Save the vectorstore to disk
                vectorstore.save_local(folder_path)

                pkl_file = os.path.join(folder_path, f"{folder_name}.pkl")

                # Save vectorstore object
                with open(pkl_file, 'wb') as f:
                    pickle.dump(vectorstore, f)

                return jsonify({'message': 'File processed and saved successfully'}), 200
            else:
                return jsonify({'error': 'No documents found in the CSV file'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid input'}), 400

if __name__ == '__main__':
    app.run(debug=True)
