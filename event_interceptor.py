import os
import json
import threading
import queue
from datetime import datetime
import redis

class EventInterceptor:
    """
    Middleware para interceptar eventos del agente y emitirlos a Redis Streams de forma asíncrona.
    """
    def __init__(self, tenant_id=None, session_id=None):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.stream_name = os.getenv("REDIS_STREAM_NAME", "agent_events")
        
        # Identificadores obligatorios segun requerimiento
        self.tenant_id = tenant_id or os.getenv("TENANT_ID", "default_tenant")
        self.session_id = session_id or os.getenv("SESSION_ID", "default_session")
        
        self.event_queue = queue.Queue()
        self.redis_client = None
        self._stop_event = threading.Event()
        
        # Iniciar hilo de envío en segundo plano para no penalizar latencia
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _get_client(self):
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host=self.host, 
                    port=self.port, 
                    password=self.password,
                    decode_responses=True
                )
                # Test connection (opcional)
                self.redis_client.ping()
            except Exception as e:
                print(f"[EventInterceptor] Error conectando a Redis en {self.host}:{self.port}: {e}")
                self.redis_client = None
        return self.redis_client

    def _worker(self):
        """Loop de fondo que consume la cola y envía a Redis."""
        while not self._stop_event.is_set():
            try:
                # Bloquear hasta 1 segundo esperando eventos
                event_data = self.event_queue.get(timeout=1.0)
                client = self._get_client()
                if client:
                    # Enviar a Redis Stream
                    client.xadd(self.stream_name, event_data)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[EventInterceptor] Error enviando evento a Redis Stream '{self.stream_name}': {e}")

    def emit(self, step_description: str, status: str = "RUNNING"):
        """Encola un evento para su envío asíncrono."""
        event = {
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "step_description": step_description,
            "timestamp": datetime.now().isoformat(),
            "status": status
        }
        self.event_queue.put(event)

    def stop(self):
        """Detiene el interceptor de forma segura."""
        self._stop_event.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
