from flask import Flask, request, render_template_string
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
import openai
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import frameworks as frame

app = Flask(__name__)

openai_api_key = "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"


csv_files = [
    {"name": "SCF", "pkl": "/home/vyavasthapak/Daniel/SCF/", "faiss": "/home/vyavasthapak/Daniel/SCF/"},
    {"name": "NIST1", "pkl": "/home/vyavasthapak/Daniel/NIST1/", "faiss": "/home/vyavasthapak/Daniel/NIST1/"},
    {"name": "NISTSMB", "pkl": "/home/vyavasthapak/Daniel/NISTSMB/", "faiss": "/home/vyavasthapak/Daniel/NISTSMB/"},
    {"name": "SMB", "pkl": "/home/vyavasthapak/Daniel/SMB/", "faiss": "/home/vyavasthapak/Daniel/SMB/"}
]

def load_vector_store(pkl_path, faiss_path):
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    try:
        vectorstore = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise
    except Exception as e:
        print(f"Error loading FAISS vector store: {e}")
        raise
    return vectorstore

vectorstores = [load_vector_store(f['pkl'], f['faiss']) for f in csv_files]

llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
chain = load_qa_chain(llm, chain_type="stuff")

prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
{context}
Question: {question}"""
PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

chat_history = []

def reformat_response(response):
    openai.api_key = openai_api_key
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Reformat the following text into JSON format with each SCF control as a separate JSON object containing 'SCF', 'Methods', and 'Description'."
                },
                {
                    "role": "user",
                    "content": response
                }
            ]
        )
        formatted_text = completion.choices[0].message['content']
        formatted_json = json.loads(formatted_text)
        return json.dumps(formatted_json, indent=4)

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return json.dumps({"error": "An error occurred while formatting the response."}, indent=4)


    
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_question = request.form["question"]
        selected_vectors = request.form.getlist("vector_spaces")

        output_texts = []
        for vectorstore_index in selected_vectors:
            vectorstore = vectorstores[int(vectorstore_index)]
            docs = vectorstore.similarity_search(user_question)
            response = chain.run(input_documents=docs, question=user_question, prompt=PROMPT)
            formatted_response = reformat_response(response)
            output_texts.append(formatted_response)

        chat_history.append(("User", user_question))
        chat_history.append(("Bot", "\n\n".join(output_texts)))

    chat_html = ""
    for speaker, message in chat_history:
        chat_html += f"<p><strong>{speaker}:</strong> <pre>{message}</pre></p>"

    return render_template_string(f'''
        <!doctype html>
        <html>
        <head>
            <title>Cyber Security AI</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #f7f7f8;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                }}
                .container {{
                    width: 80%;
                    max-width: 900px;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    text-align: center;
                    color: #333333;
                }}
                .chat-box {{
                    background-color: #eaeaea;
                    padding: 15px;
                    border-radius: 10px;
                    max-height: 400px;
                    overflow-y: scroll;
                    margin-bottom: 20px;
                }}
                .chat-message {{
                    margin-bottom: 15px;
                    display: flex;
                    justify-content: space-between;
                }}
                .user-message {{
                    text-align: right;
                }}
                .bot-message {{
                    text-align: left;
                }}
                .user-message pre, .bot-message pre {{
                    background-color: #f2f2f2;
                    padding: 10px;
                    border-radius: 5px;
                    max-width: 80%;
                    word-wrap: break-word;
                }}
                .bot-message pre {{
                    background-color: #e2f7e1;
                }}
                form {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}
                input[type="text"] {{
                    width: 100%;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ccc;
                    margin-bottom: 20px;
                }}
                button {{
                    background-color: #008cba;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }}
                button:hover {{
                    background-color: #005f5f;
                }}
                .checkbox-group {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    margin-bottom: 20px;
                }}
                .checkbox-group label {{
                    margin-right: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Cyber Security AI</h1>
                <div class="chat-box">
                    {chat_html}
                </div>
                <form method="post">
                    <div class="checkbox-group">
                        {''.join([f'<label><input type="checkbox" name="vector_spaces" value="{i}"> {csv["name"]}</label>' for i, csv in enumerate(csv_files)])}
                    </div>
                    <input type="text" name="question" placeholder="Type your question here..." required>
                    <button type="submit">Send</button>
                </form>
            </div>
        </body>
        </html>
    ''')

if __name__ == "__main__":
    app.run(debug=True)
