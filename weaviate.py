# -*- coding: utf-8 -*-
"""Weaviate.ipynb

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
from weaviate.classes.query import MetadataQuery
from weaviate import EmbeddedOptions
from sentence_transformers import SentenceTransformer
from weaviate.classes.config import Configure, DataType, Property
import os
import uuid
import json
import random

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

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
            'ID': [para['id'] for para in paragraphs], # Access the 'ID' value for each paragraph in the list
            'filename': [para['filename'] for para in paragraphs], # Access the 'text' value for each paragraph in the list
            'content': [para['content'] for para in paragraphs], # Access the 'text' value for each paragraph in the list# Access the 'text' value for each paragraph in the list           'content': [para['content'] for para in paragraphs], # Access the 'text' value for each paragraph in the list
        }
    return metadata

metadata = extract_metadata(names_dict)
for key, value in metadata.items():
    print(f"{key}: {value}\n")

# Set these environment variables correctly
os.environ["URL"] = "https://a8kemytbrfygcngbv0i0ba.c0.australia-southeast1.gcp.weaviate.cloud"
os.environ["APIKEY"] = "X3HCB7hqaTlIBng0lG2BN3uup6MhUCIOGv3w"

# Retrieve environment variables
URL = os.getenv("URL")
APIKEY = os.getenv("APIKEY")

# Connect to Weaviate Cloud
client = wv.Client(
    url=URL, # Use 'url' instead of 'weaviate_url'
    auth_client_secret=wv.AuthApiKey(api_key=APIKEY),
)

# Check connection
client.is_ready()

client=wv.connect_to_embedded()



class_obj={
  "class": "Person",
  "vectorizer": "text2vec-transformers",
  "properties": [
    {"name": "name", "dataType": ["string"], "vectorizePropertyName": True},
    {"name": "ID", "dataType": ["int[]"], "vectorizePropertyName": True},
    {"name": "filename", "dataType": ["string[]"], "vectorizePropertyName": True},
    {"name": "content", "dataType": ["text[]"], "vectorizePropertyName": True}
    ]
}

client.collections.create_from_dict(class_obj)

for item in metadata.values():
    data = client.collections.get("Person").data.insert(item)
    print(f"Inserted object with ID: {data}")

print("Data insertion complete.")

result = client.graphql_raw_query("""
{
  Get {
    Person(limit: 4) {
      name
      iD
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

    metadata_id = metadata.get(person_key, {}).get('ID', 'N/A') if person_key else 'N/A'

    print("-" * 30)  # Separator for better readability
    print(f"Name: {person.get('name', 'N/A')}")
    print(f"ID (from metadata): {metadata_id}")
    print(f"Filename: {person.get('filename', 'N/A')}")
    content_preview = person.get('content', [''])[0][:100] + "..." if person.get('content') else "N/A"
    print(f"Content Preview: {content_preview}")
    print("-" * 30)  # Separator

res=client.collections.get("Person")
result=res.query.fetch_objects(limit=1)
print(result)

result = res.query.near_text(
    query = "what are factors that boosted the remote work",
    limit=1,
    return_metadata=MetadataQuery(distance=True)
)

