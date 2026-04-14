import os
from openai import AzureOpenAI
from typing import List, Dict, Optional
import uuid
from services.learning_service import LearningService

class AzureOpenAIService:
    def __init__(self, learning_service: Optional[LearningService] = None):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key must be set in environment variables")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        
        # Learning service para mejorar prompts
        self.learning_service = learning_service
        
        # Load prompt template
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the prompt template from Prompt.md"""
        from services.prompt_loader import PromptLoader
        self.prompt_template = PromptLoader.load_prompt_template()
    
    def _build_conversation_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """Build conversation context from history"""
        if not conversation_history:
            return ""
        
        context = "\n\nContexto de la conversación:\n"
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                context += f"Usuario: {content}\n"
            elif role == "assistant":
                context += f"Asistente: {content}\n"
        
        return context
    
    async def generate_hu(
        self, 
        requirement: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        related_hus: Optional[List[Dict]] = None
    ) -> str:
        """Generate a complete User Story based on the requirement"""
        conversation_history = conversation_history or []
        
        # Build the full prompt
        conversation_context = self._build_conversation_context(conversation_history)
        
        # Add related HUs context
        related_context = ""
        if related_hus:
            related_context = "\n\n📚 HISTORIAS DE USUARIO RELACIONADAS (para referencia y consistencia):\n"
            for i, hu in enumerate(related_hus, 1):
                related_context += f"\n{i}. {hu['title']}"
                if hu.get('work_item_id'):
                    related_context += f" (Work Item #{hu['work_item_id']})"
                related_context += f"\n   Requerimiento original: {hu['requirement'][:200]}..."
                related_context += f"\n   Relevancia: {hu['relevance']:.0%}\n"
            related_context += "\nUsa estas HUs como referencia para mantener consistencia en terminología, estructura y nivel de detalle.\n"
        
        # Mejorar prompt con aprendizaje si está disponible
        enhanced_prompt = self.prompt_template
        if self.learning_service:
            enhanced_prompt = self.learning_service.enhance_prompt_with_learning(
                self.prompt_template,
                conversation_history,
                context=requirement
            )
        
        full_prompt = f"""{enhanced_prompt}

{related_context}

{conversation_context}

REQUERIMIENTO:
{requirement}

Por favor, genera la Historia de Usuario completa siguiendo el formato especificado en el prompt anterior."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un Analista Funcional Senior experto en crear Historias de Usuario completas y detalladas."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            hu_content = response.choices[0].message.content
            return hu_content
        except Exception as e:
            raise Exception(f"Error calling Azure OpenAI: {str(e)}")
    
    async def analyze_requirement(
        self, 
        requirement: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        related_hus: Optional[List[Dict]] = None
    ) -> Dict:
        """Analyze requirement and determine if more information is needed"""
        conversation_history = conversation_history or []
        conversation_context = self._build_conversation_context(conversation_history)
        
        # Add related HUs context
        related_context = ""
        if related_hus:
            related_context = "\n\nHISTORIAS DE USUARIO RELACIONADAS encontradas en la base de conocimiento:\n"
            for i, hu in enumerate(related_hus, 1):
                related_context += f"{i}. {hu['title']} (Relevancia: {hu['relevance']:.0%})\n"
                related_context += f"   Requerimiento: {hu['requirement'][:150]}...\n"
            related_context += "\nConsidera estas HUs relacionadas al analizar el requerimiento. Si hay información similar o relacionada, es posible que necesites hacer menos preguntas.\n"
        
        analysis_prompt = f"""Analiza el siguiente requerimiento y determina si falta información crítica para generar una Historia de Usuario completa.

{related_context}

{conversation_context}

REQUERIMIENTO:
{requirement}

Responde en formato JSON con la siguiente estructura:
{{
    "needs_clarification": true/false,
    "missing_info": ["item1", "item2", ...],
    "questions": ["pregunta1", "pregunta2", ...],
    "confidence": "alta/media/baja",
    "summary": "resumen breve del requerimiento"
}}

Si needs_clarification es true, proporciona preguntas específicas que ayuden a obtener la información faltante.
IMPORTANTE: Si hay HUs relacionadas que cubren aspectos similares, reduce las preguntas y enfócate solo en lo específico de este nuevo requerimiento."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un analista experto en revisar requerimientos y detectar información faltante."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except Exception as e:
            # Fallback if JSON parsing fails
            return {
                "needs_clarification": False,
                "missing_info": [],
                "questions": [],
                "confidence": "media",
                "summary": "Error en el análisis",
                "error": str(e)
            }
    
    async def continue_analysis(self, requirement: str, conversation_history: List[Dict[str, str]]) -> Dict:
        """Continue analysis after user provides answers"""
        conversation_context = self._build_conversation_context(conversation_history)
        
        continue_prompt = f"""Basándote en la conversación previa, analiza si aún falta información para generar la Historia de Usuario.

{conversation_context}

REQUERIMIENTO ORIGINAL:
{requirement}

Responde en formato JSON:
{{
    "needs_clarification": true/false,
    "questions": ["pregunta1", "pregunta2", ...],
    "ready_to_generate": true/false,
    "summary": "resumen del estado actual"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un analista que revisa requerimientos y determina cuándo hay suficiente información."},
                    {"role": "user", "content": continue_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except Exception as e:
            return {
                "needs_clarification": False,
                "questions": [],
                "ready_to_generate": True,
                "summary": "Error en el análisis, procediendo con generación",
                "error": str(e)
            }

