from connectors.gitlab_connection import GitlabConnection
import os
import pickle
from connectors.atlas_connection import AtlasConnection
from processors.embeddings import EmbeddingModel
from processors.user_query_processor import UserQueryProcessor
from processors.llm_processor import LLMProcessor
from dotenv import load_dotenv

load_dotenv()
# Gitlab connectionp

if not os.path.exists(os.getenv("INCIDENTS_PATH")):
    gl = GitlabConnection()
    gl_project = gl.get_project()
    incidents = gl.get_incidents(gl_project)
    gl.save_incidents(incidents, os.getenv("INCIDENTS_PATH"))


with open(os.getenv("INCIDENTS_PATH"), "rb") as f:
    incidents = pickle.load(f)
print(f"Total incidents loaded: {len(incidents)}")
# print(incidents[0])


# MongoDB Atlas connection

atlas_client = AtlasConnection()
atlas_client.ping()
print("Connected to Atlas instance! We are good to go!")

# convert each incident to dict
# incidents is of gitlab.v4.objects.issues.ProjectIssue type 
# use .attributes built-in property of the ProjectIssue to conver to dict
# MongoDB expects Python dicts, not JSON strings so converting to JSON isn't helpful

incidents_converted = [incident.attributes for incident in incidents]

#insert into MongDB
collection_name = "incidents"
if collection_name not in atlas_client.database.list_collection_names():
    collection = atlas_client.get_collection(collection_name)
    collection.create_index("id", unique=True)
    collection.insert_many(incidents_converted)
    print(f"Inserted {len(incidents_converted)} incidents into MongoDB.")


# create embeddings
embedding_model = EmbeddingModel()
embedding_shape, embedded_incidents = embedding_model.add_embeddings_to_documents(incidents_converted)
# print(embedded_incidents[0])


# insert into MongoDB
collection = atlas_client.get_collection(collection_name)

for incident in embedded_incidents:
    collection.update_one(
        {'id': incident['id']},
        {'$set': {'embedding': incident['embedding']}},
        upsert=True
    )


print(f"Inserted/Updated {len(embedded_incidents)} incidents with embeddings into MongoDB.")

# testing whether it works
# query
query = "pipeline failure and git errors"

query_processor_object = UserQueryProcessor(user_query=query, embedding_model=embedding_model)
incident_texts = query_processor_object.process_query(collection)

llm_processor = LLMProcessor()
response = llm_processor.get_llm_response(query, incident_texts)
print("\n🧠 LLM Response:\n")
print(response)