import os
import json
import litellm
from dotenv import load_dotenv
from skill_loader import load_skills
from tool_executor import ToolExecutor
from typing import List, Dict, Any

# Cargar .env sin sobrescribir variables ya definidas en el entorno
load_dotenv(override=False)

# Deshabilitar telemetría de litellm si se desea
os.environ["LITELLM_LOG"] = "INFO"

class SkillAgent:
    def __init__(self, skills_dir: str = None, model: str = None, provider: str = None):
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
        
        self.history = [{"role": "system", "content": self.system_prompt}]

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
        
        while True:
            # call LiteLLM completion
            response = litellm.completion(
                model=self.model,
                messages=self.history,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None
            )
            
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
                    
                    print(f"🎓 Usando skill {skill_name}")
                    print(f"\t🛠️ {tool_name}")
                    # print(f"Tool Call: {tool_name}({args})") # Opcional: mantener para debug o remover
                    
                    try:
                        result = self.executor.execute(tool_name, args)
                        print(f"Tool Result: {result}")
                        
                        # Add tool response to history
                        self.history.append({
                            "role": "tool",
                            "name": tool_name,
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {e}")
                        self.history.append({
                            "role": "tool",
                            "name": tool_name,
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"error": str(e)})
                        })
            else:
                final_text = message.content
                print(f"Assistant: {final_text}")
                return final_text

def main():
    # Verificar API Key (dependiendo del provider)
    # LiteLLM las toma de las variables de entorno estándar si existen
    
    agent = SkillAgent()
    
    print(f"Agente iniciado con LiteLLM usando: {agent.model}")
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
                # Recargar .env permitiendo sobrescribir las variables actuales
                load_dotenv(override=True)
                # Re-instanciar el agente para refrescar skills y parámetros
                agent = SkillAgent()
                print(f"Recarga completada. Modelo actual: {agent.model}")
                continue
                
            if user_input.lower() == "/settings":
                print("\n--- Configuración Actual ---")
                print(f"Proveedor: {agent.provider}")
                print(f"Modelo: {agent.raw_model}")
                print(f"Modelo LiteLLM: {agent.model}")
                print(f"Directorio de Skills: {agent.skills_dir}")
                print(f"Skills cargados: {', '.join([s.name for s in agent.skills])}")
                
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
                print("  exit | quit   - Sale de la aplicación.")
                print("------------------------------------\n")
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
