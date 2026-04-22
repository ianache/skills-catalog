import os
import json
import litellm
import redis
import warnings
warnings.filterwarnings("ignore") # Suprimir warnings de pydantic/litellm

from dotenv import load_dotenv
from skill_loader import load_skills
from tool_executor import ToolExecutor
from event_interceptor import EventInterceptor
from typing import List, Dict, Any

# Guardar captura del entorno inicial para respetar variables del shell
initial_env = os.environ.copy()

# Cargar .env sin sobrescribir variables ya definidas en el entorno
load_dotenv(override=False)

# Configurar logs de litellm
os.environ["LITELLM_LOG"] = "INFO"

# litellm._turn_on_debug()

class SkillAgent:
    def __init__(self, skills_dir: str = None, model: str = None, provider: str = None, tenant_id: str = None, session_id: str = None):
        self.skills_dir = skills_dir or os.getenv("SKILLS_DIR", "skills")
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self.raw_model = model or os.getenv("LLM_MODEL", "gemini-2.0-flash")
        
        # LiteLLM model string format: provider/model_name
        # Priorizar el provider especificado si el raw_model no lo incluye ya
        if self.raw_model.startswith(f"{self.provider}/"):
            self.model = self.raw_model
        else:
            self.model = f"{self.provider}/{self.raw_model}"
        
        self.skills = load_skills(self.skills_dir)
        self.executor = ToolExecutor(self.skills)
        
        # Build system prompt from skill instructions
        self.system_prompt = "Eres un asistente inteligente altamente capaz. "
        for skill in self.skills:
            if skill.instructions:
                # Resolver referencias tipo @skill/folder/file en las instrucciones
                instructions = self._resolve_references(skill.instructions)
                self.system_prompt += f"\n\nInstrucciones para el skill '{skill.name}':\n{instructions}"
        
        self.system_prompt += "\n\nREGLAS DE ARTEFACTOS (CLAIM CHECK):"
        self.system_prompt += "\n1. Si el resultado de una herramienta indica que se ha generado un artefacto (ej: 📚💎 Se ha generado un artefacto con referencia 'agent_artifacts:uuid'), NO intentes adivinar el contenido."
        self.system_prompt += "\n2. Si necesitas la información de ese artefacto para responder, utiliza SIEMPRE la herramienta 'read_artifact' pasando el ID extraído de la referencia."
        self.system_prompt += "\n3. Cuando respondas al usuario sobre un artefacto, incluye siempre la frase exacta: 📚💎 Se ha generado un artefacto con referencia 'agent_artifacts:uuid'."
        
        # Prepare tools in OpenAI format (standard for LiteLLM)
        self.tools = []
        for skill in self.skills:
            for tool in skill.tools:
                self.tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"]
                    }
                })
        
        # DEBUG: Guardar el prompt final para auditoría
        try:
            with open("debug_system_prompt.txt", "w", encoding="utf-8") as f:
                f.write(self.system_prompt)
        except:
            pass
            
        self.history = [{"role": "system", "content": self.system_prompt}]
        
        # Inicializar el interceptor de eventos (middleware)
        self.interceptor = EventInterceptor(tenant_id=tenant_id, session_id=session_id)

    def _resolve_references(self, text: str) -> str:
        import re
        from pathlib import Path
        
        # Patrón para encontrar @skill/folder/file
        # Ej: @especificar_user_story/assets/template.md
        pattern = r'@([\w-]+)/([\w-]+)/([\w.-]+)'
        
        def replace_match(match):
            skill_name, folder, filename = match.groups()
            # Construir ruta relativa al directorio de skills
            file_path = Path(self.skills_dir) / skill_name / folder / filename
            
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    return f"\n--- Contenido de {skill_name}/{folder}/{filename} ---\n{content}\n--- Fin de {filename} ---\n"
                except Exception as e:
                    return f"[Error cargando {file_path}: {e}]"
            else:
                return f"[Archivo {file_path} no encontrado]"
        
        return re.sub(pattern, replace_match, text)

    def process_message(self, user_message: str):
        print(f"User: {user_message}")
        self.history.append({"role": "user", "content": user_message})
        
        self.interceptor.emit(f"Procesando mensaje del usuario: {user_message[:50]}", "RUNNING")
        print(f"🔄 Iniciando ciclo de procesamiento...", flush=True)
        
        while True:
            self.interceptor.emit("Generando paso de razonamiento", "RUNNING")
            print("👤+💭 Analizando y razonando...", flush=True)
            
            # call LiteLLM completion with automatic retries
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=self.history,
                    tools=self.tools if self.tools else None,
                    tool_choice="auto" if self.tools else None,
                    num_retries=3
                )
                self.interceptor.emit("Razonamiento completado", "SUCCESS")
                # print("✅ Razonamiento listo", flush=True)
            except Exception as e:
                self.interceptor.emit(f"Error en razonamiento LLM: {str(e)}", "ERROR")
                raise e
            
            message = response.choices[0].message
            self.history.append(message)
            
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    tool_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    # Encontrar a qué skill pertenece la herramienta
                    skill_name = "Desconocido"
                    for skill in self.skills:
                        if any(t["name"] == tool_name for t in skill.tools):
                            skill_name = skill.name
                            break
                    
                    # Log interno vía interceptor (sin salida a consola)
                    self.interceptor.emit(f"Invocando herramienta {tool_name} (Skill: {skill_name})", "RUNNING")
                    
                    print(f"🎓 Usando skill {skill_name}", flush=True)
                    print(f"\t🛠️ {tool_name}", flush=True)
                    
                    try:
                        result = self.executor.execute(tool_name, args)
                        # print(f"Tool Result: {result}", flush=True) # Silenciado para terminal limpia
                        
                        self.interceptor.emit(f"Herramienta {tool_name} ejecutada con éxito", "SUCCESS")
                        print(f"✅ Herramienta {tool_name} completada con éxito.", flush=True)
                        
                        # Add tool response to history
                        self.history.append({
                            "role": "tool",
                            "name": tool_name,
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {e}", flush=True)
                        self.interceptor.emit(f"Error en herramienta {tool_name}: {str(e)}", "ERROR")
                        self.history.append({
                            "role": "tool",
                            "name": tool_name,
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"error": str(e)})
                        })
            else:
                final_text = message.content
                
                # Patrón Claim Check para la respuesta del asistente (si es muy larga)
                final_text = self.executor.artifact_manager.save_if_needed("assistant_response", final_text)
                
                print(f"Assistant: {final_text}", flush=True)
                self.interceptor.emit("Respuesta final generada y enviada al usuario", "SUCCESS")
                return final_text

