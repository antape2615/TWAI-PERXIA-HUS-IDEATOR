from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import uvicorn

from services.azure_openai_service import AzureOpenAIService
from services.azure_devops_service import AzureDevOpsService
from services.conversation_service import ConversationService
from services.feedback_service import FeedbackService
from services.learning_service import LearningService

load_dotenv()

app = FastAPI(title="HU Generator API", version="1.0.0")

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
from services.knowledge_base_service import KnowledgeBaseService

feedback_service = FeedbackService()
learning_service = LearningService(feedback_service)
knowledge_base_service = KnowledgeBaseService()
openai_service = AzureOpenAIService(learning_service=learning_service)
devops_service = AzureDevOpsService()
conversation_service = ConversationService(openai_service, knowledge_base_service)


# Request/Response Models
class RequirementRequest(BaseModel):
    requirement: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class QuestionResponse(BaseModel):
    has_questions: bool
    questions: List[str]
    conversation_id: str
    message: str


class GenerateHURequest(BaseModel):
    requirement: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    conversation_id: str


class GenerateHUResponse(BaseModel):
    hu_content: str
    conversation_id: str
    requires_review: bool = True


class CreateWorkItemRequest(BaseModel):
    hu_content: str
    title: str
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None


class CreateWorkItemResponse(BaseModel):
    work_item_id: int
    url: str
    success: bool


class FeedbackRequest(BaseModel):
    conversation_id: str
    user_message: str
    assistant_response: str
    rating: Optional[float] = None  # 1-5
    is_correct: Optional[bool] = None
    error_description: Optional[str] = None
    correction: Optional[str] = None
    feedback_text: Optional[str] = None
    hu_generated: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    message: str
    success: bool


class PerformanceAnalysisResponse(BaseModel):
    total_interactions: int
    average_rating: float
    satisfaction_rate: float
    error_rate: float
    common_errors: List[str]
    improvement_areas: List[str]


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Start conversation and get questions if needed
@app.post("/api/conversation/start", response_model=QuestionResponse)
async def start_conversation(request: RequirementRequest):
    """Inicia una conversación y determina si se necesitan más preguntas"""
    try:
        result = await conversation_service.start_conversation(
            request.requirement,
            request.conversation_history
        )
        return QuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Continue conversation with answers
@app.post("/api/conversation/continue", response_model=QuestionResponse)
async def continue_conversation(request: RequirementRequest):
    """Continúa la conversación con respuestas del usuario"""
    try:
        result = await conversation_service.continue_conversation(
            request.requirement,
            request.conversation_history
        )
        return QuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Generate HU from requirement
