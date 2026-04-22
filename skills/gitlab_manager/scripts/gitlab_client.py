import os
import requests
from typing import Optional, Dict, Any, List

class GitLabClient:
    def __init__(self, base_url: str = None, private_token: str = None):
        self.base_url = (base_url or os.getenv('GITLAB_URL', "https://project.comsatel.com.pe")).rstrip('/')
        self.private_token = private_token or os.getenv('GITLAB_TOKEN')
        
        if not self.private_token:
            raise ValueError("Se requiere un token de GitLab (GITLAB_TOKEN)")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Private-Token': self.private_token,
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None, json_data: Dict[str, Any] = None) -> Any:
        url = f"{self.base_url}/api/v4{endpoint}"
        response = self.session.request(method, url, params=params, json=json_data)
        response.raise_for_status()
        if response.status_code == 204:
            return True
        return response.json()

    # Groups
    def list_groups(self, search: str = None) -> List[Dict[str, Any]]:
        if search and (isinstance(search, int) or (isinstance(search, str) and search.isdigit())):
            try:
                group = self.get_group(int(search))
                return [group]
            except Exception:
                return []
        
        params = {}
        if search:
            params['search'] = search
        return self._request('GET', '/groups', params=params)

    def get_group(self, group_id: int) -> Dict[str, Any]:
        return self._request('GET', f'/groups/{group_id}')

    def create_group(self, name: str, path: str, parent_id: int = None) -> Dict[str, Any]:
        data = {'name': name, 'path': path}
        if parent_id:
            data['parent_id'] = parent_id
        return self._request('POST', '/groups', json_data=data)

    # Projects
    def list_projects(self, search: str = None, group_id: int = None) -> List[Dict[str, Any]]:
        params = {}
        if search:
            params['search'] = search
            
        if group_id:
            endpoint = f"/groups/{group_id}/projects"
        else:
            endpoint = "/projects"
            
        return self._request('GET', endpoint, params=params)

    # Users
    def list_users(self, search: str = None, username: str = None) -> List[Dict[str, Any]]:
        params = {}
        if search:
            params['search'] = search
        if username:
            params['username'] = username
        return self._request('GET', '/users', params=params)

    # Issues
    def list_issues(self, project_id: int = None, group_id: int = None, state: str = None, search: str = None) -> List[Dict[str, Any]]:
        params = {}
        if state:
            params['state'] = state
        if search:
            params['search'] = search
            
        if project_id:
            endpoint = f"/projects/{project_id}/issues"
        elif group_id:
            endpoint = f"/groups/{group_id}/issues"
        else:
            endpoint = "/issues"
            
        return self._request('GET', endpoint, params=params)

    def create_issue(self, project_id: int, title: str, description: str = None, labels: List[str] = None, assignee_ids: List[int] = None) -> Dict[str, Any]:
        data = {'title': title}
        if description:
            data['description'] = description
        if labels:
            data['labels'] = ",".join(labels)
        if assignee_ids:
            data['assignee_ids'] = assignee_ids
            
        return self._request('POST', f"/projects/{project_id}/issues", json_data=data)

    def update_issue(self, project_id: int, issue_iid: int, **kwargs) -> Dict[str, Any]:
        data = {}
        if 'title' in kwargs: data['title'] = kwargs['title']
        if 'description' in kwargs: data['description'] = kwargs['description']
        if 'state_event' in kwargs: data['state_event'] = kwargs['state_event']
        if 'labels' in kwargs: data['labels'] = ",".join(kwargs['labels'])
        if 'assignee_ids' in kwargs: data['assignee_ids'] = kwargs['assignee_ids']
        
        return self._request('PUT', f"/projects/{project_id}/issues/{issue_iid}", json_data=data)

    # Milestones
    def list_milestones(self, project_id: int = None, group_id: int = None, state: str = None, search: str = None) -> List[Dict[str, Any]]:
        params = {}
        if state:
            params['state'] = state
        if search:
            params['search'] = search
            
        if project_id:
            endpoint = f"/projects/{project_id}/milestones"
        elif group_id:
            endpoint = f"/groups/{group_id}/milestones"
        else:
            raise ValueError("Se requiere project_id o group_id para listar milestones")
            
        return self._request('GET', endpoint, params=params)

    def create_milestone(self, project_id: int = None, group_id: int = None, title: str = None, description: str = None, start_date: str = None, due_date: str = None) -> Dict[str, Any]:
        if not title:
            raise ValueError("El título es obligatorio para crear un milestone")
            
        data = {'title': title}
        if description:
            data['description'] = description
        if start_date:
            data['start_date'] = start_date
        if due_date:
            data['due_date'] = due_date
            
        if project_id:
            endpoint = f"/projects/{project_id}/milestones"
        elif group_id:
            endpoint = f"/groups/{group_id}/milestones"
        else:
            raise ValueError("Se requiere project_id o group_id para crear un milestone")
            
        return self._request('POST', endpoint, json_data=data)
