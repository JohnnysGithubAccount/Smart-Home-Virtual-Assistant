import time
from typing import List
from langchain_community.document_loaders import WikipediaLoader
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.graph_transformers import LLMGraphTransformer
import langchain_experimental.graph_transformers.llm as llm_module

from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import TokenTextSplitter
# from pydantic import BaseModel, Field
from langchain.schema import Document
# from langchain_core.documents import Document
from .utils import extract_thought_and_speech


def _safe_format_nodes(nodes):
    formatted = []
    for el in nodes:
        props = el.properties if isinstance(el.properties, dict) else {}
        # print(f"[DEBUG] node properties:", el.properties, type(el.properties))
        formatted.append(
            llm_module.Node(  # ✅ use Node from the module
                id=el.id,
                type=el.type,
                properties=props,
            )
        )
    return formatted


llm_module._format_nodes = _safe_format_nodes  # ✅ patch globally


class MemoryHelper:
    def __init__(self, url, username, password, embeddings=None, llm=None):
        # === Neo4j Setup ===
        # url = "neo4j://127.0.0.1:7687"
        # username = "neo4j"
        # password = "password"

        # === Init Knowledge Graph ===
        self.graph = Neo4jGraph(
            url=url,
            username=username,
            password=password
        )

        # === Embedding Model (Ollama) ===
        if not embeddings:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        else:
            self.embeddings = embeddings

        # === LLM (for graph extraction & queries) ===
        if not llm:
            self.llm = ChatOllama(model="qwen3:0.6b", temperature=0)
        else:
            self.llm = llm

        self.llm_transformer = LLMGraphTransformer(llm=self.llm)

        system_prompt = f"""
        You are analyzing conversation logs between a smart home assistant and the user.  
        Extract and summarize the user's **habits, preferences, and routines** that may be useful 
        for future automation.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            MessagesPlaceholder(variable_name="context"),
            ("human", "{input}")
        ])

        self.llm_chain = prompt | llm  # Chain with the tool-bound LLM

        # === Create / Attach Vector Index ===
        self.vector_index = Neo4jVector.from_existing_graph(
            self.embeddings,
            url=url,
            username=username,
            password=password,
            search_type="hybrid",
            node_label="Chunk",  # chunks hold text
            text_node_properties=["text"],  # property containing the text
            embedding_node_property="embedding"
        )

    def delete_database_data(self):
        # (Optional) Clear the database if you want fresh start
        self.graph.query("MATCH (n) DETACH DELETE n")

    def summarize_messages(self, messages):
        """
        Summarize user habits and preferences from a list of conversation messages.
        messages: list of HumanMessage, AIMessage, ToolMessage
        Returns: summarized text string
        """
        # Convert structured messages into a plain text transcript
        transcript = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                transcript.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                transcript.append(f"Assistant: {msg.content}")
            elif isinstance(msg, ToolMessage):
                transcript.append(f"Tool: {msg.content}")
            else:
                transcript.append(f"Other: {msg.content}")

        conversation_text = "\n".join(transcript)

        # Ask the LLM to extract **habits/preferences** instead of just generic summary
        prompt = f"""Learn user habits from the conversation."""
        # context = self.retrieve_context()

        input_dict = {
            "input": prompt,
            "history": messages,
            "context": []
        }

        response = self.llm_chain.invoke(input_dict)
        thoughts, response = extract_thought_and_speech(response.content)
        print(f"Summarizer thoughts: {thoughts}")
        print(f"Summarizer response: {response}")

        return response.content if hasattr(response, "content") else str(response)

    def load_wiki_data(self):
        # === Load Data (Wikipedia: Black Holes) ===
        raw_documents = WikipediaLoader(query="Black hole").load()
        print(f"Loaded {len(raw_documents)} documents.")
        print(raw_documents)

        # === Split Documents into Chunks ===
        text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
        documents = text_splitter.split_documents(raw_documents[:3])  # take only first 3 for testing
        return documents

    def text_to_graph(self, text):
        # === Convert to Graph Format ===
        if isinstance(text, str):
            print(f"[DEBUG] Converting to Document")
            _, text = extract_thought_and_speech(text)
            text = Document(page_content=text, metadata={"source": "conversation"})
        graph_documents = self.llm_transformer.convert_to_graph_documents([text])

        # === Store Graph in Neo4j ===
        self.graph.add_graph_documents(
            graph_documents,
            baseEntityLabel=True,   # keep a general "Entity" label
            include_source=True     # track where facts came from
        )

    def retrieve_context(self, text, k: int = 3):
        retrieved_docs = self.vector_index.similarity_search(text, k=k)
        # Format docs into context
        context = "\n".join([doc.page_content for doc in retrieved_docs])
        return context


def main():
    # Now run LLM with context (RAG style)
    # rag_prompt = ChatPromptTemplate.from_messages([
    #     ("system", "You are a black hole scientist."),
    #     ("human", "Answer the question using the context:\n\nContext:\n{context}\n\nQuestion: {question}")
    # ])
    #
    # rag_chain = rag_prompt | llm
    # rag_answer = rag_chain.invoke({
    #     "context": context,
    #     "question": "What happens at the event horizon of a black hole?"
    # })
    #
    # print(rag_answer.content)
    pass


if __name__ == "__main__":
    main()
