# PDF Question Answering API

This is a Flask-based API that allows users to upload PDF documents, ask questions based on the uploaded PDFs, and retrieve answers. The API uses various components such as Ollama, HuggingFaceEmbeddings, and Chroma for handling and processing the PDF documents.

## Docker

Use this docker command to pull the latest image of this application

```docker run -d -p 5000:5000 --name my-ollama-app vardhanamdaga/ollama-flask-app:latest```

The flask-server will be up and running at `http://localhost:5000`

## Endpoints

### 1. `/upload-pdf` (POST)

This endpoint allows users to upload one or more PDF files. It expects the following parameters:
- `file` (file): The PDF file(s) to be uploaded.
- `username` (string): The username associated with the uploaded PDF(s).

The uploaded PDF(s) will be saved in the specified upload folder and added to the Chroma database. The endpoint returns a JSON response indicating the success or failure of the file upload along with the filenames of the successfully uploaded files.

### 2. `/query` (POST)

This endpoint allows users to ask questions based on the uploaded PDFs. It expects the following parameters in the JSON request body:
- `question` (string): The question to be answered.
- `username` (string): The username associated with the PDFs to be queried.
- `model` (string): The name of the Ollama model to be used for answering the question.

The endpoint executes the retrieval and answering pipeline using the specified model and returns the answer as a JSON response. If any required parameters are missing or an error occurs during the process, appropriate error messages are returned.

### 3. `/delete-all-pdfs` (POST)

This endpoint deletes all the PDF files in the specified directory. It does not require any parameters. If the directory is already empty, it returns a message indicating that the directory is empty. Otherwise, it deletes all the files and subdirectories in the specified directory and resets the Chroma database. The endpoint returns a JSON response indicating the success or failure of the deletion process.

### 4. `/delete_pdfs` (POST)

This endpoint allows users to delete specific PDF documents associated with a username. It expects the following parameters in the JSON request body:
- `doc_paths` (list): A list of document paths to be deleted.
- `username` (string): The username associated with the documents to be deleted.

The endpoint iterates over the provided document paths, deletes the corresponding documents from the Chroma database, and returns a JSON response with the deletion results for each document.

### 5. `/check-model` (POST)

This endpoint checks if a specified Ollama model is already loaded in the Ollama repository. It expects the following parameter in the JSON request body:
- `model_name` (string): The name of the model to be checked.

The endpoint sends a GET request to the Ollama repository API to retrieve the list of loaded models. If the specified model is found, it returns a message indicating that the model is already loaded. If the model is not found, it attempts to pull the model using the `ollama pull` command. If the model is successfully loaded, it returns a success message. Otherwise, it returns an error message.

### 6. `/user_doc_paths` (GET)

This endpoint retrieves the unique document paths associated with a specific username. It expects the following parameter as a query parameter:
- `username` (string): The username for which to retrieve the document paths.

The endpoint calls the `get_user_doc_paths` function with the provided username and returns a JSON response containing the unique document paths associated with that username. If the username is not provided or an error occurs during the process, appropriate error messages are returned.

## Setup and Usage

1. Make sure you have the required dependencies installed, including Flask, requests, subprocess, werkzeug, os, shutil, langchain_community, langchain_chroma, langchain_core, and langchain.

2. Set up the necessary configurations, such as the upload folder path and allowed file extensions, in the code.

3. Run the Flask application by executing the script.

4. Use the provided endpoints to upload PDFs, ask questions, delete PDFs, check models, and retrieve user document paths.

Note: Make sure to have the Ollama repository running and accessible at the specified URL (`http://localhost:11434`) for the `/check-model` endpoint to work correctly.