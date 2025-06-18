from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging
from pymongo.collection import Collection
from pymongo.database import Database
from dotenv import load_dotenv
import os
from utils.secrets_helper import get_secret
from utils.config import DB_NAME
load_dotenv()

class AtlasConnection:
    def __init__(self, server_api:str =ServerApi('1')):
        """
        Initialize the AtlasConnection class.

        :param uri: MongoDB connection URI.
        :param server_api: Server API version (default is '1').
        """
        atlas_uri = get_secret("atlas-uri", "ATLAS_URI")
        self.client: MongoClient = MongoClient(atlas_uri)
        self.database: Database = self.client[DB_NAME]
    

    def ping(self):
        """
        Send a ping to confirm a successful connection.
        """
        try:
            self.client.admin.command('ping')
        except Exception as e:
            logging.error(f"Error pinging the server: {e}")
    
    # Get the MongoDB Atlas collection to connect to
    def get_collection(self, collection_name:str) -> Collection:
        collection = self.database[collection_name]
        return collection

    # Query a MongoDB collection
    def find(self, collection_name: str, filter={}, limit=0) -> list:
        collection = self.database[collection_name]
        items = list(collection.find(filter=filter, limit=limit))
        return items
            