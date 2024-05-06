from flask import Flask, request, jsonify

import requests
import subprocess

from werkzeug.utils import secure_filename

import os
import shutil

from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.docstore.document import Document

app = Flask(__name__)
UPLOAD_FOLDER = 'pdf_db'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize components for handling and processing PDF documents.

embeddings = HuggingFaceEmbeddings(model_name='BAAI/bge-large-en-v1.5')
text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=20, length_function=len, is_separator_regex=False)
directory_path = '/home/azureuser/rag_boilerplate_api/pdf_db'

# Load PDFs from directory and prepare Chroma database if PDFs exist.
try:
    db.delete_collection()
    print("Collection deleted successfully.")
except Exception as e:
    print(f"An error occurred while deleting the collection: {str(e)}")
    print("Moving on...")

db = Chroma.from_documents([Document(page_content="", metadata = {'source': 'None', 'user': 'admin'})], embeddings, collection_name = 'main')


template = "Answer the question based only on the following context:\n{context}\n\nQuestion: {question}\n"
prompt = ChatPromptTemplate.from_template(template)
output_parser = StrOutputParser()

def answer_query(question, username, model):
    """Execute the retrieval and answering pipeline."""
    retriever = retriever = db.as_retriever(
        search_kwargs={'k': 10, 'filter': {'user': username}}
    )
    llm = Ollama(model=model)
    setup_and_retrieval = RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
    chain = setup_and_retrieval | prompt | llm | output_parser
    return chain.invoke(question)

def upload_pdf_documents(filepath, username):
    """Load and add PDF documents to the Chroma database."""
    file_name = os.path.basename(filepath)
    if file_name.lower().endswith('.pdf'):
        loader_temp = PyPDFLoader(filepath)  # Assuming PyPDFLoader is defined elsewhere
        # Assuming text_splitter is defined elsewhere or passed as an argument if needed
        docs_temp = loader_temp.load_and_split(text_splitter=text_splitter)

        for doc in docs_temp:
            # Replace newline characters with spaces
            doc.page_content = doc.page_content.replace('\n', ' ')

            # Check if 'metadata' exists and is a dictionary
            if not hasattr(doc, 'metadata'):
                doc.metadata = {}
            if not isinstance(doc.metadata, dict):
                doc.metadata = {}

            # Add or update the 'user' field in the metadata
            doc.metadata['user'] = username

        # Assuming db is defined and has a method add_documents
        db.add_documents(docs_temp)
    else:
        print(f"Skipping non-PDF file: {file_name}")

def delete_pdf(doc_path, username):

    data = db.get()
    filtered_ids = [
        data['ids'][i]
        for i in range(len(data['metadatas']))
        if data['metadatas'][i]['source'] == doc_path and data['metadatas'][i]['user'] == username
    ]
    db.delete(filtered_ids)

    return f'Given document: {doc_path} for the user: {username} deleted from the db'

def get_user_doc_paths(username):
    data = db.get()
    user_doc_paths = [
        data['metadatas'][i]['source']
        for i in range(len(data['metadatas']))
        if data['metadatas'][i]['user'] == username
    ]
    unique_doc_paths = list(set(user_doc_paths))

    return unique_doc_paths

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Endpoint to upload PDF files."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'No username provided'}), 400

    files = request.files.getlist('file')
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            upload_pdf_documents(file_path, username)
            saved_files.append(filename)

    if not saved_files:
        return jsonify({"error": "No valid PDF files uploaded"}), 400
    return jsonify({"message": "Files uploaded successfully", "filenames": saved_files}), 200

@app.route('/query', methods=['POST'])
def handle_query():
    """Endpoint to answer questions based on the uploaded PDFs."""
    data = request.json
    question = data.get('question')
    username = data.get('username')
    model = data.get('model')

    # Check if all required parameters are provided
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    if not username:
        return jsonify({'error': 'No username provided'}), 400
    if not model:
        return jsonify({'error': 'No model specified'}), 400

    try:
        answer = answer_query(question, username, model)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_pdfs', methods=['POST'])
def delete_pdfs():
    data = request.json
    doc_paths = data.get('doc_paths')
    username = data.get('username')

    if not doc_paths:
        return jsonify({'error': 'No document paths provided'}), 400
    if not username:
        return jsonify({'error': 'No username provided'}), 400
    if not isinstance(doc_paths, list):
        return jsonify({'error': 'Document paths should be a list'}), 400

    results = []
    for doc_path in doc_paths:
        result = delete_pdf(doc_path, username)
        results.append(result)

    return jsonify({'results': results}), 200

@app.route('/delete-all-pdfs', methods=['POST'])
def delete_all_pdfs():
    """Endpoint to delete all PDF files in the directory."""
    try:
        if not os.listdir(directory_path):
            return jsonify({"message": "Directory is already empty"}), 200

        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        # Reset the Chroma database since all files are deleted.
        global db
        db.delete_collection()
        db = Chroma.from_documents([Document(page_content="", metadata = {'source': 'None', 'user': 'admin'})], embeddings, collection_name = 'main')

        return jsonify({"message": "All files deleted successfully"}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to delete {filename}. Reason: {str(e)}'}), 500

@app.route('/check-model', methods=['POST'])
def check_model():
    data = request.json
    model_name = data.get('model_name')
    if not model_name:
        return jsonify({'error': 'No model name provided'}), 400

    try:
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_exists = any(model['name'] == model_name for model in models)
            if model_exists:
                return jsonify({'message': 'Model already loaded in Ollama Repository'}), 200
            else:
                # Attempt to pull the model if not found
                try:
                    subprocess.run(['ollama', 'pull', model_name], check=True)
                    return jsonify({'message': 'Model loaded successfully'}), 200
                except subprocess.CalledProcessError as e:
                    return jsonify({'error': 'Failed to load model'}), 500
        else:
            return jsonify({'error': 'Failed to retrieve model information'}), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500


@app.route('/user_doc_paths', methods=['GET'])
def user_doc_paths():
    username = request.args.get('username')

    if username is None:
        return jsonify({'error': 'Please provide a username.'}), 400

    try:
        unique_doc_paths = get_user_doc_paths(username)
        return jsonify({'doc_paths': unique_doc_paths}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)