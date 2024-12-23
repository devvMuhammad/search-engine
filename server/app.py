import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from server.entities.docindex import DocumentIndex
from server.functions.rank import calculate_bm25
from server.lib.utils import preprocess_text

app = Flask(__name__)
CORS(app)
@app.route('/search')
def search():
    totalStart= time.time()
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "No query provided"}), 400

        query_terms = preprocess_text(query)

        start = time.time()
        results, logs = calculate_bm25(query_terms.split(" "))
        end = time.time()
        print(f"BM25 calculation took {end - start:.4} seconds")

        formatted_results = []
        
        # Use context manager to handle CSV file lifecycle
        start = time.time()
        with DocumentIndex() as doc_index:
            # Get first 50 doc IDs
            doc_ids = [doc_id for doc_id, _ in results]
            # Get all documents in one go
            documents = doc_index.get_documents(doc_ids)
            
            # Format results
            for (doc_id, score), doc in zip(results, documents):
                if doc:
                    formatted_results.append({
                        "doc_id": doc_id,
                        "score": score, 
                        "title": doc['title'],
                        "abstract": doc['abstract'][0:500]+"...",
                        "keywords": doc['keywords'],
                        "year": doc['year'],
                        "venue": doc['venue'],
                        "citations": doc['n_citation'],
                        "url": doc['url']
                    })
        end = time.time()

        totalEnd = time.time()
        print(f"Document retrieval took {end - start:.4} seconds")

        print(f"Total time is {totalEnd - totalStart:.4} seconds")

        return jsonify({
            "results_count": len(results),
            "query": query_terms,
            "results": formatted_results 
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)