# Sistema de Aprendizaje y Reinforcement Learning

## Descripción General

El sistema incluye un módulo completo de aprendizaje automático que permite que el chatbot mejore continuamente basándose en el feedback de los usuarios. Este sistema implementa técnicas de **Reinforcement Learning** donde el usuario actúa como el "entrenador" que recompensa o corrige las respuestas del sistema.

## Arquitectura

### Componentes Principales

1. **FeedbackService** (`backend/services/feedback_service.py`)
   - Almacena feedback de usuarios en formato JSONL
   - Mantiene estadísticas agregadas
   - Proporciona ejemplos de aprendizaje y patrones de errores

2. **LearningService** (`backend/services/learning_service.py`)
   - Mejora prompts basándose en feedback
   - Construye contexto de errores comunes
   - Genera variantes mejoradas de prompts

3. **Integración con AzureOpenAIService**
   - Usa el LearningService para enriquecer prompts antes de generar respuestas
   - Incorpora lecciones aprendidas automáticamente

## Flujo de Aprendizaje

```
Usuario → Genera HU → Revisa → Califica/Reporta Error → FeedbackService → LearningService → Mejora Prompts → Próxima Generación
```

### 1. Captura de Feedback

Cuando un usuario interactúa con el sistema:
- El sistema genera una respuesta (HU, preguntas, etc.)
- El usuario puede calificar la respuesta (1-5 estrellas)
- El usuario puede reportar errores y proporcionar correcciones
- Todo este feedback se almacena en `backend/data/feedback.jsonl`

### 2. Procesamiento del Feedback

El `FeedbackService` procesa el feedback y:
- Actualiza estadísticas (calificación promedio, tasas de error, etc.)
- Categoriza feedback positivo vs negativo
- Extrae patrones de errores comunes
- Identifica ejemplos de buenas respuestas

### 3. Mejora de Prompts

El `LearningService` usa el feedback para:
- **Identificar Errores Comunes**: Analiza errores reportados y los agrega al prompt como "errores a evitar"
- **Incluir Ejemplos Positivos**: Usa respuestas bien calificadas como ejemplos a seguir
- **Aplicar Correcciones**: Incorpora correcciones sugeridas por usuarios

### 4. Aplicación en Próximas Generaciones

Cuando se genera una nueva HU o respuesta:
- El prompt base se enriquece con:
  - Lecciones aprendidas de feedback previo
  - Ejemplos de buenas respuestas
  - Correcciones importantes
  - Errores comunes a evitar

## Estructura de Datos

### FeedbackEntry

```python
{
    "id": "uuid",
    "conversation_id": "uuid",
    "timestamp": "2024-01-15T10:30:00",
    "user_message": "Mensaje original del usuario",
    "assistant_response": "Respuesta del asistente",
    "rating": 4.5,  # 1-5 o None
    "is_correct": true,  # true/false/None
    "error_description": "Descripción del error",
    "correction": "Corrección sugerida",
    "feedback_text": "Comentarios adicionales",
    "hu_generated": "HU generada completa"
}
```

### Estadísticas

```python
{
    "total_feedback": 50,
    "total_ratings": 45,
    "average_rating": 4.2,
    "total_errors_reported": 5,
    "total_corrections": 3,
    "positive_feedback": 40,
    "negative_feedback": 5,
    "last_updated": "2024-01-15T10:30:00"
}
```

## API Endpoints

### POST /api/feedback/submit

Envía feedback sobre una respuesta.

**Campos importantes:**
- `rating`: Calificación de 1-5 (opcional pero recomendado)
- `is_correct`: Si la respuesta fue correcta (opcional)
- `error_description`: Descripción de qué estuvo mal (opcional)
- `correction`: Cómo debería haber sido (opcional pero muy valioso)

### GET /api/feedback/statistics

Obtiene estadísticas agregadas de feedback.

### GET /api/learning/performance

Obtiene análisis de desempeño incluyendo:
- Tasa de satisfacción
- Tasa de errores
- Áreas de mejora identificadas

## Privacidad y Datos

- **Almacenamiento Local**: El feedback se almacena localmente en `backend/data/`
- **Sin Entrenamiento Automático**: El sistema NO envía tus conversaciones a Azure OpenAI para entrenamiento
- **Solo Feedback Explícito**: Solo se usa el feedback que explícitamente proporcionas
- **Datos Anonimizados**: El feedback no incluye información personal identificable

## Mejoras Futuras

1. **Fine-tuning de Modelos**: Usar feedback acumulado para fine-tune de modelos
2. **Análisis Avanzado**: ML para identificar patrones complejos en errores
3. **A/B Testing**: Probar diferentes versiones de prompts y medir resultados
4. **Personalización**: Aprender preferencias por usuario
5. **Dashboard Visual**: Interfaz para visualizar métricas de aprendizaje

## Uso Recomendado

Para obtener los mejores resultados del sistema de aprendizaje:

1. **Sé Específico**: Al reportar errores, describe exactamente qué estuvo mal
2. **Proporciona Correcciones**: Indica cómo debería haber sido la respuesta
3. **Califica Consistente**: Usa el sistema de calificación para ayudar al sistema a aprender
4. **Feedback Temprano**: Envía feedback incluso si la respuesta es correcta pero podría mejorar

El sistema aprende mejor cuando recibe feedback variado y específico sobre diferentes tipos de errores y situaciones.