def main():
    # Verificar API Key (dependiendo del provider)
    # LiteLLM las toma de las variables de entorno estándar si existen
    
    agent = SkillAgent(
        tenant_id=os.getenv("TENANT_ID"),
        session_id=os.getenv("SESSION_ID")
    )
    
    print(f"Agente iniciado con LiteLLM usando: {agent.model}")
    print(f"Skills cargados: {len(agent.skills)} | Herramientas disponibles: {len(agent.tools)}")
    print("Escriba su consulta, '/help' para ver comandos, o 'exit' para salir.")
    
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                break
                
            if user_input.lower() == "/reload":
                print("Recargando configuración y skills...")
                
                # Cargar .env manualmente para poder filtrar valores
                from tqdm import tqdm # No necesaria, solo por consistencia de imports si hubiera
                from dotenv import dotenv_values
                
                new_env = dotenv_values(".env")
                for key, value in new_env.items():
                    # No sobrescribir si el nuevo valor es un placeholder o está vacío
                    # y ya tenemos algo útil en el entorno.
                    placeholders = ["changeme", "your_token_here", ""]
                    current_val = os.environ.get(key, "")
                    
                    if value and value not in placeholders:
                        os.environ[key] = value
                    elif not current_val or current_val in placeholders:
                        # Si no tenemos nada útil, aceptamos lo que venga (aunque sea placeholder)
                        if value:
                            os.environ[key] = value

                # Re-instanciar el agente para refrescar skills y parámetros
                agent = SkillAgent(
                    tenant_id=os.getenv("TENANT_ID"),
                    session_id=os.getenv("SESSION_ID")
                )
                print(f"Recarga completada. Proveedor: {agent.provider} | Modelo: {agent.model}")
                continue
                
            if user_input.lower() == "/settings":
                print("\n--- Configuración Actual ---")
                print(f"Proveedor: {agent.provider}")
                print(f"Modelo: {agent.raw_model}")
                print(f"Modelo LiteLLM: {agent.model}")
                print(f"Directorio de Skills: {agent.skills_dir}")
                print(f"Skills cargados: {', '.join([s.name for s in agent.skills])}")
                print(f"Base de Conocimientos (Qdrant): {os.getenv('QDRANT_URL', ':memory:')}")
                print(f"Modelo de Embedding: {os.getenv('EMBEDDING_MODEL', 'n/a')}")
                
                # Opcional: mostrar qué API keys están presentes (enmascaradas)
                keys_to_check = ["GEMINI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
                print("API Keys detectadas:")
                for key in keys_to_check:
                    val = os.getenv(key)
                    status = "Configurada" if val else "No configurada"
                    masked = f"{val[:4]}...{val[-4:]}" if val and len(val) > 8 else "****" if val else "N/A"
                    print(f"  {key}: {status} ({masked})")
                print("---------------------------\n")
                continue

            if user_input.lower() in ["/skill", "/skills"]:
                print("\n--- Skills y Herramientas ---")
                for skill in agent.skills:
                    print(f"\nSkill: {skill.name}")
                    if skill.tools:
                        for tool in skill.tools:
                            print(f"  - Herramienta: {tool['name']}")
                            print(f"    Descripción: {tool['description']}")
                    else:
                        print("  (Sin herramientas)")
                print("-----------------------------\n")
                continue

            if user_input.lower() == "/confidential":
                print("\n--- Información Confidencial ---")
                provider = agent.provider.lower()
                key_map = {
                    "gemini": "GEMINI_API_KEY",
                    "groq": "GROQ_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY"
                }
                key_env = key_map.get(provider)
                if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
                    key_env = "GOOGLE_API_KEY"
                
                val = os.getenv(key_env) if key_env else None
                
                if val:
                    # Enmascaramiento: Mostrar 5 primeros y 5 últimos
                    if len(val) > 10:
                        masked = f"{val[:5]}{'*' * (len(val)-10)}{val[-5:]}"
                    else:
                        masked = f"{val[:2]}...{val[-2:]}" if len(val) > 4 else "****"
                    
                    print(f"Proveedor Actual: {provider}")
                    print(f"Variable de Entorno: {key_env}")
                    print(f"Valor Detectado: {masked} (Largo: {len(val)})")
                else:
                    print(f"Error: No se encontró valor para la key del proveedor '{provider}'")
                    print(f"Intenté con: {key_env}")
                print("--------------------------------\n")
                continue

            if user_input.lower() == "/help":
                print("\n--- Comandos Rápidos Disponibles ---")
                print("  /help         - Muestra esta lista de ayuda.")
                print("  /reload       - Recarga la configuración (.env) y los skills.")
                print("  /settings     - Muestra la configuración actual y estado de API Keys.")
                print("  /skill(s)     - Lista todos los skills y sus herramientas disponibles.")
                print("  /confidential - Muestra la API Key enmascarada del proveedor actual.")
                print("  /history      - Muestra el historial de la conversación actual.")
                print("  /clear        - Limpia el historial de la conversación.")
                print("  /redis [st] [l]- Explora el stream [st] de Redis con límite [l].")
                print("  /artifacts [ID|clear]- Explora, recupera o limpia artefactos.")
                print("  exit | quit   - Sale de la aplicación.")
                print("------------------------------------\n")
                continue

            if user_input.lower().startswith("/redis"):
                parts = user_input.split()
                stream = parts[1] if len(parts) > 1 else os.getenv("REDIS_STREAM_NAME", "agent_events")
                try:
                    limit = int(parts[2]) if len(parts) > 2 else 10
                except ValueError:
                    limit = 10
                
                print(f"\n--- Explorando Redis Stream: {stream} (Límite: {limit}) ---")
                try:
                    r = redis.Redis(
                        host=os.getenv("REDIS_HOST", "localhost"),
                        port=int(os.getenv("REDIS_PORT", 6379)),
                        password=os.getenv("REDIS_PASSWORD"),
                        decode_responses=True
                    )
                    # Leer eventos en orden inverso para ver los más recientes primero
                    events = r.xrevrange(stream, count=limit)
                    if not events:
                        print("No se encontraron eventos en el stream.")
                    for event_id, data in events:
                        ts = data.get("timestamp", "N/A")
                        # Acortar timestamp si es ISO largo
                        ts_short = ts.split(".")[0].replace("T", " ") if "T" in ts else ts
                        status = data.get("status", "N/A")
                        desc = data.get("step_description", "N/A")
                        tenant = data.get("tenant_id", "N/A")
                        print(f"[{ts_short}] [{status}] {tenant}: {desc}")
                except Exception as e:
                    print(f"Error consultando Redis: {e}")
                print("-------------------------------------------\n")
                continue

            if user_input.lower().startswith("/artifacts"):
                parts = user_input.split()
                target_id = parts[1] if len(parts) > 1 else None
                hash_name = "agent_artifacts"
                
                try:
                    r = redis.Redis(
                        host=os.getenv("REDIS_HOST", "localhost"),
                        port=int(os.getenv("REDIS_PORT", 6379)),
                        password=os.getenv("REDIS_PASSWORD"),
                        decode_responses=True
                    )
                    
                    if target_id == "clear":
                        r.delete(hash_name)
                        print(f"Almacenamiento de artefactos '{hash_name}' limpiado correctamente.")
                    elif not target_id:
                        print(f"\n--- Listado de Artefactos (Hash: {hash_name}) ---")
                        keys = r.hkeys(hash_name)
                        if not keys:
                            print("No se encontraron artefactos guardados.")
                        else:
                            for k in keys:
                                raw_data = r.hget(hash_name, k)
                                try:
                                    data = json.loads(raw_data)
                                    tool = data.get("origin_tool", "unknown")
                                    ts = data.get("timestamp", "N/A").split("-")[0] # Simplificar UUID/TS
                                    print(f"  ID: {k} | Herramienta: {tool} | Ref: {ts}")
                                except:
                                    print(f"  ID: {k} (Error parseando metadatos)")
                        print("Usa '/artifacts [id]' para ver el contenido completo.")
                    else:
                        print(f"\n--- Contenido del Artefacto: {target_id} ---")
                        raw_data = r.hget(hash_name, target_id)
                        if not raw_data:
                            print(f"Error: Artefacto {target_id} no encontrado.")
                        else:
                            try:
                                data = json.loads(raw_data)
                                # Mostrar contenido de forma bonita
                                print(json.dumps(data.get("content", data), indent=2, ensure_ascii=False))
                            except:
                                print(raw_data)
                except Exception as e:
                    print(f"Error consultando artefactos en Redis: {e}")
                print("----------------------------------------------\n")
                continue

            if user_input.lower() == "/history":
                print("\n--- Historial de Conversación ---")
                for msg in agent.history:
                    role = msg.get("role", "unknown")
                    if role == "system": continue # Omitir prompt de sistema por brevedad
                    content = msg.get("content", "")
                    if msg.get("tool_calls"):
                        content = f"[Tool Calls: {len(msg['tool_calls'])}]"
                    print(f"[{role.upper()}]: {content[:100]}{'...' if len(str(content))>100 else ''}")
                print("---------------------------------\n")
                continue

            if user_input.lower() == "/clear":
                agent.history = [{"role": "system", "content": agent.system_prompt}]
                print("Historial de conversación limpiado.")
                continue
                
            agent.process_message(user_input)
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
