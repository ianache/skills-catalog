import os
import json
import uuid
import redis
from typing import Any, Dict, Union

class ArtifactManager:
    """
    Gestiona el almacenamiento de resultados pesados (Claim Check Pattern) en Redis.
    """
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.hash_name = "agent_artifacts"
        
        # Umbral configurable vía env (default 2048 bytes)
        self.threshold_bytes = int(os.getenv("CLAIM_CHECK_THRESHOLD_BYTES", 2048))
        
        self._redis_client = None

    @property
    def redis_client(self):
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    decode_responses=True
                )
            except Exception as e:
                print(f"[ArtifactManager] Error conectando a Redis: {e}")
        return self._redis_client

    def save_if_needed(self, tool_name: str, result: Any) -> Union[Any, str]:
        """
        Evalúa si el resultado debe guardarse en Redis (Claim Check).
        Si supera el umbral o es un artefacto explícito, devuelve una referencia.
        """
        # Si el resultado es un error o algo muy simple, no procesar
        if not result or isinstance(result, (int, float, bool)):
            return result

        # Convertir a JSON para medir tamaño real
        try:
            serialized = json.dumps(result)
        except Exception:
            serialized = str(result)

        size = len(serialized)
        is_explicit_artifact = isinstance(result, dict) and result.get("is_artifact") is True
        
        if size > self.threshold_bytes or is_explicit_artifact:
            # print(f"[ArtifactManager] Objeto pesado detectado ({size} bytes). Guardando en Redis...")
            return self._save_to_redis(tool_name, result)
        
        return result

    def _save_to_redis(self, tool_name: str, result: Any) -> str:
        """Guarda en Redis y devuelve la referencia textual."""
        artifact_id = str(uuid.uuid4())
        client = self.redis_client
        
        if not client:
            # Fallback si Redis no está disponible: devolver truncado con advertencia
            return f"[ERROR: Redis no disponible para Artifact. Contenido truncado]: {str(result)[:500]}..."

        try:
            # Guardar en el hashmap
            # El campo es el artifact_id, el valor es el JSON
            client.hset(self.hash_name, artifact_id, json.dumps({
                "origin_tool": tool_name,
                "timestamp": str(uuid.uuid1()), # Usando uuid1 para tener un ts semi-ordenado si se requiere
                "content": result
            }))
            
            ref = f"{self.hash_name}:{artifact_id}"
            return f"📚💎 Se ha generado un artefacto con referencia '{ref}'"
        except Exception as e:
            return f"[ERROR guardando artefacto: {e}]"
