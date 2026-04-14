import os
from typing import List, Dict, Optional
from services.feedback_service import FeedbackService
from services.prompt_loader import PromptLoader

class LearningService:
    """Servicio de aprendizaje que mejora prompts basándose en feedback"""
    
    def __init__(self, feedback_service: FeedbackService):
        self.feedback_service = feedback_service
        self.prompt_loader = PromptLoader()
        
    def enhance_prompt_with_learning(
        self,
        base_prompt: str,
        conversation_history: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> str:
        """Mejora el prompt base con ejemplos aprendidos del feedback"""
        
        # Obtener ejemplos de aprendizaje (buenas respuestas y correcciones)
        learning_examples = self.feedback_service.get_learning_examples(min_rating=3.5, limit=5)
        error_patterns = self.feedback_service.get_error_patterns()
        
        enhanced_prompt = base_prompt
        
        # Agregar contexto de errores comunes si hay
        if error_patterns:
            error_context = self._build_error_context(error_patterns[:3])  # Top 3 errores
            enhanced_prompt += f"\n\n## LECCIONES APRENDIDAS DE FEEDBACK PREVIO:\n{error_context}"
        
        # Agregar ejemplos positivos si hay
        if learning_examples:
            positive_examples = [ex for ex in learning_examples if ex.get("rating", 0) >= 4.0]
            if positive_examples:
                examples_context = self._build_examples_context(positive_examples[:2])  # Top 2 ejemplos
                enhanced_prompt += f"\n\n## EJEMPLOS DE BUENAS RESPUESTAS:\n{examples_context}"
        
        # Agregar correcciones si hay
        corrections = [ex for ex in learning_examples if ex.get("correction")]
        if corrections:
            corrections_context = self._build_corrections_context(corrections[:2])
            enhanced_prompt += f"\n\n## CORRECCIONES IMPORTANTES:\n{corrections_context}"
        
        return enhanced_prompt
    
    def _build_error_context(self, error_patterns: List[Dict]) -> str:
        """Construye contexto de errores comunes"""
        context = "Evita estos errores comunes que se han identificado:\n"
        for i, error in enumerate(error_patterns, 1):
            context += f"\n{i}. Error reportado:\n"
            context += f"   - Contexto: {error.get('user_message', '')[:100]}...\n"
            context += f"   - Problema: {error.get('error_description', '')}\n"
            if error.get('correction'):
                context += f"   - Corrección aplicada: {error.get('correction', '')[:200]}...\n"
        return context
    
    def _build_examples_context(self, examples: List[Dict]) -> str:
        """Construye contexto de ejemplos positivos"""
        context = "Sigue estos ejemplos de buenas respuestas:\n"
        for i, example in enumerate(examples, 1):
            context += f"\n{i}. Ejemplo:\n"
            context += f"   - Requerimiento: {example.get('user_message', '')[:150]}...\n"
            context += f"   - Respuesta exitosa: {example.get('assistant_response', '')[:200]}...\n"
        return context
    
    def _build_corrections_context(self, corrections: List[Dict]) -> str:
        """Construye contexto de correcciones"""
        context = "Cuando encuentres situaciones similares, aplica estas correcciones:\n"
        for i, correction in enumerate(corrections, 1):
            context += f"\n{i}. Corrección:\n"
            context += f"   - Situación: {correction.get('user_message', '')[:100]}...\n"
            context += f"   - Respuesta incorrecta: {correction.get('assistant_response', '')[:150]}...\n"
            context += f"   - Corrección: {correction.get('correction', '')}\n"
        return context
    
    def generate_improved_prompt_variant(
        self,
        original_prompt: str,
        specific_feedback: List[Dict]
    ) -> str:
        """Genera una variante mejorada del prompt basada en feedback específico"""
        # Esta función podría usar un LLM para generar mejoras al prompt
        # Por ahora, simplemente agregamos las lecciones aprendidas
        
        improved = original_prompt
        
        if specific_feedback:
            improvements = "\n\n## MEJORAS BASADAS EN FEEDBACK:\n"
            for feedback in specific_feedback:
                if feedback.get("correction"):
                    improvements += f"- {feedback['correction']}\n"
            
            improved += improvements
        
        return improved
    
    def analyze_performance(self) -> Dict:
        """Analiza el desempeño del sistema basándose en feedback"""
        stats = self.feedback_service.get_statistics()
        errors = self.feedback_service.get_error_patterns()
        
        analysis = {
            "total_interactions": stats.get("total_feedback", 0),
            "average_rating": stats.get("average_rating", 0.0),
            "satisfaction_rate": 0.0,
            "error_rate": 0.0,
            "common_errors": [],
            "improvement_areas": []
        }
        
        total = stats.get("total_feedback", 0)
        if total > 0:
            positive = stats.get("positive_feedback", 0)
            negative = stats.get("negative_feedback", 0)
            analysis["satisfaction_rate"] = (positive / total) * 100 if total > 0 else 0
            analysis["error_rate"] = (stats.get("total_errors_reported", 0) / total) * 100 if total > 0 else 0
        
        # Analizar errores comunes
        error_descriptions = [e.get("error_description", "") for e in errors if e.get("error_description")]
        if error_descriptions:
            # Contar palabras clave comunes en errores
            from collections import Counter
            words = []
            for desc in error_descriptions:
                words.extend(desc.lower().split())
            common_words = Counter(words).most_common(5)
            analysis["common_errors"] = [word for word, count in common_words]
        
        # Áreas de mejora basadas en feedback negativo
        if analysis["error_rate"] > 20:
            analysis["improvement_areas"].append("Reducir tasa de errores en respuestas")
        if analysis["average_rating"] < 3.5:
            analysis["improvement_areas"].append("Mejorar calidad general de respuestas")
        
        return analysis

