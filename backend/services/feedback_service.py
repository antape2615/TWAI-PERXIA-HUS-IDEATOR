import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import uuid

@dataclass
class FeedbackEntry:
    """Estructura para almacenar feedback de una interacción"""
    id: str
    conversation_id: str
    timestamp: str
    user_message: str
    assistant_response: str
    rating: Optional[float] = None  # 1-5 o None
    is_correct: Optional[bool] = None
    error_description: Optional[str] = None
    correction: Optional[str] = None
    feedback_text: Optional[str] = None
    hu_generated: Optional[str] = None  # Si fue generación de HU
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class FeedbackService:
    """Servicio para almacenar y recuperar feedback de usuarios"""
    
    def __init__(self, storage_path: str = "data/feedback"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Archivos de almacenamiento
        self.feedback_file = os.path.join(storage_path, "feedback.jsonl")
        self.learning_file = os.path.join(storage_path, "learning_data.jsonl")
        self.statistics_file = os.path.join(storage_path, "statistics.json")
        
        # Caché en memoria para estadísticas
        self._statistics_cache = None
    
    def _load_statistics(self) -> Dict:
        """Carga estadísticas de feedback"""
        if self._statistics_cache is not None:
            return self._statistics_cache
        
        if os.path.exists(self.statistics_file):
            try:
                with open(self.statistics_file, 'r', encoding='utf-8') as f:
                    self._statistics_cache = json.load(f)
                    return self._statistics_cache
            except:
                pass
        
        # Inicializar estadísticas vacías
        stats = {
            "total_feedback": 0,
            "total_ratings": 0,
            "average_rating": 0.0,
            "total_errors_reported": 0,
            "total_corrections": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "last_updated": None
        }
        self._statistics_cache = stats
        return stats
    
    def _save_statistics(self, stats: Dict):
        """Guarda estadísticas"""
        stats["last_updated"] = datetime.now().isoformat()
        with open(self.statistics_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        self._statistics_cache = stats
    
    def save_feedback(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        rating: Optional[float] = None,
        is_correct: Optional[bool] = None,
        error_description: Optional[str] = None,
        correction: Optional[str] = None,
        feedback_text: Optional[str] = None,
        hu_generated: Optional[str] = None
    ) -> str:
        """Guarda feedback de una interacción"""
        feedback_id = str(uuid.uuid4())
        
        feedback = FeedbackEntry(
            id=feedback_id,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            assistant_response=assistant_response,
            rating=rating,
            is_correct=is_correct,
            error_description=error_description,
            correction=correction,
            feedback_text=feedback_text,
            hu_generated=hu_generated
        )
        
        # Guardar en JSONL (línea por línea para fácil procesamiento)
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback.to_dict(), ensure_ascii=False) + '\n')
        
        # Actualizar estadísticas
        stats = self._load_statistics()
        stats["total_feedback"] += 1
        
        if rating is not None:
            stats["total_ratings"] += 1
            # Calcular promedio
            if stats["total_ratings"] == 1:
                stats["average_rating"] = rating
            else:
                current_avg = stats["average_rating"]
                total = stats["total_ratings"]
                stats["average_rating"] = ((current_avg * (total - 1)) + rating) / total
        
        if error_description is not None or (is_correct is not None and not is_correct):
            stats["total_errors_reported"] += 1
        
        if correction is not None:
            stats["total_corrections"] += 1
        
        if is_correct is True or (rating is not None and rating >= 4):
            stats["positive_feedback"] += 1
        elif is_correct is False or (rating is not None and rating < 3):
            stats["negative_feedback"] += 1
        
        self._save_statistics(stats)
        
        return feedback_id
    
    def get_feedback_by_conversation(self, conversation_id: str) -> List[FeedbackEntry]:
        """Obtiene todo el feedback de una conversación"""
        feedback_list = []
        
        if not os.path.exists(self.feedback_file):
            return feedback_list
        
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("conversation_id") == conversation_id:
                            feedback_list.append(FeedbackEntry.from_dict(data))
                    except:
                        continue
        
        return feedback_list
    
    def get_all_feedback(self, limit: Optional[int] = None) -> List[FeedbackEntry]:
        """Obtiene todo el feedback (útil para análisis)"""
        feedback_list = []
        
        if not os.path.exists(self.feedback_file):
            return feedback_list
        
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        feedback_list.append(FeedbackEntry.from_dict(data))
                    except:
                        continue
        
        # Ordenar por timestamp (más reciente primero)
        feedback_list.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            return feedback_list[:limit]
        
        return feedback_list
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de feedback"""
        return self._load_statistics()
    
    def get_learning_examples(self, min_rating: float = 3.0, limit: int = 100) -> List[Dict]:
        """Obtiene ejemplos para aprendizaje (respuestas bien calificadas)"""
        examples = []
        
        if not os.path.exists(self.feedback_file):
            return examples
        
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        # Incluir ejemplos con buena calificación o correcciones
                        if (data.get("rating", 0) >= min_rating) or (data.get("correction") is not None):
                            examples.append(data)
                    except:
                        continue
        
        # Ordenar por rating (mejores primero) o por timestamp si hay correcciones
        examples.sort(key=lambda x: (
            x.get("rating", 0) if x.get("correction") is None else 5,
            x.get("timestamp", "")
        ), reverse=True)
        
        return examples[:limit]
    
    def get_error_patterns(self) -> List[Dict]:
        """Analiza patrones de errores reportados"""
        errors = []
        
        if not os.path.exists(self.feedback_file):
            return errors
        
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("error_description") or (data.get("is_correct") is False):
                            errors.append({
                                "user_message": data.get("user_message", ""),
                                "assistant_response": data.get("assistant_response", ""),
                                "error_description": data.get("error_description", ""),
                                "correction": data.get("correction", ""),
                                "timestamp": data.get("timestamp", "")
                            })
                    except:
                        continue
        
        return errors

