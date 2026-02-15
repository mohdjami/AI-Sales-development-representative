try:
    from pinecone import Pinecone
    print("Successfully imported Pinecone")
    pc = Pinecone(api_key="test")
    print("Successfully initialized Pinecone client")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

import pinecone
print(f"Pinecone module location: {pinecone.__file__}")
