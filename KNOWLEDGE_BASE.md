# 📚 Base de Conocimiento de Historias de Usuario

## Descripción

El sistema incluye una **base de conocimiento** que almacena y aprende de todas las Historias de Usuario (HUs) creadas anteriormente. Esto permite:

✅ **Búsqueda inteligente** de HUs relacionadas antes de generar nuevas  
✅ **Reutilización de conocimiento** para mantener consistencia  
✅ **Reducción de preguntas** cuando hay contexto similar previo  
✅ **Referencias automáticas** a work items relacionados  

---

## ¿Cómo funciona?

### 1. **Almacenamiento automático**
Cada vez que creas un work item en Azure DevOps, la HU se guarda automáticamente en la base de conocimiento con:
- ID único (basado en el Work Item ID)
- Título y contenido completo
- Requerimiento original
- Keywords extraídas automáticamente
- Tags (si los proporcionaste)
- Referencia al Work Item en Azure DevOps

### 2. **Búsqueda inteligente**
Cuando inicias una nueva conversación:
- El sistema busca HUs relacionadas basándose en keywords
- Calcula relevancia usando similitud de Jaccard
- Muestra las HUs más relevantes (mínimo 30% de relevancia)
- Incluye enlaces directos a los work items en Azure DevOps

### 3. **Generación contextual**
Al generar una nueva HU:
- El sistema usa las HUs relacionadas como referencia
- Mantiene consistencia en terminología y estructura
- Reduce preguntas redundantes
- Sugiere patrones similares cuando aplica

---

## Endpoints de la API

### 🔍 Buscar HUs relacionadas
```http
GET /api/knowledge-base/search?query=libranza&min_relevance=0.3&max_results=5
```

**Respuesta:**
```json
{
  "query": "libranza",
  "results": [
    {
      "hu_id": "HU-52991",
      "title": "Creación de etapa automática Cierre Motor",
      "requirement": "...",
      "work_item_id": 52991,
      "work_item_url": "https://...",
      "relevance": 0.75,
      "common_keywords": ["libranza", "credito", "motor"]
    }
  ],
  "count": 1
}
```

### 📄 Obtener HU específica
```http
GET /api/knowledge-base/hu/HU-52991
```

**Respuesta:**
```json
{
  "hu_id": "HU-52991",
  "title": "...",
  "content": "...",
  "requirement": "...",
  "created_at": "2025-12-26T..."
}
```

### 📊 Estadísticas de la base de conocimiento
```http
GET /api/knowledge-base/statistics
```

**Respuesta:**
```json
{
  "total_hus": 15,
  "total_keywords": 250,
  "total_tags": 12,
  "top_keywords": [
    {"keyword": "libranza", "count": 8},
    {"keyword": "credito", "count": 6}
  ],
  "most_recent": {...}
}
```

### 📋 Listar todas las HUs
```http
GET /api/knowledge-base/all
```

---

## Almacenamiento

Los datos se guardan en: `backend/data/knowledge_base/`

### Estructura de archivos:
```
backend/data/knowledge_base/
├── hu_index.json          # Índice con metadata de todas las HUs
├── HU-52991.json         # Contenido completo de cada HU
├── HU-52992.json
└── ...
```

### Formato del índice (`hu_index.json`):
```json
[
  {
    "hu_id": "HU-52991",
    "title": "Creación de etapa automática...",
    "requirement": "Automatizar la activación...",
    "keywords": ["libranza", "credito", "motor", "automatico"],
    "tags": ["libranza", "bpm"],
    "work_item_id": 52991,
    "work_item_url": "https://dev.azure.com/...",
    "created_at": "2025-12-26T10:30:00",
    "content_file": "HU-52991.json"
  }
]
```

---

## Ejemplo de uso

### Escenario: Nueva HU sobre libranza

1. **Usuario ingresa requerimiento:**
   ```
   "Necesito automatizar el proceso de desembolso de libranza"
   ```

2. **Sistema busca HUs relacionadas:**
   - Encuentra: "HU-52991: Creación de etapa automática Cierre Motor (Libranza)"
   - Relevancia: 65%
   - Keywords comunes: libranza, automatico, proceso

3. **Sistema muestra contexto:**
   ```
   📚 HUs relacionadas encontradas:
   
   1. Creación de etapa automática Cierre Motor (Work Item #52991)
      - Relevancia: 65%
      - Palabras clave comunes: libranza, automatico, proceso
      - Ver en Azure DevOps
   ```

4. **Sistema hace menos preguntas:**
   - Ya conoce el contexto de libranza
   - Ya conoce el flujo BPM típico
   - Solo pregunta lo específico del desembolso

5. **Sistema genera HU consistente:**
   - Usa terminología similar a HU-52991
   - Mantiene estructura de campos
   - Referencia la HU anterior cuando aplica

---

## Ventajas

✅ **Consistencia**: Mantiene terminología y estructura uniforme  
✅ **Eficiencia**: Reduce tiempo de análisis y preguntas  
✅ **Trazabilidad**: Enlaces directos a work items relacionados  
✅ **Aprendizaje continuo**: Mejora con cada HU creada  
✅ **Búsqueda rápida**: Encuentra HUs similares en segundos  

---

## Configuración

La base de conocimiento se configura automáticamente. No requiere configuración adicional.

Para cambiar la ubicación de almacenamiento, modifica en `knowledge_base_service.py`:
```python
knowledge_base_service = KnowledgeBaseService(storage_path="ruta/personalizada")
```

---

## Mantenimiento

### Backup
Los archivos JSON son texto plano, fáciles de respaldar:
```bash
cp -r backend/data/knowledge_base/ backup/
```

### Limpieza
Para eliminar HUs antiguas o irrelevantes, simplemente elimina el archivo JSON correspondiente y actualiza el índice.

### Migración
Para migrar a otro servidor, copia la carpeta `knowledge_base/` completa.

---

## Próximas mejoras

🔮 **Búsqueda semántica** con embeddings de OpenAI  
🔮 **Clustering automático** de HUs por dominio  
🔮 **Sugerencias proactivas** de HUs relacionadas  
🔮 **Versionado** de HUs con cambios  
🔮 **Exportación** a diferentes formatos  



