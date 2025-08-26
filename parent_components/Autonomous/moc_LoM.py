from langchain.vectorstores import FAISS
from langchain.embeddings import OllamaEmbeddings

db = FAISS.load_local("vector_db/lom_index", embeddings=OllamaEmbeddings(model="llama3"))

def store_to_lom(summary: str):
    db.add_texts([summary])
    db.save_local("vector_db/lom_index")


def retrieve_lom_context(user_input: str) -> str:
    results = db.similarity_search(user_input, k=3)
    return "\n".join([doc.page_content for doc in results])

