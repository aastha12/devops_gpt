from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self,model_name:str = 'all-MiniLM-L6-v2'):
        """
        Initialize the EmbeddingModel class.

        :param model_name: Name of the pre-trained model to use for embeddings.
        """
        self.model = SentenceTransformer(model_name)
    
    def prepare_data(self, data: list[dict]) -> list[str]:
        """
        Prepare the data for embedding.

        :param data: List of strings to be embedded.
        :return: List of strings.
        """
        # combine title and description in one string to capture full context
        return [f"{item['title']} {item["description"]}" for item in data]

    def get_embeddings(self,combined_content:list[str]) -> list:
        """
        Get embeddings for the provided data.

        :param combined_content: List of strings to be embedded.
        :return: List of embeddings.
        """
        return self.model.encode(combined_content, show_progress_bar = True)

    def add_embeddings_to_documents(self,data:list[dict]) -> tuple[tuple[int,int],list[dict]]:
        """
        Add embeddings to the documents.

        :param data: List of strings to be embedded.
        :return: List of dictionaries with embeddings.
        """
        combined_content = self.prepare_data(data)
        embeddings = self.get_embeddings(combined_content)
        print(f"Model embedding size/dimensionality of vectors: {embeddings.shape}")

        for index, doc in enumerate(data):
            doc['embedding'] = embeddings[index].tolist()
        
        return embeddings.shape,data
