import os
import litellm
litellm.suppress_debug_info = True
litellm.drop_params = True
from qdrant_client import QdrantClient

from typing import Dict, Any, List

def execute(query: str, limit: int = 3) -> Dict[str, Any]:
    """
    Realiza búsqueda semántica en Qdrant.
    """
    qdrant_url = os.getenv("QDRANT_URL", ":memory:")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    emb_model = os.getenv("EMBEDDING_MODEL", "gemini/text-embedding-004")
    collection_name = "mykb"
    
    try:
        # Asegurar compatibilidad de claves para Gemini
        gen_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gen_key:
            os.environ["GOOGLE_API_KEY"] = gen_key
            os.environ["GEMINI_API_KEY"] = gen_key
        
        # 1. Generar Embedding de la consulta usando LiteLLM
        response = litellm.embedding(
            model=emb_model, 
            input=[query],
            api_key=gen_key
        )
        query_vector = response.data[0]['embedding']
        
        # 2. Conectar a Qdrant
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        # 3. Buscar
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        results = []
        for hit in search_result:
            results.append({
                "score": hit.score,
                "text": hit.payload.get("text"),
                "metadata": hit.payload.get("metadata")
            })
            
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        return {"error": f"Error en Qdrant Search: {str(e)}"}
