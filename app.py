import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import ollama
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from rag_utils import RAGSystem

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

# Initialize RAG System
rag_system = RAGSystem(
    embedding_model="all-MiniLM-L6-v2",
    chat_model="llama3",  
    ollama_host="http://localhost:11434"
)

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Save file temporarily
    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)
    
    # Process document
    try:
        rag_system.ingest_document(filepath)
        return jsonify({"message": "Document uploaded and indexed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query')
    language = data.get('language', 'english')
    
    try:
        # Retrieve relevant context
        context = rag_system.retrieve_context(query)
        
        # Generate response
        response = rag_system.generate_response(query, context, language)
        
        return jsonify({
            "response": response,
            "context": context
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000)
