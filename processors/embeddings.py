import os
import logging
import numpy as np
import requests
from utils.secrets_helper import get_secret
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self):
        self.api_token = get_secret("huggingface-api-token", "HUGGINGFACE_API_TOKEN") 
        self.model_id = "BAAI/bge-small-en-v1.5"
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def prepare_data(self, data: list[dict]) -> list[str]:
        """
        Prepare the data for embedding.
        """
        return [f"{item['title']} {item['description']}" for item in data]

    def get_embeddings(self, combined_content: list[str]) -> np.ndarray:
        """
        Get embeddings from HuggingFace API with retry logic.
        """
        # Configure session with retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        try:
            logger.info(f"Requesting embeddings for {len(combined_content)} items...")
            response = session.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": combined_content, "options": {"wait_for_model": True}},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Successfully received embeddings from HuggingFace API")
            return np.array(result)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing embeddings: {e}")
            raise
        finally:
            session.close()

    def add_embeddings_to_documents(self, data: list[dict]) -> tuple[tuple[int,int], list[dict]]:
        """
        Add embeddings to the documents.
        """
        logger.info("Starting embedding process...")
        
        combined_content = self.prepare_data(data)
        embeddings = self.get_embeddings(combined_content)
        
        logger.info(f"Model embedding size/dimensionality: {embeddings.shape}")

        for index, doc in enumerate(data):
            doc['embedding'] = embeddings[index].tolist()
        
        logger.info("Embedding process completed")
        return embeddings.shape, data