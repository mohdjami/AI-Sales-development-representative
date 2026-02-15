from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Union, Dict, Any
from dotenv import load_dotenv
import json
import os

from core.logger import logger

class LLMService:
    def __init__(self):
        load_dotenv()
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.logger = logger

    async def get_json_response(
        self, 
        system_prompt: str, 
        user_prompt: str,
        json_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get a JSON response from the LLM with proper error handling and formatting
        """
        try:
            prompt = [
                SystemMessage(content=f"""You are an AI assistant that ALWAYS responds in valid JSON format.
                Expected JSON structure:
                {json_structure}
                
                Important rules:
                - ONLY return valid JSON
                - Use double quotes for strings
                - Ensure proper escaping
                - No trailing commas
                - No comments
                
                Additional context:
                {system_prompt}"""),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(prompt)
            
            # Clean and parse response
            cleaned_response = response.content.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
            
            self.logger.debug(f"Raw LLM response: {cleaned_response}")
            return json.loads(cleaned_response)

        except Exception as e:
            self.logger.error(f"Error in LLM service: {str(e)}")
            raise

    async def get_streaming_response(self, prompt: List[Union[SystemMessage, HumanMessage]]):
        """
        Get a streaming response from the LLM
        
        Args:
            prompt: List of SystemMessage and/or HumanMessage objects
            
        Returns:
            An async generator that yields chunks of the response as they become available
        """
        try:
            # Use the astream method to get a streaming response
            stream = await self.llm.astream(prompt)
            
            # Yield each chunk as it becomes available
            async for chunk in stream:
                yield chunk.content
                
        except Exception as e:
            self.logger.error(f"Error in LLM streaming: {str(e)}")
            raise

    async def get_completion(self, prompt: List[Union[SystemMessage, HumanMessage]]):
        """
        Get a regular completion from the LLM
        """
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            self.logger.error(f"Error in LLM completion: {str(e)}")
            raise 
        
    async def invoke(self, prompt: str):
        """
        Get a regular response from the LLM
        """
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            self.logger.error(f"Error in LLM completion: {str(e)}")
            raise 

    async def get_text_response(self, system_prompt: str, user_prompt: str) -> str:
        """Get a plain text response from the LLM"""
        try:
            # Create the message objects
            messages = [
                HumanMessage(content=user_prompt),
            ]
            
            if system_prompt:
                messages.insert(0, SystemMessage(content=system_prompt))
            
            # Use the existing llm instance
            response = await self.llm.ainvoke(messages)
            
            # Return just the text content
            return response.content
        
        except Exception as e:
            self.logger.error(f"Error getting text response from LLM: {str(e)}")
            return f"Error: {str(e)}"
