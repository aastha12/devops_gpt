import gitlab
from tqdm import tqdm
import pickle
import logging
from utils.secrets_helper import get_secret
from utils.config import GITLAB_URL, GITLAB_PROJECT_URL
logging.basicConfig(level=logging.INFO)

class GitlabConnection:
    def __init__(self):
        gitlab_token = get_secret("gitlab-token", "GITLAB_TOKEN")
        self.gl = gitlab.Gitlab(url=GITLAB_URL,private_token=gitlab_token)
        self.gl.auth()
        self.gl.enable_debug()
    
    def get_project(self):
        return self.gl.projects.get(GITLAB_PROJECT_URL)
    
    def get_incidents(self,project):
        incidents = []

        for page in tqdm(project.issues.list(labels='incident',as_list=False,per_page=100)):
            incidents.append(page)
        
        logging.info(f"Total incidents retrieved: {len(incidents)}")
        return incidents
    
    def save_incidents(self,incidents,filename):
        with open(filename,"wb") as f:
            pickle.dump(incidents,f)