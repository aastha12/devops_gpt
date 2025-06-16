from processors.embeddings import EmbeddingModel 
from pymongo.collection import Collection

class UserQueryProcessor:
    def __init__(self, user_query: str ,embedding_model: EmbeddingModel):
        self.user_query = user_query
        self.embedding_model = embedding_model

    def process_query(self,collection: Collection) -> list[str]:
        query_embedding = self.embedding_model.get_embeddings([self.user_query])[0]  # shape: (384,)

        # Perform vector search in MongoDB Atlas
        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": query_embedding.tolist(), # embedding of your query
                    "path": "embedding", # field in MongoDB that holds the embeddings
                    "numCandidates": 100, # How many documents MongoDB considers before picking top limit results
                    "limit": 5, #How many top similar results you want
                    "index": "embedding_vector_index"  # name of the index you created
                }
            },
            {
                # The $project stage in the MongoDB aggregation pipeline is used to shape the output
                "$project": {
                    "_id": 0, # Excludes MongoDB's internal _id field (default in documents)
                    "id": 1, # Includes the GitLab incident's id
                    "title": 1, # Includes the title field from the document
                    "description": 1,
                    "score": {"$meta": "vectorSearchScore"} # Uses {"$meta": "vectorSearchScore"} to include MongoDB's similarity score
                }
            }
        ]

        # .aggregate() method in MongoDB is used to process data records through a pipeline of operations like vector search
        results = list(collection.aggregate(pipeline))

        # Combine incident descriptions for LLM input
        incident_texts = [f"{r['title']}\n{r['description']}" for r in results]

        return incident_texts