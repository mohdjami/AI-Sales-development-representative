from pinecone import Pinecone, ServerlessSpec
import requests
from typing import Dict, List, Any, Literal
import json
import logging
import re
import time
import random
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.index_name = "meetings-index"
        
        # OpenAI text-embedding-3-small dimension
        self.dimension = 1536
        
        if not self.pc.has_index(self.index_name):
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        self.index = self.pc.Index(self.index_name)
        
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks suitable for embedding"""
        logger.info(f"Chunking text of length {len(text)}")
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        while start < len(text):
            # Find a good break point (sentence end or paragraph)
            end = min(start + chunk_size, len(text))
            
            # Try to end at sentence boundary if within the overlap
            if end < len(text):
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('\n\n', start, end)
                )
                
                if sentence_end > start + (chunk_size - overlap):
                    end = sentence_end + 2  # Include the period and space
            
            chunks.append(text[start:end])
            start = end - overlap
        
        logger.info(f"Text split into {len(chunks)} chunks")    
        return chunks
                
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding using OpenAI text-embedding-3-small"""
        try:
            logger.info(f"Creating embedding for text (length: {len(text)}) starting with: {text[:50]}...")
            
            response = await self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            
            embedding_vector = response.data[0].embedding
            
            logger.info(f"Successfully created embedding of dimension {len(embedding_vector)}")
            return embedding_vector
            
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            # Use random non-zero vector instead of all zeros to avoid Pinecone errors
            random_vector = [random.uniform(0.01, 0.1) for _ in range(self.dimension)]
            logger.warning("Returning random non-zero vector as fallback due to error")
            return random_vector

    async def store_meeting_data(self, meeting_data: Dict[str, Any], user_id: str):
        """Store meeting data in Pinecone using chunking for large transcripts and user_id for namespace"""
        try:
            if not user_id:
                raise ValueError("user_id is required for storing meeting data")

            # Create base metadata common to all chunks
            base_metadata = {
                "meeting_id": meeting_data.get("id", "meet_20250407_152504_89f13387"),
                "title": meeting_data.get("title", "Untitled Meeting"),
                "date": meeting_data.get("date", ""),
                # Use speakers instead of participants, with empty list fallback
                "participants": meeting_data.get("speakers", []) or [],
                "summary": meeting_data.get("ai_summary", ""),
                "action_items": json.dumps(meeting_data.get("action_items", [])),
                "main_topics": json.dumps(meeting_data.get("main_topics", [])),
                "insights": json.dumps(meeting_data.get("insights", []))
            }
            logger.info(f"Base metadata: {base_metadata}")
            
            # Get full transcript
            transcript = meeting_data.get("transcript", "")
            if not transcript:
                logger.warning("No transcript found in meeting data")
                transcript = "No transcript available"
            
            # Chunk the transcript
            logger.info("Starting transcript chunking")
            chunks = self._chunk_text(transcript)
            logger.info(f"Split transcript into {len(chunks)} chunks")
            
            # Batch vectors for upsert
            vectors_to_upsert = []
            
            # Store only up to 5 chunks for testing to prevent overload
            max_chunks = min(5, len(chunks))
            logger.info(f"Processing {max_chunks} chunks (limited for testing)")
            
            # Store chunks with embeddings
            for i in range(max_chunks):
                chunk = chunks[i]
                logger.info(f"Processing chunk {i+1}/{max_chunks}")
                
                # Create embedding for this chunk
                logger.info(f"Creating embedding for chunk {i}")
                chunk_embedding = await self.create_embedding(chunk)
                logger.info(f"Created embedding for chunk {i}")
                
                # Create chunk-specific metadata
                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["chunk_count"] = len(chunks)
                chunk_metadata["chunk_text"] = chunk[:500]  # Store limited preview of the chunk
                
                # Add to upsert batch
                vectors_to_upsert.append({
                    "id": f"meeting_{base_metadata['meeting_id']}_chunk_{i}",
                    "values": chunk_embedding,
                    "metadata": chunk_metadata
                })
                
                # Add a small delay to prevent rate limiting
                time.sleep(0.5)
            
            # Store summary embedding separately for high-level search
            if meeting_data.get("ai_summary"):
                logger.info("Creating embedding for summary")
                summary_embedding = await self.create_embedding(meeting_data["ai_summary"])
                logger.info("Successfully created embedding for summary")
                
                summary_metadata = base_metadata.copy()
                summary_metadata["content_type"] = "summary"
                
                vectors_to_upsert.append({
                    "id": f"meeting_{base_metadata['meeting_id']}_summary",
                    "values": summary_embedding,
                    "metadata": summary_metadata
                })
            
            # Upsert in smaller batches to prevent timeouts
            batch_size = 2  # Smaller batch size for testing
            logger.info(f"Upserting vectors in batches of {batch_size}")
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                logger.info(f"Upserting batch {i//batch_size + 1}/{(len(vectors_to_upsert) + batch_size - 1)//batch_size}")
                
                try:
                    self.index.upsert(
                        vectors=batch,
                        namespace=user_id  # Use user_id as namespace
                    )
                    logger.info(f"Successfully upserted batch {i//batch_size + 1} to namespace {user_id}")
                except Exception as e:
                    logger.error(f"Error upserting batch {i//batch_size + 1}: {str(e)}")
                
                # Add delay between batches to prevent rate limiting
                time.sleep(1)
            
            logger.info(f"Completed storing meeting {base_metadata['meeting_id']} with {len(vectors_to_upsert)} vectors in Pinecone namespace {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing meeting data: {str(e)}")
            raise

    async def search_meetings(self, query: str, user_id: str, meeting_id: str = None, top_k: int = 5) -> List[Dict]:
        """Search meetings based on query, constrained to user_id namespace"""
        try:
            if not user_id:
                raise ValueError("user_id is required for searching meetings")
                
            query_embedding = await self.create_embedding(query)
            
            filter_dict = {}
            if meeting_id:
                filter_dict["meeting_id"] = meeting_id
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=user_id,
                filter=filter_dict if filter_dict else None
            )
            
            return results.matches
            
        except Exception as e:
            logger.error(f"Error searching meetings: {str(e)}")
            raise
            
    async def generate_rag_response(self, query: str, llm_service, user_id: str, meeting_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Generate a RAG-based response to a query about meetings
        
        Args:
            query: The user's question
            llm_service: An instance of LLMService to use for generation
            user_id: The user ID to namespace the search
            meeting_id: Optional meeting ID to filter results
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Dictionary with response and source information
        """
        try:
            # Step 1: Retrieve relevant meeting chunks
            search_results = await self.search_meetings(query, user_id, meeting_id, top_k=top_k)
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant meeting information for your query.",
                    "sources": []
                }
            
            # Step 2: Prepare context from search results
            context_chunks = []
            sources = []
            meeting_metadata = {}
            
            # First pass to gather all metadata about meetings
            for result in search_results:
                metadata = result.metadata
                meeting_id_meta = metadata.get("meeting_id")
                
                if meeting_id_meta and meeting_id_meta not in meeting_metadata:
                    meeting_metadata[meeting_id_meta] = {
                        "meeting_id": meeting_id_meta,
                        "title": metadata.get("title", "Untitled Meeting"),
                        "date": metadata.get("date", "Unknown date"),
                        "participants": metadata.get("participants", []),
                        "summary": metadata.get("summary", ""),
                        "transcript_preview": metadata.get("transcript_preview", ""),
                        "score": result.score,
                        "chunks": []
                    }
                    
                    # Try to parse action items, topics and insights if available
                    try:
                        if "action_items" in metadata:
                            meeting_metadata[meeting_id_meta]["action_items"] = json.loads(metadata.get("action_items", "[]"))
                    except:
                        meeting_metadata[meeting_id_meta]["action_items"] = []
                        
                    try:
                        if "main_topics" in metadata:
                            meeting_metadata[meeting_id_meta]["main_topics"] = json.loads(metadata.get("main_topics", "[]"))
                    except:
                        meeting_metadata[meeting_id_meta]["main_topics"] = []
                        
                    try:
                        if "insights" in metadata:
                            meeting_metadata[meeting_id_meta]["insights"] = json.loads(metadata.get("insights", "[]"))
                    except:
                        meeting_metadata[meeting_id_meta]["insights"] = []
                
                # Add the chunk text to the meeting data
                if meeting_id_meta and "chunk_text" in metadata:
                    meeting_metadata[meeting_id_meta]["chunks"].append({
                        "text": metadata.get("chunk_text", ""),
                        "score": result.score,
                        "index": metadata.get("chunk_index", 0)
                    })
            
            # Second pass to build formatted context
            for mid, meeting in meeting_metadata.items():
                # Add to sources list for return value
                source = {
                    "meeting_id": meeting["meeting_id"],
                    "title": meeting["title"],
                    "date": meeting["date"],
                    "score": meeting["score"]
                }
                sources.append(source)
                
                # Build rich context for this meeting
                meeting_context = [
                    f"Meeting: {meeting['title']} (ID: {meeting['meeting_id']})",
                    f"Date: {meeting['date']}",
                ]
                
                if meeting.get("participants"):
                    if isinstance(meeting["participants"], list):
                        meeting_context.append(f"Participants: {', '.join(meeting['participants'])}")
                    else:
                        meeting_context.append(f"Participants: {meeting['participants']}")
                
                if meeting.get("summary"):
                    meeting_context.append(f"Summary: {meeting['summary']}")
                
                # Add action items if available
                if meeting.get("action_items") and len(meeting["action_items"]) > 0:
                    action_items = meeting["action_items"]
                    if isinstance(action_items, list) and len(action_items) > 0:
                        meeting_context.append("Action Items:")
                        for item in action_items:
                            meeting_context.append(f"- {item}")
                
                # Add main topics if available
                if meeting.get("main_topics") and len(meeting["main_topics"]) > 0:
                    topics = meeting["main_topics"]
                    if isinstance(topics, list) and len(topics) > 0:
                        meeting_context.append("Main Topics:")
                        for topic in topics:
                            meeting_context.append(f"- {topic}")
                
                # Add insights if available
                if meeting.get("insights") and len(meeting["insights"]) > 0:
                    insights = meeting["insights"]
                    if isinstance(insights, list) and len(insights) > 0:
                        meeting_context.append("Insights:")
                        for insight in insights:
                            meeting_context.append(f"- {insight}")
                
                # Add transcript excerpts
                if meeting.get("chunks") and len(meeting["chunks"]) > 0:
                    # Sort chunks by index
                    sorted_chunks = sorted(meeting["chunks"], key=lambda x: x.get("index", 0))
                    
                    # Add the first 2 highest scoring chunks
                    best_chunks = sorted(meeting["chunks"], key=lambda x: x.get("score", 0), reverse=True)[:2]
                    if best_chunks:
                        meeting_context.append("Relevant Transcript Excerpts:")
                        for chunk in best_chunks:
                            meeting_context.append(f"[Excerpt] {chunk['text']}")
                
                # Add the complete context for this meeting to the overall context
                context_chunks.append("\n".join(meeting_context))
            
            # Step 3: Generate response
            context = "\n\n---\n\n".join(context_chunks)
            
            system_prompt = """You are a helpful assistant with access to a knowledge base of meeting transcripts and summaries.
Your task is to answer questions based on the context provided below.

Important instructions:
1. Base your answer ONLY on the provided context.
2. If the specific information asked for is not in the context, say so clearly - don't make up information.
3. Focus on providing direct, factual answers based on the meeting data.
4. If asked about specific meeting insights, action items, or topics, provide those exactly as they appear in the context.
5. If a specific meeting ID is mentioned in the query, prioritize information from that meeting.
6. For queries about opinions or summaries, stick to what's stated in the meeting records.
7. References to "AI insights" should be understood as referring to the insights already extracted from the meeting."""

            user_prompt = f"""
Context from meeting knowledge base:
{context}

User question: {query}

Please provide a comprehensive answer based only on the information in the context above.
"""

            # Call LLM to generate the response
            answer = await llm_service.get_text_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            return {
                "answer": answer,
                "sources": sources[:3]  # Limit to top 3 sources
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return {
                "answer": f"I encountered an error while searching the meeting knowledge base: {str(e)}",
                "sources": []
            }