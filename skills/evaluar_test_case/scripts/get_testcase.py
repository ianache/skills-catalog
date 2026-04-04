"""Get test case information from GitLab."""

import sys
import os
import json  
from typing import Dict, Any
from skills.evaluar_test_case.scripts.gitlab_client import GitLabClient
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

def execute(project_id: int, issue_id: int) -> Dict[str, Any]:
    """Get test case information.

    Args:
        project_id: Project identifier
        issue_id: Test Case identifier

    Returns:
        Dictionary with test case specification
    """
    logger.info(f"Getting test case information for project {project_id} and issue {issue_id}")

    try:
        client = GitLabClient(
            base_url=os.getenv('GITLAB_URL', 'https://project.comsatel.com.pe'),
            private_token=os.getenv('GITLAB_TOKEN')
        )

        issue = client.get_issue(project_id, issue_id)
        return json.dumps({
            'title': issue.title,
            'specification': issue.description,
            'labels': issue.labels,
            'state': issue.state,
            'author': issue.author,
            'url': issue.url
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        if isinstance(client, GitLabClient):
            client.close()
