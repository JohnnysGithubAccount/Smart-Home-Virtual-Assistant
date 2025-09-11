# from langchain_community.graphs import Neo4jGraph
from langchain_community.embeddings import OllamaEmbeddings
from langchain_neo4j import Neo4jGraph
from langchain_neo4j import Neo4jVector
import requests
import getpass

def create_graph_from_devices(graph_input, url: str = ""):
    url = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/test.json"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        raise Exception

    room_devices = response.json()

    for room_name, room_data in room_devices.items():
        # Create Room node
        graph_input.query(f"""
            MERGE (r:Room {{name: '{room_name}'}})
        """)

        # Devices
        for device_type, value in room_data.get("device", {}).items():
            device_id = f"{room_name}_{device_type}"
            graph_input.query(f"""
                MERGE (r:Room {{name: '{room_name}'}})
                MERGE (d:Device {{
                    id: '{device_id}',
                    type: '{device_type}',
                    room: '{room_name}'
                }})
                SET d.value = '{value}'
                MERGE (r)-[:HAS_DEVICE]->(d)
            """)

        # Sensors
        for sensor_type, value in room_data.get("sensors", {}).items():
            sensor_id = f"{room_name}_{sensor_type}"
            graph_input.query(f"""
                MERGE (r:Room {{name: '{room_name}'}})
                MERGE (s:Sensors {{
                    id: '{sensor_id}',
                    type: '{sensor_type}',
                    room: '{room_name}'
                }})
                SET s.value = {value}
                MERGE (r)-[:HAS_SENSOR]->(s)
            """)



def main():
    # password = getpass.getpass("Enter Neo4j password: ")
    url = "neo4j://127.0.0.1:7687"
    username = 'neo4j'
    password = "password"

    graph_db = Neo4jGraph(
        url=url,
        username=username,
        password=password
    )

    # delete and recreate the graph
    # graph_db.query("MATCH (n) DETACH DELETE n")
    # create_graph_from_devices(graph_db)

    # Use Ollama’s embedding model
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # vector_index = Neo4jVector.from_existing_graph(
    #     embeddings,
    #     url=url,
    #     username=username,
    #     password=password,
    #     index_name="device_index",
    #     node_label="Device",
    #     text_node_properties=["id", "type", "room", "value"],
    #     embedding_node_property="embedding",
    # )
    vector_index = Neo4jVector.from_existing_graph(
        embeddings,
        url=url,
        username=username,
        password=password,
        index_name="device_index",
        node_label="Sensors",
        text_node_properties=["id", "type", "room", "value"],
        embedding_node_property="embedding",
    )
    result = vector_index.similarity_search("Which room is the hottest room")
    print(result)

if __name__ == "__main__":
    main()