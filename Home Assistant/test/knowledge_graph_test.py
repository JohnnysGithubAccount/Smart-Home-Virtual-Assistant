import time
from typing import List
from langchain_community.document_loaders import WikipediaLoader
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.graph_transformers import LLMGraphTransformer

from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import TokenTextSplitter
from pydantic import BaseModel, Field


def main():
    # === Neo4j Setup ===
    url = "neo4j://127.0.0.1:7687"
    username = "neo4j"
    password = "password"

    graph = Neo4jGraph(
        url=url,
        username=username,
        password=password
    )

    # (Optional) Clear the database if you want fresh start
    graph.query("MATCH (n) DETACH DELETE n")

    # === Embedding Model (Ollama) ===
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # === Load Data (Wikipedia: Black Holes) ===
    # raw_documents = WikipediaLoader(query="Black hole").load()
    # print(f"Loaded {len(raw_documents)} documents.")
    # print(raw_documents)
    raw_documents = [
        Document(
            page_content="Johnny is living in a black hole",
            metadata={"source": "test"}
        )
    ]

    # === Split Documents into Chunks ===
    text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
    documents = text_splitter.split_documents(raw_documents)  # take only first 3 for testing

    # === LLM (for graph extraction & queries) ===
    llm = ChatOllama(model="qwen3:0.6b", temperature=0)

    # def _safe_format_nodes(nodes):
    #     formatted = []
    #     for el in nodes:
    #         props = el.properties if isinstance(el.properties, dict) else {}
    #         formatted.append(
    #             llm.Node(
    #                 id=el.id,
    #                 type=el.type,
    #                 properties=props,
    #             )
    #         )
    #     return formatted

    # llm._format_nodes = _safe_format_nodes

    # === Convert to Graph Format ===
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(documents)

    # === Store Graph in Neo4j ===
    # graph.add_graph_documents(
    #     graph_documents,
    #     baseEntityLabel=True,   # keep a general "Entity" label
    #     include_source=True     # track where facts came from
    # )

    # === Create / Attach Vector Index ===

    vector_index = Neo4jVector.from_existing_graph(
        embeddings,
        url=url,
        username=username,
        password=password,
        search_type="hybrid",
        node_label="Chunk",                # chunks hold text
        text_node_properties=["text"],     # property containing the text
        embedding_node_property="embedding"
    )

    # Retrieval step
    start_time = time.time()
    retrieved_docs = vector_index.similarity_search(
        "Where is Johnny living", k=3)
    print(f"Elapse time:{time.time() - start_time}")

    # Format docs into context
    context = "\n".join([doc.page_content for doc in retrieved_docs])

    # Now run LLM with context (RAG style)
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a black hole scientist."),
        ("human", "Answer the question using the context:\n\nContext:\n{context}\n\nQuestion: {question}")
    ])

    rag_chain = rag_prompt | llm
    rag_answer = rag_chain.invoke({
        "context": context,
        "question": "Where is Johnny living"
    })

    print(rag_answer.content)


if __name__ == "__main__":
    main()
