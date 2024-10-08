# -*- coding: utf-8 -*-
"""vector_search & genertion w weaviate.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/14uDdvIfJea1bqkpdWpgoER-WPymXG4th
"""

import gc
gc.collect()

!pip install -U weaviate-client

!pip show weaviate-client

!pip install sentence-transformers

import weaviate as wv
import weaviate.batch as wb
import weaviate.classes as wc
import weaviate.classes.config as wvc
from weaviate.classes.init import Auth
from weaviate.util import generate_uuid5
from weaviate.classes.query import Filter
from weaviate import EmbeddedOptions
from sentence_transformers import SentenceTransformer
from weaviate.classes.config import Configure, DataType, Property
import os
import uuid
import json
import random
import time

model_name = "all-MiniLM-L6-v2"  # Replace with your desired model
model = SentenceTransformer(model_name)

folder_path = '/content/drive/MyDrive/text_files'
file_data_dict = {}

for filename in os.listdir(folder_path):
    if filename.endswith('.txt'):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            unique_id = int(uuid.uuid4())  # Generate a unique ID
            unique_id = unique_id % 1000000000
            file_data_dict[unique_id] = {
                'filename': filename,
                'content': content
            }

def chunk_text(text, chunk_size):
    """Chunk text into smaller parts of a given size."""
    chunks = []
    while len(text) > chunk_size:
        chunks.append(text[:chunk_size])
        text = text[chunk_size:]
    chunks.append(text)  # Add the last chunk
    return chunks

def recursive_chunk(file_data_dict, chunk_size):
    """Apply chunking recursively to the content of each file in the dictionary."""
    chunked_data = {}
    for unique_id, data in file_data_dict.items():
        content = data['content']
        chunks = chunk_text(content, chunk_size)
        chunked_data[unique_id] = {
            'filename': data['filename'],
            'chunks': chunks
        }
    return chunked_data

chunks=recursive_chunk(file_data_dict, 100)

#chunks=list(chunks.values())
print(chunks)

for unique_id, data in file_data_dict.items():
    print(f"ID: {unique_id}")
    print(f"Filename: {data['filename']}")
    print(f"Content: {data['content']}")

file_ids = list(file_data_dict.keys())
random.shuffle(file_ids)

def assign_files_to_names(file_data_dict, file_ids, names_list):
    """
    Assigns files to names in a round-robin fashion.

    Args:
        file_data_dict (dict): Dictionary where keys are file IDs and values are file data.
        file_ids (list): List of file IDs.
        names_list (list): List of names to assign files to.

    Returns:
        dict: A dictionary where keys are names and values are lists of file data with IDs.
    """
    # Initialize the result dictionary with names as keys and empty lists as values
    names_dict = {name: [] for name in names_list}

    # Assign files to names
    for i, file_id in enumerate(file_ids):
        name = names_list[i % len(names_list)]  # Use modulo to cycle through names
        file_data = file_data_dict[file_id]
        # Format the file data with ID first, then filename, and content last
        formatted_file_data = {
            'id': file_id,
            'filename': file_data['filename'],
            'content': file_data['content']
        }
        names_dict[name].append(formatted_file_data)

    return names_dict

names_list=["Amaan", "Huzan", "Umair", "Waleed"]
names_dict = assign_files_to_names(file_data_dict, file_ids, names_list)
print(names_dict)

def extract_metadata(names_dict):
    """Extract metadata from the names_dict."""
    metadata = {}
    for name, paragraphs in names_dict.items():
        metadata[name] = {
            'name': name,
            'file_id': [para['id'] for para in paragraphs], # Access the 'ID' value for each paragraph in the list
            'filename': [para['filename'] for para in paragraphs], # Access the 'text' value for each paragraph in the list
            'content': [para['content'] for para in paragraphs], # Access the 'text' value for each paragraph in the list# Access the 'text' value for each paragraph in the list           'content': [para['content'] for para in paragraphs], # Access the 'text' value for each paragraph in the list
        }
    return metadata

metadata = extract_metadata(names_dict)
for key, value in metadata.items():
    print(f"{key}: {value}\n")

client.close()

#os.environ["COHERE_API"] = "0Wv2lxPPOI1yqEtz11NiGjZsjpM10778KRZ7TgYo"
client=wv.connect_to_embedded(
    headers={
    "X-Cohere-Api-Key" : "0Wv2lxPPOI1yqEtz11NiGjZsjpM10778KRZ7TgYo"
    }
)
wv.auth.AuthApiKey(api_key=os.environ["COHERE_API"])

client.get_meta()



class_obj = {
    "class": "Person",
    "vectorizer": "text2vec-transformers",  # Ensure this matches the desired vectorizer
    "moduleConfig": {
        "text2vec-transformers": {
            "poolingStrategy": "masked_mean",
            "vectorizeClassName": True
        }
    },
    "properties": [
        {"name": "name", "dataType": ["string"]},
        {"name": "ID", "dataType": ["int"]},
        {"name": "filename", "dataType": ["string"]},
        {"name": "content", "dataType": ["text"]}
    ]
}



client.collections.delete("Person")



# Load the Hugging Face model
client.collections.create(
    name="Person",
    description="A class to store the authors of articles",
    vectorizer_config=wvc.Configure.Vectorizer.text2vec_cohere(),

    #module_config=wc.config.Configure.ModuleConfig.text2vec_huggingface(
    #    model_name="sentence-transformers/all-MiniLM-L6-v2"
    #),
    inverted_index_config=wc.config.Configure.inverted_index(
        index_property_length=True
    ),
    vector_index_config=wc.config.Configure.VectorIndex.hnsw(),
    properties=[
        Property(name="name", data_type=DataType.TEXT),
        Property(name="file_id", data_type=DataType.INT_ARRAY),
        Property(name="filename", data_type=DataType.TEXT_ARRAY),
        Property(name="content", data_type=DataType.TEXT_ARRAY)
    ]
)

