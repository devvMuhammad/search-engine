import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from server.entities.docindex import DocumentIndex
from server.functions.rank import calculate_bm25
from server.entities.lexicon import Lexicon
from server.functions.autosuggest import Autosuggestion
from server.lib.utils import preprocess_text

lexicon = Lexicon().lexicon
words_list = list(lexicon.keys())
auto = Autosuggestion(words_list)

with DocumentIndex() as doc_index:

    app = Flask(__name__)
    CORS(app)

    @app.route('/search')
    def search():
        totalStart = time.time()
        try:
            query = request.args.get('q', '')
            if not query:
                return jsonify({"error": "No query provided"}), 400

            query_terms = preprocess_text(query)

            start = time.time()
            results, logs = calculate_bm25(query.split(" "), len(lexicon))
            end = time.time()
            print(f"BM25 calculation took {end - start:.4} seconds")

            formatted_results = []
            
            start = time.time()
            # Simply use the global instance directly
            doc_ids = [doc_id for doc_id, _ in results][:1000]
            documents = doc_index.get_documents(doc_ids)
            
            for (doc_id, score), doc in zip(results, documents):
                if doc:
                    formatted_results.append({
                        "doc_id": doc_id,
                        "score": score, 
                        "title": doc['title'],
                        "abstract": doc['abstract'],
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
                "results": formatted_results[:50]
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/typos')
    def suggest():
        try:
            query = request.args.get('q', '')
            if not query:
                return jsonify({"error": "No query provided"}), 400
            matches = process.extract(
                    query,
                    words_list,
                    scorer=fuzz.ratio,
                    limit=5,
                    score_cutoff=70
                )
            
            return jsonify({
                "matches": [word for word, _, _ in matches]
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/test')
    def test():
        return jsonify({"message": "Hello World!"}), 200

    @app.route('/autocomplete')
    def autocomplete():
        try:
            query = request.args.get('q', '')
            if not query:
                return jsonify({"error": "No query provided"}), 400
            
            query_terms=  query.split(" ")
            query_term = preprocess_text(query_terms[-1])
            print("this is the query term", query_term)

            if(query_term == ""):
                return jsonify({
                    "suggestions": []
                }), 200

            suggestions = auto.suggest(query_term)
            print(query_term, suggestions)
            # print(query_terms)
            if(len(query_terms) == 1):
                return jsonify({
                    "suggestions": suggestions
                }), 200
            print("hahaahahah")
            # join each suggestion with the remaining query terms and return
            suggestions = [" ".join(query_terms[:-1] + [suggestion]) for suggestion in suggestions]
            print(suggestions)
            return jsonify({
                "suggestions": suggestions
            }), 200
        except Exception as e:
            print(e)
            return jsonify({"error": str(e)}), 500

    if __name__ == '__main__':
        app.run(debug=True, port=5000)