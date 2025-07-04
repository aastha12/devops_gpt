import os
import logging
import numpy as np
import requests
from utils.secrets_helper import get_secret
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import random

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self):
        print("EmbeddingModel: Initializing...")
        logger.info("EmbeddingModel: Initializing...")
        
        self.api_token = get_secret("huggingface-api-token", "HUGGINGFACE_API_TOKEN") 
        if self.api_token:
            print("EmbeddingModel: HuggingFace API token retrieved.")
            logger.info("EmbeddingModel: HuggingFace API token retrieved.")
        else:
            print("EmbeddingModel: HuggingFace API token NOT found!")
            logger.error("EmbeddingModel: HuggingFace API token NOT found!")
            
        self.model_id = "BAAI/bge-small-en-v1.5"
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        print(f"EmbeddingModel: API URL set to {self.api_url}")
        logger.info(f"EmbeddingModel: API URL set to {self.api_url}")
        
        # Test API connection immediately
        self._test_api_connection()

    def _test_api_connection(self):
        """Test if the API is accessible"""
        try:
            print("EmbeddingModel: Testing API connection...")
            logger.info("EmbeddingModel: Testing API connection...")
            
            test_response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": ["test"], "options": {"wait_for_model": True}},
                timeout=30
            )
            
            if test_response.status_code == 200:
                print("EmbeddingModel: API connection successful!")
                logger.info("EmbeddingModel: API connection successful!")
            elif test_response.status_code == 503:
                print("EmbeddingModel: API model is loading, will retry during actual request")
                logger.warning("EmbeddingModel: API model is loading, will retry during actual request")
            else:
                print(f"EmbeddingModel: API test failed with status {test_response.status_code}")
                logger.error(f"EmbeddingModel: API test failed with status {test_response.status_code}: {test_response.text}")
                
        except Exception as e:
            print(f"EmbeddingModel: API test failed: {e}")
            logger.error(f"EmbeddingModel: API test failed: {e}")

    def prepare_data(self, data: list[dict]) -> list[str]:
        """
        Prepare the data for embedding.
        """
        combined_content = [f"{item['title']} {item['description']}" for item in data]
        print(f"EmbeddingModel: Prepared {len(combined_content)} texts for embedding")
        logger.info(f"EmbeddingModel: Prepared {len(combined_content)} texts for embedding")
        return combined_content

    def get_embeddings(self, combined_content: list[str]) -> np.ndarray:
        """
        Get embeddings from HuggingFace API with aggressive timeout handling.
        """
        if not self.api_token:
            print("EmbeddingModel: No API token, using fallback embeddings")
            logger.warning("EmbeddingModel: No API token, using fallback embeddings")
            return self._get_fallback_embeddings(combined_content)
        
        # Reduced retries and shorter timeouts for faster failure detection
        max_retries = 3
        base_delay = 2
        timeout = 45  # Reduced from 300 to 45 seconds
        
        for attempt in range(max_retries):
            try:
                print(f"EmbeddingModel: Requesting embeddings for {len(combined_content)} items (attempt {attempt + 1}/{max_retries})...")
                logger.info(f"Requesting embeddings for {len(combined_content)} items (attempt {attempt + 1}/{max_retries})...")
                
                # Create a fresh session for each attempt
                session = requests.Session()
                
                # More aggressive retry strategy
                retry_strategy = Retry(
                    total=1,  # Reduced from 2
                    backoff_factor=0.5,  # Reduced from 1
                    status_forcelist=[429, 500, 502, 503, 504],
                    raise_on_status=False
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                start_time = time.time()
                response = session.post(
                    self.api_url,
                    headers=self.headers,
                    json={"inputs": combined_content, "options": {"wait_for_model": True}},
                    timeout=timeout
                )
                elapsed_time = time.time() - start_time
                
                print(f"EmbeddingModel: Request completed in {elapsed_time:.2f} seconds")
                logger.info(f"Request completed in {elapsed_time:.2f} seconds")
                
                if response.status_code == 200:
                    result = response.json()
                    print("EmbeddingModel: Successfully received embeddings from HuggingFace API")
                    logger.info("Successfully received embeddings from HuggingFace API")
                    session.close()
                    return np.array(result)
                    
                elif response.status_code == 503:
                    print(f"EmbeddingModel: Model loading (503), attempt {attempt + 1}/{max_retries}")
                    logger.warning(f"Model loading (503), attempt {attempt + 1}/{max_retries}")
                    session.close()
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"EmbeddingModel: Waiting {delay:.2f} seconds before retry...")
                        logger.info(f"Waiting {delay:.2f} seconds before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        print("EmbeddingModel: Model still loading after all retries, using fallback")
                        logger.error("Model still loading after all retries, using fallback")
                        return self._get_fallback_embeddings(combined_content)
                        
                else:
                    print(f"EmbeddingModel: HTTP {response.status_code}: {response.text}")
                    logger.error(f"HTTP {response.status_code}: {response.text}")
                    session.close()
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"EmbeddingModel: Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        print("EmbeddingModel: All API attempts failed, using fallback")
                        logger.error("All API attempts failed, using fallback")
                        return self._get_fallback_embeddings(combined_content)
                
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
                print(f"EmbeddingModel: Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                
                if 'session' in locals():
                    session.close()
                    
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"EmbeddingModel: Retrying in {delay:.2f} seconds...")
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("EmbeddingModel: All attempts timed out, using fallback embeddings")
                    logger.error("All attempts timed out, using fallback embeddings")
                    return self._get_fallback_embeddings(combined_content)
                    
            except requests.exceptions.RequestException as e:
                print(f"EmbeddingModel: Request failed on attempt {attempt + 1}: {e}")
                logger.error(f"Request failed on attempt {attempt + 1}: {e}")
                
                if 'session' in locals():
                    session.close()
                    
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                else:
                    print("EmbeddingModel: All requests failed, using fallback embeddings")
                    logger.error("All requests failed, using fallback embeddings")
                    return self._get_fallback_embeddings(combined_content)
            
            except Exception as e:
                print(f"EmbeddingModel: Unexpected error: {e}")
                logger.error(f"Unexpected error: {e}")
                
                if 'session' in locals():
                    session.close()
                    
                if attempt < max_retries - 1:
                    continue
                else:
                    print("EmbeddingModel: Unexpected errors, using fallback embeddings")
                    logger.error("Unexpected errors, using fallback embeddings")
                    return self._get_fallback_embeddings(combined_content)
        
        # If we get here, all retries failed
        print("EmbeddingModel: All embedding attempts failed, using fallback")
        logger.error("All embedding attempts failed, using fallback")
        return self._get_fallback_embeddings(combined_content)
    
    def _get_fallback_embeddings(self, combined_content: list[str]) -> np.ndarray:
        """
        Generate simple fallback embeddings when API fails.
        This uses a basic TF-IDF-like approach.
        """
        print(f"EmbeddingModel: Generating fallback embeddings for {len(combined_content)} items")
        logger.warning(f"Using fallback embeddings for {len(combined_content)} items")
        
        # Simple word-based embeddings (384 dimensions to match BGE model)
        embeddings = []
        
        # Build vocabulary from all texts
        all_words = set()
        for text in combined_content:
            words = text.lower().split()
            all_words.update(words)
        
        vocab = list(all_words)
        vocab_size = min(len(vocab), 384)  # Limit to embedding size
        
        for text in combined_content:
            words = text.lower().split()
            embedding = [0.0] * 384
            
            # Simple word frequency embedding
            for word in words:
                if word in vocab:
                    idx = vocab.index(word) % 384
                    embedding[idx] += 1.0
            
            # Normalize
            norm = sum(x*x for x in embedding) ** 0.5
            if norm > 0:
                embedding = [x/norm for x in embedding]
            
            embeddings.append(embedding)
        
        print(f"EmbeddingModel: Generated fallback embeddings with shape {len(embeddings)}x384")
        logger.info(f"Generated fallback embeddings with shape {len(embeddings)}x384")
        return np.array(embeddings)

    def add_embeddings_to_documents(self, data: list[dict]) -> tuple[tuple[int,int], list[dict]]:
        """
        Add embeddings to the documents.
        """
        print(f"EmbeddingModel: Starting embedding process for {len(data)} documents")
        logger.info(f"Starting embedding process for {len(data)} documents")
        
        try:
            combined_content = self.prepare_data(data)
            embeddings = self.get_embeddings(combined_content)
            
            print(f"EmbeddingModel: Generated embeddings with shape: {embeddings.shape}")
            logger.info(f"Model embedding size/dimensionality: {embeddings.shape}")

            for index, doc in enumerate(data):
                doc['embedding'] = embeddings[index].tolist()
            
            print("EmbeddingModel: Embedding process completed successfully")
            logger.info("Embedding process completed successfully")
            return embeddings.shape, data
            
        except Exception as e:
            print(f"EmbeddingModel: Critical error in embedding process: {e}")
            logger.error(f"Critical error in embedding process: {e}")
            raise