client.get_meta()

data = client.collections.get("Person")
print(data)

client.connect()
client.is_ready()

for item in metadata.values():
    data=client.collections.get("Person").data.insert(item)
    print(f"Inserted object with ID: {data}")
print("Data insertion complete.")

result = client.graphql_raw_query("""
{
  Get {
    Person(limit: 4) {
      name
      file_id
      filename
      content
    }
  }
}
""")

print(f"Type of result: {type(result)}")
print(f"Result structure: {result}")  # Print the entire result to inspect its structure

# Convert result.get to a dictionary if it's not already
result_dict = dict(result.get) if not isinstance(result.get, dict) else result.get

print(f"Type of result_dict: {type(result_dict)}")
print(f"Result_dict structure: {result_dict}")  # Print the entire result to inspect its structure

# Access the data from the correct path
persons = result_dict.get('Get', {}).get('Person', [])

for person in persons:
    person_key = None
    for key, value in metadata.items():
        if value.get('name') == person.get('name'):
            person_key = key
            break  # Stop searching once a match is found

    metadata_id = metadata.get(person_key, {}).get('file_id', 'N/A') if person_key else 'N/A'

    print("-" * 30)  # Separator for better readability
    print(f"Name: {person.get('name', 'N/A')}")
    print(f"ID (from metadata): {metadata_id}")
    print(f"Filename: {person.get('filename', 'N/A')}")
    content_preview = person.get('content', [''])[0][:100] + "..." if person.get('content') else "N/A"
    print(f"Content Preview: {content_preview}")
    print("-" * 30)  # Separator

res = client.collections.get("Person")

result = res.query.near_text(
    query="what is the importance of artificial intelligence",
    limit=1,
    return_metadata=wc.query.MetadataQuery(distance=True)
)

for o in result.objects:
    print(o.properties)

from weaviate.classes.query import QueryReference

res = client.collections.get("Person")
response = res.query.fetch_objects(
    return_references=[
        QueryReference(
            link_on="content",
            return_properties=["name", "file_id","content"]
        ),
    ],
    limit=5
)

for o in response.objects:
    print(o.properties)
    # print referenced objects



from weaviate.classes.query import MetadataQuery
res = client.collections.get("Person")
response = res.query.near_text(
    query="Impact of technology",
    distance = 0.25,
    limit=2,
    return_metadata=MetadataQuery(distance=True)
)

for o in response.objects:
    print(o.properties)
    print(o.metadata.distance)

res=client.collections.get("Person")
print(res)
result=res.query.fetch_objects(limit=1)
print(result)

the_query = "what is the importance of artificial intelligence"

query_vector = model.encode(the_query)
print(query_vector)

from weaviate.classes.query import HybridFusion

res = client.collections.get("Person")
result = res.query.hybrid(
    query="COVID-19",
    fusion_type=HybridFusion.RANKED,
    auto_limit=1,

    limit=5,
    return_metadata=wc.query.MetadataQuery(
        certainty=True,
)
)

for item in result.objects:
  print(item)

res = client.collections.get("Person")
response = res.query.near_text(
    query="what is the importance of artificial intelligence",
    limit=1,
    return_metadata=wc.query.MetadataQuery(distance=True)
)

for o in response.objects:
    print(o.properties)  # Selected properties only
    print(o.uuid)  # UUID included by default
    print(o.vector)  # With vector
    print(o.metadata)  # With selected metadata

prompt ="Importance of remote work in IT industry"

prompt_vector = model.encode(prompt)

result = res.query.near_vector(
    #distance = "cosine",
    near_vector = query_vector,
    limit = 5,
    #single_prompt= "Translate to french: {query}",
    return_properties=["name", "filename"],
    return_metadata=wc.query.MetadataQuery(certainty=True)
)
for item in result.objects:
  print(item)

result = res.query.fetch_objects(
    filters = (Filter.by_property("name").equal("Amaan") |
    Filter.by_property("name").equal("Huzan")) &
    (Filter.by_property("filename").equal("data11.txt") |
    Filter.by_property("filename").equal("data5.txt")),
    return_properties=["name", "filename"]
)
print(result)

response = res.query.bm25(
    query="artificial",
    include_vector=True,
    return_properties=["name", "filename", "file_id"],
    return_metadata=wc.query.MetadataQuery(distance=True),
    return_references=wc.query.QueryReference(
        link_on="file_id",
        return_properties=["name"],
        return_metadata=wc.query.MetadataQuery(creation_time=True)
    ),
    limit=2
)

for o in response.objects:
    print(o.properties)  # Selected properties only
    print(o.references)  # Selected references
    print(o.uuid)  # UUID included by default
    print(o.vector)  # With vector
    print(o.metadata)  # With selected metadata

for query in prompt:
  result = res.query.near_text(
      query = query,
      limit = 5,
      return_metadata=wc.query.MetadataQuery(certainty=True)
  )
print(result)

result = res.generate.near_text(
    query="How significant is remote job nowadays",
    limit=1,

    return_metadata=wc.query.MetadataQuery(distance=True)
)

print(result)

name="Waleed"
id = metadata[name]["file_id"] # Make sure metadata[name] exists and has a "file_id" key
print(id)

if isinstance(id, list):
    # Handle the case where 'id' is a list
    if id:  # Check if the list is not empty
        id = id[0]  # Use the first element of the list
    else:
        print("Error: 'id' is an empty list. Cannot perform query.")
        # Handle the error appropriately, perhaps by skipping the query or raising an exception

result = res.query.fetch_objects(
    filters = Filter.by_property("file_id").equal(id),
    return_properties=["file_id"]
)
print(result)

