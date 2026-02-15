from typing import Literal, List
import requests
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

JINA_API_KEY = os.getenv("JINA_API_KEY")
dimension = 1024

index_name = "jina-embeddings-v3"

if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

index = pc.Index(index_name)

def get_embeddings(
	texts: List[str], 
	dimensions: int, 
	task: Literal['text-matching', 'separation', 'classification', 'retrieval.query', 'retrieval.passage']):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {JINA_API_KEY}'
    }
    data = {
        'input': texts,
        'model': 'jina-embeddings-v3',
        'dimensions': dimensions,
        'task': task
    }
    response = requests.post('https://api.jina.ai/v1/embeddings', headers=headers, json=data)
    return response.json()
    
# Data to index
data = [
	{"id": "vec1", "text": "Apple is a popular fruit known for its sweetness and crisp texture."},
	{"id": "vec2", "text": "The tech company Apple is known for its innovative products like the iPhone."},
	{"id": "vec3", "text": "Many people enjoy eating apples as a healthy snack."},
	{"id": "vec4", "text": "Apple Inc. has revolutionized the tech industry with its sleek designs and user-friendly interfaces."},
	{"id": "vec5", "text": "An apple a day keeps the doctor away, as the saying goes."},
]


embeddings = get_embeddings([d["text"] for d in data], dimensions=dimension, task='retrieval.passage')
embeddings = [e["embedding"] for e in embeddings["data"]]
vectors = []
for d, e in zip(data, embeddings):
	vectors.append({
		"id": d['id'],
		"values": e,
		"metadata": {'text': d['text']}
	})
	
index.upsert(
	vectors=vectors,
	namespace="ns1"
)