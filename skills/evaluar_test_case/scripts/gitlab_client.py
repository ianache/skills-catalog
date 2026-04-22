
#!/usr/bin/env python3
"""
GitLab Issue Client for Test Case Evaluation

Este módulo permite conectarse a una instancia de GitLab y obtener
información de issues para evaluar especificaciones de casos de prueba.
"""

import os
import sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

log_format = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout) # Asegura que salgan por consola
    ]
)

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.error("Requests library is required. Install with: pip install requests")
    sys.exit(1)


@dataclass
class IssueInfo:
    """Dataclass para almacenar información de un issue de GitLab."""
    title: str
    description: str
    labels: List[str]
    state: str
    issue_id: int
    project_id: int
    author: str
    created_at: str
    updated_at: str
    url: str


class GitLabClient:
    """
    Cliente para interactuar con la API de GitLab.
    
    Attributes:
        base_url: URL base de la instancia de GitLab
        private_token: Token de acceso privado para autenticación
        session: Sesión HTTP para reutilizar conexiones
    """
    
    def __init__(self, base_url: str = "https://project.comsatel.com.pe", private_token: Optional[str] = None):
        """
        Inicializa el cliente de GitLab.
        
        Args:
            base_url: URL base de la instancia de GitLab
            private_token: Token de acceso privado. Si no se proporciona,
                          se busca en la variable de entorno GITLAB_TOKEN
        """
        self.base_url = base_url.rstrip('/')
        self.private_token = private_token or os.getenv('GITLAB_TOKEN')
        
        if not self.private_token:
            raise ValueError(
                "Se requiere un token de GitLab. "
                "Proporcione el parámetro private_token o configure la variable de entorno GITLAB_TOKEN"
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            'Private-Token': self.private_token,
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Realiza una petición GET a la API de GitLab.
        
        Args:
            endpoint: Endpoint de la API (sin la URL base)
            
        Returns:
            Dict con la respuesta JSON
            
        Raises:
            requests.exceptions.RequestException: Si hay error en la petición
        """
        url = f"{self.base_url}/api/v4{endpoint}"
        response = None
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response is not None:
                if response.status_code == 401:
                    raise requests.exceptions.HTTPError(
                        "Error de autenticación: Token inválido o expirado"
                    ) from e
                elif response.status_code == 404:
                    raise requests.exceptions.HTTPError(
                        f"Recurso no encontrado: {endpoint}"
                    ) from e
            raise
    
    def get_issue(self, project_id: int, issue_id: int) -> IssueInfo:
        """
        Obtiene la información de un issue específico.
        
        Args:
            project_id: ID del proyecto en GitLab
            issue_id: ID (iid) del issue dentro del proyecto
            
        Returns:
            IssueInfo con los datos del issue
            
        Raises:
            requests.exceptions.RequestException: Si hay error al obtener el issue
            ValueError: Si los parámetros son inválidos
        """
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError(f"project_id debe ser un entero positivo, got: {project_id}")
        
        if not isinstance(issue_id, int) or issue_id <= 0:
            raise ValueError(f"issue_id debe ser un entero positivo, got: {issue_id}")
        
        # GitLab API usa project_id con formato URL-encoded (reemplazar / por %2F)
        encoded_project_id = str(project_id).replace('/', '%2F')
        
        endpoint = f"/projects/{encoded_project_id}/issues/{issue_id}"
        
        try:
            data = self._make_request(endpoint)
            
            return IssueInfo(
                title=data.get('title', ''),
                description=data.get('description', ''),
                labels=data.get('labels', []),
                state=data.get('state', ''),
                issue_id=data.get('iid', issue_id),
                project_id=project_id,
                author=data.get('author', {}).get('name', ''),
                created_at=data.get('created_at', ''),
                updated_at=data.get('updated_at', ''),
                url=data.get('web_url', '')
            )
            
        except requests.exceptions.HTTPError as e:
            print(f"Error al obtener el issue {issue_id} del proyecto {project_id}: {e}")
            raise
    
    def get_issue_notes(self, project_id: int, issue_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los comentarios/notas de un issue.
        
        Args:
            project_id: ID del proyecto en GitLab
            issue_id: ID (iid) del issue dentro del proyecto
            
        Returns:
            Lista de notas/comentarios del issue
        """
        encoded_project_id = str(project_id).replace('/', '%2F')
        endpoint = f"/projects/{encoded_project_id}/issues/{issue_id}/notes"
        
        result = self._make_request(endpoint)
        if isinstance(result, list):
            return result
        return [result] if isinstance(result, dict) else []
    
    def close(self):
        """Cierra la sesión HTTP."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def format_issue_for_evaluation(issue: IssueInfo) -> str:
    """
    Formatea la información del issue para su evaluación.
    
    Args:
        issue: IssueInfo con los datos del issue
        
    Returns:
        String formateado con la información relevante
    """
    lines = [
        "=" * 60,
        f"ISSUE #{issue.issue_id} - {issue.title}",
        "=" * 60,
        f"Estado: {issue.state}",
        f"Autor: {issue.author}",
        f"Labels: {', '.join(issue.labels) if issue.labels else 'Ninguna'}",
        f"URL: {issue.url}",
        "-" * 60,
        "DESCRIPCIÓN:",
        "-" * 60,
        issue.description or "(Sin descripción)",
        "=" * 60,
    ]
    
    return "\n".join(lines)


# Ejemplo de uso
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Obtiene información de un issue de GitLab para evaluación de casos de prueba"
    )
    parser.add_argument(
        "--project-id",
        type=int,
        required=True,
        help="ID del proyecto en GitLab"
    )
    parser.add_argument(
        "--issue-id",
        type=int,
        required=True,
        help="ID del issue dentro del proyecto"
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Token de GitLab (opcional, también se puede usar GITLAB_TOKEN env var)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://project.comsatel.com.pe",
        help="URL base de GitLab"
    )
    
    args = parser.parse_args()
    client = None
    
    try:
        client = GitLabClient(
            base_url=args.url,
            private_token=args.token
        )
        
        print(f"\nConectando a {args.url}...")
        print(f"Obteniendo issue #{args.issue_id} del proyecto {args.project_id}...\n")
        
        issue = client.get_issue(args.project_id, args.issue_id)
        
        # Imprimir información formateada
        print(format_issue_for_evaluation(issue))
        
        # Retornar datos como JSON para uso programático
        import json
        print("\n" + "=" * 60)
        print("DATOS EN FORMATO JSON:")
        print("=" * 60)
        print(json.dumps({
            'title': issue.title,
            'description': issue.description,
            'labels': issue.labels,
            'state': issue.state,
            'author': issue.author,
            'url': issue.url
        }, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        if isinstance(client, GitLabClient):
            client.close()
