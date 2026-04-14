from typing import List, Dict, Optional
import uuid
import logging
from services.azure_openai_service import AzureOpenAIService
from services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, openai_service: AzureOpenAIService, knowledge_base_service: Optional[KnowledgeBaseService] = None):
        self.openai_service = openai_service
        self.knowledge_base = knowledge_base_service or KnowledgeBaseService()
        self.conversations = {}  # In-memory storage for conversations
    
    def generate_conversation_id(self) -> str:
        """Generate a unique conversation ID"""
        return str(uuid.uuid4())
    
    async def start_conversation(self, requirement: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict:
        """Start a new conversation and analyze if questions are needed"""
        conversation_id = self.generate_conversation_id()
        conversation_history = conversation_history or []
        
        # Search for related HUs in knowledge base
        related_hus = self.knowledge_base.search_related_hus(requirement, min_relevance=0.3, max_results=3)
        
        logger.info(f"Found {len(related_hus)} related HUs for requirement")
        
        # Add related HUs context to the analysis
        context_info = ""
        if related_hus:
            context_info = "\n\n📚 **HUs relacionadas encontradas:**\n"
            for i, hu in enumerate(related_hus, 1):
                context_info += f"\n{i}. **{hu['title']}**"
                if hu.get('work_item_id'):
                    context_info += f" (Work Item #{hu['work_item_id']})"
                context_info += f"\n   - Relevancia: {hu['relevance']:.0%}"
                context_info += f"\n   - Palabras clave comunes: {', '.join(hu['common_keywords'][:5])}"
                if hu.get('work_item_url'):
                    context_info += f"\n   - [Ver en Azure DevOps]({hu['work_item_url']})"
        
        # Analyze the requirement with context from related HUs
        analysis = await self.openai_service.analyze_requirement(
            requirement, 
            conversation_history,
            related_hus=related_hus
        )
        
        has_questions = analysis.get("needs_clarification", False)
        questions = analysis.get("questions", [])
        
        # Store initial conversation state
        self.conversations[conversation_id] = {
            "requirement": requirement,
            "history": conversation_history,
            "questions_asked": [],
            "ready_to_generate": not has_questions,
            "last_user_message": requirement,
            "last_assistant_response": None,
            "related_hus": related_hus
        }
        
        message = analysis.get("summary", "Análisis completado")
        if related_hus:
            message += context_info
        
        if has_questions:
            message += f"\n\n❓ Necesitamos más información para generar la HU completa. Por favor, responde las siguientes preguntas:"
        else:
            message += "\n\n✅ El requerimiento parece completo. Puedes proceder a generar la Historia de Usuario."
        
        return {
            "has_questions": has_questions,
            "questions": questions,
            "conversation_id": conversation_id,
            "message": message,
            "related_hus": related_hus
        }
    
    async def continue_conversation(self, requirement: str, conversation_history: List[Dict[str, str]]) -> Dict:
        """Continue conversation after user answers questions"""
        # Analyze if more information is needed
        analysis = await self.openai_service.continue_analysis(requirement, conversation_history)
        
        has_questions = analysis.get("needs_clarification", False)
        questions = analysis.get("questions", [])
        ready_to_generate = analysis.get("ready_to_generate", False)
        
        # Generate conversation ID if not present
        conversation_id = self.generate_conversation_id()
        
        # Update conversation state
        self.conversations[conversation_id] = {
            "requirement": requirement,
            "history": conversation_history,
            "ready_to_generate": ready_to_generate,
            "last_user_message": conversation_history[-1].get("content", "") if conversation_history else "",
            "last_assistant_response": None
        }
        
        if has_questions:
            message = f"Aún necesitamos más información. Por favor, responde las siguientes preguntas:"
        else:
            message = "¡Perfecto! Ahora tenemos suficiente información. Puedes proceder a generar la Historia de Usuario."
        
        return {
            "has_questions": has_questions,
            "questions": questions,
            "conversation_id": conversation_id,
            "message": message,
            "ready_to_generate": ready_to_generate
        }

