import gitlab
from tqdm import tqdm
import pickle
import logging
import os
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)

class GitlabConnection:
    def __init__(self):
        self.gl = gitlab.Gitlab(url=os.getenv("GITLAB_URL"),private_token=os.getenv("GITLAB_TOKEN"))
        self.gl.auth()
        self.gl.enable_debug()
    
    def get_project(self):
        return self.gl.projects.get(os.getenv("GITLAB_PROJECT_URL"))
    
    def get_incidents(self,project):
        incidents = []

        for page in tqdm(project.issues.list(labels='incident',as_list=False,per_page=100)):
            incidents.append(page)
        
        logging.info(f"Total incidents retrieved: {len(incidents)}")
        return incidents
    
    def save_incidents(self,incidents,filename):
        with open(filename,"wb") as f:
            pickle.dump(incidents,f)