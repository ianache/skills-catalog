import os
import uuid
import litellm
litellm.suppress_debug_info = True
litellm.drop_params = True
from qdrant_client import QdrantClient

from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import Dict, Any

def execute(text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Genera embeddings e indexa un documento en Qdrant.
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

        # 1. Generar Embedding usando LiteLLM
        response = litellm.embedding(
            model=emb_model, 
            input=[text],
            api_key=gen_key
        )
        vector = response.data[0]['embedding']
        vector_size = len(vector)
        
        # 2. Conectar a Qdrant
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        # 3. Asegurar que la colección existe y está correctamente configurada
        try:
            client.get_collection(collection_name)
        except Exception:
            # Si falla, asumimos que no existe y la creamos
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            # Opcional: Crear índices de carga útil (payload) para búsqueda más rápida en metadatos
            # client.create_payload_index(collection_name, "metadata.id_proyecto", "keyword")
        
        # 4. Upsert el punto
        point_id = str(uuid.uuid4())
        client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": text,
                        "metadata": metadata or {}
                    }
                )
            ]
        )
        
        return {
            "status": "success",
            "message": f"Documento indexado en '{collection_name}'",
            "id": point_id,
            "vector_size": vector_size
        }
        
    except Exception as e:
        return {"error": f"Error en Qdrant Upsert: {str(e)}"}