@app.post("/api/hu/generate", response_model=GenerateHUResponse)
async def generate_hu(request: GenerateHURequest):
    """Genera una Historia de Usuario completa basada en el requerimiento"""
    try:
        conversation_id = request.conversation_id or conversation_service.generate_conversation_id()
        
        # Get related HUs from conversation context
        related_hus = []
        if conversation_id in conversation_service.conversations:
            related_hus = conversation_service.conversations[conversation_id].get("related_hus", [])
        
        hu_content = await openai_service.generate_hu(
            request.requirement,
            request.conversation_history,
            related_hus=related_hus
        )
        
        # Store conversation state for potential feedback
        if conversation_id in conversation_service.conversations:
            conversation_service.conversations[conversation_id]["last_assistant_response"] = hu_content
            conversation_service.conversations[conversation_id]["hu_content"] = hu_content
            # Get last user message from history
            user_messages = [msg for msg in request.conversation_history if msg.get("role") == "user"]
            if user_messages:
                conversation_service.conversations[conversation_id]["last_user_message"] = user_messages[-1].get("content", request.requirement)
        
        return GenerateHUResponse(
            hu_content=hu_content,
            conversation_id=conversation_id,
            requires_review=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating HU: {str(e)}")


# Get available work item types from Azure DevOps
@app.get("/api/devops/work-item-types")
async def get_work_item_types():
    """Obtiene los tipos de work items disponibles en el proyecto de Azure DevOps"""
    try:
        work_item_types = await devops_service.get_work_item_types()
        current_type = os.getenv("AZURE_DEVOPS_WORK_ITEM_TYPE", "User Story")
        return {
            "available_types": work_item_types,
            "current_type": current_type,
            "message": f"Tipos de work items disponibles en tu proyecto. Actualmente configurado: '{current_type}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting work item types: {str(e)}")


# Get available fields for a work item type
@app.get("/api/devops/work-item-fields")
async def get_work_item_fields(work_item_type: Optional[str] = None):
    """Obtiene los campos disponibles para un tipo de work item"""
    try:
        fields = await devops_service.get_work_item_fields(work_item_type)
        return {
            "fields": fields,
            "count": len(fields)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting work item fields: {str(e)}")


# Create work item in Azure DevOps
@app.post("/api/devops/create-work-item", response_model=CreateWorkItemResponse)
async def create_work_item(request: CreateWorkItemRequest):
    """Crea un work item (User Story) en Azure DevOps"""
    try:
        # Default assigned_to if not provided
        assigned_to = request.assigned_to or os.getenv("AZURE_DEVOPS_DEFAULT_ASSIGNED_TO", "angiepena@cbit-online.com")
        
        result = await devops_service.create_user_story(
            title=request.title,
            description=request.hu_content,
            area_path=request.area_path,
            iteration_path=request.iteration_path,
            tags=request.tags,
            assigned_to=assigned_to
        )
        
        # Save HU to knowledge base after successful creation
        if result.get("success"):
            try:
                # Extract requirement from conversation (if available)
                # For now, use title as a simple requirement
                requirement = request.title
                
                # Generate HU ID
                hu_id = f"HU-{result['work_item_id']}"
                
                knowledge_base_service.add_hu(
                    hu_id=hu_id,
                    title=request.title,
                    content=request.hu_content,
                    requirement=requirement,
                    tags=request.tags,
                    work_item_id=result['work_item_id'],
                    work_item_url=result.get('url')
                )
            except Exception as kb_error:
                # Log error but don't fail the request
                import logging
                logging.error(f"Error saving to knowledge base: {kb_error}")
        
        return CreateWorkItemResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating work item: {str(e)}")


# Submit feedback (rating, error report, correction)
@app.post("/api/feedback/submit", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Envía feedback sobre una respuesta del sistema (rating, error, corrección)"""
    try:
        feedback_id = feedback_service.save_feedback(
            conversation_id=request.conversation_id,
            user_message=request.user_message,
            assistant_response=request.assistant_response,
            rating=request.rating,
            is_correct=request.is_correct,
            error_description=request.error_description,
            correction=request.correction,
            feedback_text=request.feedback_text,
            hu_generated=request.hu_generated
        )
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            message="Feedback guardado exitosamente. Gracias por ayudarnos a mejorar.",
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")


# Get feedback statistics
@app.get("/api/feedback/statistics")
async def get_feedback_statistics():
    """Obtiene estadísticas de feedback"""
    try:
        stats = feedback_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


# Get performance analysis
@app.get("/api/learning/performance", response_model=PerformanceAnalysisResponse)
async def get_performance_analysis():
    """Obtiene análisis de desempeño del sistema"""
    try:
        analysis = learning_service.analyze_performance()
        return PerformanceAnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing performance: {str(e)}")


# Get feedback for a conversation
@app.get("/api/feedback/conversation/{conversation_id}")
async def get_conversation_feedback(conversation_id: str):
    """Obtiene todo el feedback asociado a una conversación"""
    try:
        feedback_list = feedback_service.get_feedback_by_conversation(conversation_id)
        return {
            "conversation_id": conversation_id,
            "feedback_count": len(feedback_list),
            "feedback": [f.to_dict() for f in feedback_list]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feedback: {str(e)}")


# Knowledge Base endpoints
@app.get("/api/knowledge-base/search")
async def search_knowledge_base(query: str, min_relevance: float = 0.3, max_results: int = 5):
    """Busca HUs relacionadas en la base de conocimiento"""
    try:
        results = knowledge_base_service.search_related_hus(query, min_relevance, max_results)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching knowledge base: {str(e)}")


@app.get("/api/knowledge-base/hu/{hu_id}")
async def get_hu_from_knowledge_base(hu_id: str):
    """Obtiene el contenido completo de una HU de la base de conocimiento"""
    try:
        hu_content = knowledge_base_service.get_hu_content(hu_id)
        if not hu_content:
            raise HTTPException(status_code=404, detail=f"HU {hu_id} not found")
        return hu_content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting HU: {str(e)}")


@app.get("/api/knowledge-base/statistics")
async def get_knowledge_base_statistics():
    """Obtiene estadísticas de la base de conocimiento"""
    try:
        stats = knowledge_base_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@app.get("/api/knowledge-base/all")
async def get_all_hus():
    """Obtiene lista de todas las HUs en la base de conocimiento"""
    try:
        hus = knowledge_base_service.get_all_hus()
        return {
            "hus": hus,
            "count": len(hus)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting HUs: {str(e)}")


# Serve frontend (for Render / single-service deployments)
_FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
)
_FRONTEND_INDEX = os.path.join(_FRONTEND_DIR, "index.html")

if os.path.isdir(_FRONTEND_DIR) and os.path.isfile(_FRONTEND_INDEX):
    @app.get("/")
    async def serve_frontend_index():
        return FileResponse(_FRONTEND_INDEX)

    # Mount after API routes so `/api/*` keeps working
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import sys
    import os
    # Add parent directory to path to allow imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    port = int(os.getenv("PORT", os.getenv("BACKEND_PORT", 8000)))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)

