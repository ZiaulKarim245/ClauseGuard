"""
Chat Service - Business logic for routing and processing conversational legal queries.
"""
from typing import List, Optional
from langsmith import traceable
from src.llm.agents.research_agent import researcher_agent_invoke
from src.llm.agents.statute_agent import fact_check_with_google
from src.llm.agents.rag_agent import answer_from_documents 
from src.llm.agents.vision_agent import vision_agent_invoke 

class ChatService:
    """
    Orchestrates the selection and execution of specialized AI agents based on the query type.
    """
    @staticmethod
    @traceable(name="Conversational_Legal_Interface", run_type="chain")
    async def process_chat(
        query: str, 
        agent_type: str,
        image_base64: Optional[str] = None,
        chat_history: List = [],
        filename: Optional[str] = None
    ) -> dict:
        """
        Routes the user query to the appropriate agent persona and returns a formatted response.
        """
        # --- Precedent Research Branch ---
        if agent_type == "researcher":
            inputs = {"messages": [("user", query)]}
            result = researcher_agent_invoke(inputs)
            clean_text = result["messages"][-1].content
            if isinstance(clean_text, list):
                clean_text = clean_text[0].get("text", "")
            return {"agent": "Researcher", "reply": clean_text}

        # --- Statute Verification Branch ---
        elif agent_type == "fact_checker":
            result = fact_check_with_google(query)
            return {"agent": "Search (Google)", "reply": result}
        
        # --- Document Context (RAG) Branch ---
        elif agent_type == "rag_agent":
            result = answer_from_documents(query, chat_history, filename=filename)
            return {
                "agent": "RAG (Document Intelligence)", 
                "reply": result.get("reply", "No reply generated."),
                "citations": result.get("citations", []) 
            }  
            
        # --- Multimodal Vision Branch ---
        elif agent_type == "vision_agent":
            if not image_base64:
                raise ValueError("Vision Agent requires an image context.")
            result = vision_agent_invoke(query, image_base64)
            return {
                "agent": "Vision Analyst", 
                "reply": result.get("reply"),
                "citations": result.get("citations")
            }         
        
        else:
            raise ValueError(f"Unsupported agent type requested: {agent_type}")
