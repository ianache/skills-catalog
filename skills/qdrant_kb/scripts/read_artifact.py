import os
import json
import redis
from typing import Dict, Any

def execute(artifact_id: str) -> Any:
    """
    Recupera el contenido de un artefacto desde Redis.
    """
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD", None)
    hash_name = "agent_artifacts"
    
    try:
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True
        )
        
        raw_data = r.hget(hash_name, artifact_id)
        if not raw_data:
            return {"error": f"Artefacto {artifact_id} no encontrado en el hash '{hash_name}'."}
        
        data = json.loads(raw_data)
        # Devolver solo el contenido original para que el agente pueda razonar sobre él
        return data.get("content", data)
    
    except Exception as e:
        return {"error": f"Error recuperando artefacto de Redis: {str(e)}"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            args = json.loads(sys.argv[1])
            print(json.dumps(execute(**args)))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
