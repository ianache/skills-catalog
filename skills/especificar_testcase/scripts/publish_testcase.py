"""Publish a test case to GitLab."""

import sys
import os
import json  
import gitlab
from typing import Dict, Any
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

def execute(project_id: int, specification: str) -> Dict[str, Any]:
    """Publish a test case to GitLab.

    Args:
        project_id: Project identifier
        specification: Test case specification

    Returns:
        Dictionary with status and issue link
    """
    logger.info(f"Publishing test case to project {project_id}")

    url = os.getenv('GITLAB_URL', 'https://project.comsatel.com.pe')
    token = os.getenv("GITLAB_TOKEN")
    
    if not token:
        logger.error("GITLAB_TOKEN not configured in environment")
        return {"status": "error", "message": "GITLAB_TOKEN no configurado en el entorno (.env)"}

    try:
        # Use python-gitlab for creation as in write_userstory.py
        import gitlab
        gl = gitlab.Gitlab(url=url, private_token=token)
        gl.auth()
        
        project = gl.projects.get(project_id)
        
        # Extract title from the first line or use a default
        title = specification.split('\n')[0].strip() if specification else "Nuevo Caso de Prueba"
        if len(title) > 60:
            title = title[:57] + "..."
        if not title:
            title = "Especificación de Caso de Prueba"
            
        issue = project.issues.create({
            'title': title,
            'description': specification,
            'labels': ['testcase']
        })
        
        logger.info(f"Successfully created test case issue #{issue.iid}")
        
        return {
            "status": "success",
            "action": "create",
            "issue_id": issue.iid,
            "project_id": project_id,
            "web_url": issue.web_url,
            "title": title
        }

    except Exception as e:
        logger.error(f"Error publishing to GitLab: {e}")
        return {"status": "error", "message": f"Error en GitLab: {str(e)}"}
