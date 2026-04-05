import os
import json
import uuid
import litellm
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import Dict, Any

def execute(text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Genera embeddings e indexa un documento en Qdrant.
    """
    qdrant_url = os.getenv("QDRANT_URL", ":memory:")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    emb_model = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
    collection_name = "mykb"
    
    try:
        # 1. Generar Embedding usando LiteLLM
        response = litellm.embedding(model=emb_model, input=[text])
        vector = response.data[0]['embedding']
        vector_size = len(vector)
        
        # 2. Conectar a Qdrant
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        # 3. Asegurar que la colección existe
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        
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
