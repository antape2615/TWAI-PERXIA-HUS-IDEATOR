# Generador de Historias de Usuario (HU Generator)

Sistema completo para generar Historias de Usuario usando Azure OpenAI y crear work items en Azure DevOps automáticamente.

## Características

- 🔐 Autenticación con Azure AD (MSAL)
- 🤖 Generación de HUs usando Azure OpenAI
- 💬 Chatbot interactivo para clarificar requerimientos
- 👀 Revisión de HUs antes de crear en Azure DevOps
- 🔗 Integración con Azure DevOps API
- 📱 Interfaz web moderna y responsiva
- 🧠 **Sistema de Aprendizaje Automático**: El sistema aprende de cada interacción
- ⭐ **Reinforcement Learning**: Califica respuestas y reporta errores para mejorar el sistema
- 📊 **Análisis de Desempeño**: Estadísticas y análisis del rendimiento del sistema

## Arquitectura

### Backend (Python/FastAPI)
- `backend/main.py`: API principal con endpoints REST
- `backend/services/azure_openai_service.py`: Integración con Azure OpenAI
- `backend/services/azure_devops_service.py`: Integración con Azure DevOps
- `backend/services/conversation_service.py`: Gestión de conversaciones y preguntas

### Frontend (HTML/JavaScript)
- `frontend/index.html`: Interfaz principal
- `frontend/app.js`: Lógica de aplicación y MSAL
- `frontend/styles.css`: Estilos CSS

## Requisitos Previos

1. Azure OpenAI Resource con una deployment (GPT-4 recomendado)
2. Azure DevOps Organization y Project
3. Personal Access Token (PAT) de Azure DevOps con permisos para crear work items
4. Azure AD App Registration para MSAL (opcional pero recomendado)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd TWAI-PERXIA-IDEATOR
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto (puedes usar `.env.example` como base):

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure DevOps Configuration
AZURE_DEVOPS_ORG=https://dev.azure.com/your-organization
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_PAT=your-personal-access-token
AZURE_DEVOPS_WORK_ITEM_TYPE=User Story  # Optional: User Story, Product Backlog Item, Issue, Task, Bug, etc.
AZURE_DEVOPS_DEFAULT_ASSIGNED_TO=angiepena@cbit-online.com  # Optional: Default user to assign work items

# Azure AD/MSAL Configuration
AZURE_CLIENT_ID=your-client-id
AZURE_TENANT_ID=your-tenant-id

# Server Configuration
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:8080,http://localhost:3000
```

### 5. Configurar Azure AD App Registration (para MSAL) - Opcional

La autenticación con MSAL es opcional. Si no la configuras, la aplicación funcionará sin autenticación.

1. Ve a Azure Portal > Azure Active Directory > App registrations
2. Crea una nueva app registration
3. Configura:
   - **Redirect URIs**: `http://localhost:8080` (o tu URL del frontend)
   - **API permissions**: `User.Read` (Microsoft Graph)
4. Copia el **Application (client) ID** y **Directory (tenant) ID**
5. Edita `frontend/static/config.js` y actualiza `AZURE_CLIENT_ID` y `AZURE_TENANT_ID`
   - O puedes copiar `frontend/static/config.example.js` a `frontend/static/config.js` y actualizar los valores

### 6. Configurar Azure DevOps PAT

1. Ve a Azure DevOps > User Settings > Personal Access Tokens
2. Crea un nuevo token con scope: **Work Items (Read & Write)**
3. Copia el token y actualiza `AZURE_DEVOPS_PAT` en `.env`

## Uso

### 1. Iniciar el backend

**Opción A: Usando el script de inicio (recomendado)**

```bash
./start_backend.sh
```

**Opción B: Manualmente**

```bash
cd backend
python main.py
```

**Opción C: Usando uvicorn directamente desde la raíz**

```bash
uvicorn backend.main:app --reload --port 8000
```

El backend estará disponible en `http://localhost:8000`

**Nota**: Asegúrate de tener el archivo `.env` configurado antes de iniciar el backend.

### 2. Iniciar el frontend

**Opción A: Usando el script de inicio (recomendado)**

```bash
./start_frontend.sh
```

**Opción B: Manualmente con Python**

```bash
cd frontend
python -m http.server 8080
# O con python3
python3 -m http.server 8080
```

**Opción C: Con Node.js http-server**

```bash
npx http-server frontend -p 8080
```

**Opción D: Con cualquier otro servidor HTTP estático**

El frontend estará disponible en `http://localhost:8080`

**Nota**: Si vas a usar MSAL, asegúrate de configurar `frontend/static/config.js` antes de iniciar el frontend.

### 3. Acceder a la aplicación

Abre tu navegador en `http://localhost:8080`

**Nota**: Si usas MSAL, asegúrate de que la URL del frontend coincida con la configurada en Azure AD.

## Flujo de Uso

1. **Iniciar Sesión**: Haz clic en "Iniciar Sesión" (si MSAL está configurado)
2. **Ingresar Requerimiento**: Escribe el requerimiento en el campo de texto
3. **Responder Preguntas**: Si el sistema necesita más información, responderá preguntas
4. **Revisar HU**: Una vez generada, revisa la Historia de Usuario completa
5. **Crear en Azure DevOps**: Aprobar y crear el work item en Azure DevOps
6. **Ver en Azure DevOps**: Acceder al work item creado mediante el link proporcionado

## API Endpoints

### `POST /api/conversation/start`
Inicia una conversación y determina si se necesitan preguntas.

**Request:**
```json
{
  "requirement": "Descripción del requerimiento",
  "conversation_history": []
}
```

**Response:**
```json
{
  "has_questions": true,
  "questions": ["pregunta1", "pregunta2"],
  "conversation_id": "uuid",
  "message": "Mensaje del sistema"
}
```

### `POST /api/conversation/continue`
Continúa la conversación con respuestas del usuario.

### `POST /api/hu/generate`
Genera la Historia de Usuario completa.

**Request:**
```json
{
  "requirement": "Descripción del requerimiento",
  "conversation_history": [...],
  "conversation_id": "uuid"
}
```

**Response:**
```json
{
  "hu_content": "HU completa en formato markdown",
  "conversation_id": "uuid",
  "requires_review": true
}
```

### `POST /api/devops/create-work-item`
Crea un work item en Azure DevOps.

**Request:**
```json
{
  "title": "Título de la HU",
  "hu_content": "Contenido completo de la HU",
  "area_path": "Area Path (opcional)",
  "iteration_path": "Iteration Path (opcional)",
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "work_item_id": 123,
  "url": "https://dev.azure.com/org/project/_workitems/edit/123",
  "success": true
}
```

### `POST /api/feedback/submit`
Envía feedback sobre una respuesta del sistema (calificación, error, corrección).

**Request:**
```json
{
  "conversation_id": "uuid",
  "user_message": "Mensaje original del usuario",
  "assistant_response": "Respuesta del asistente",
  "rating": 4.5,
  "is_correct": true,
  "error_description": "Descripción del error (opcional)",
  "correction": "Corrección sugerida (opcional)",
  "feedback_text": "Comentarios adicionales (opcional)",
  "hu_generated": "HU generada (opcional)"
}
```

**Response:**
```json
{
  "feedback_id": "uuid",
  "message": "Feedback guardado exitosamente",
  "success": true
}
```

### `GET /api/feedback/statistics`
Obtiene estadísticas de feedback.

**Response:**
```json
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

### `GET /api/learning/performance`
Obtiene análisis de desempeño del sistema.

**Response:**
```json
{
  "total_interactions": 50,
  "average_rating": 4.2,
  "satisfaction_rate": 80.0,
  "error_rate": 10.0,
  "common_errors": ["error1", "error2"],
  "improvement_areas": ["Área 1", "Área 2"]
}
```

## Configuración del Frontend

Para configurar las credenciales de Azure AD en el frontend:

1. **Recomendado**: Copia `frontend/static/config.example.js` a `frontend/static/config.js`:
   ```bash
   cp frontend/static/config.example.js frontend/static/config.js
   ```
   
2. Edita `frontend/static/config.js` y actualiza los valores:
   ```javascript
   window.AZURE_CLIENT_ID = 'tu-client-id-aqui';
   window.AZURE_TENANT_ID = 'tu-tenant-id-aqui';
   window.API_BASE_URL = 'http://localhost:8000';
   ```

3. Si dejas `AZURE_CLIENT_ID` vacío, la aplicación funcionará sin autenticación (útil para desarrollo)

## Troubleshooting

### Error: "Azure OpenAI endpoint and API key must be set"
- Verifica que el archivo `.env` existe y tiene las variables correctas
- Asegúrate de que estás ejecutando el backend desde el directorio correcto

### Error: "Azure DevOps API error"
- Verifica que el PAT tiene permisos de escritura para work items
- Confirma que la organización y proyecto están correctos
- Verifica que el formato de `AZURE_DEVOPS_ORG` es correcto (ej: `https://dev.azure.com/myorg`)

### Error de CORS
- Asegúrate de que `CORS_ORIGINS` en `.env` incluye la URL del frontend
- Verifica que el backend está ejecutándose

### MSAL no funciona
- Verifica que las URLs de redirect coinciden entre Azure AD y el frontend
- Asegúrate de que el navegador permite popups
- Para desarrollo local, puedes usar `http://localhost:8080` como redirect URI

## Estructura del Proyecto

```
TWAI-PERXIA-IDEATOR/
├── backend/
│   ├── main.py
│   └── services/
│       ├── __init__.py
│       ├── azure_openai_service.py
│       ├── azure_devops_service.py
│       └── conversation_service.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── Prompt.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Sistema de Aprendizaje y Reinforcement Learning

El sistema incluye un módulo avanzado de aprendizaje automático que mejora continuamente basándose en el feedback de los usuarios:

### Características del Sistema de Aprendizaje

1. **Almacenamiento de Feedback**: Todas las interacciones se guardan con:
   - Calificaciones (1-5 estrellas)
   - Indicadores de corrección/error
   - Descripciones de errores
   - Correcciones sugeridas
   - Comentarios adicionales

2. **Mejora de Prompts**: El sistema usa el feedback para:
   - Identificar errores comunes y agregarlos al prompt
   - Incluir ejemplos de buenas respuestas
   - Aplicar correcciones aprendidas
   - Mejorar el contexto de las generaciones futuras

3. **Análisis de Desempeño**: Estadísticas en tiempo real sobre:
   - Tasa de satisfacción
   - Tasa de errores
   - Calificación promedio
   - Patrones de errores comunes
   - Áreas de mejora identificadas

### Cómo Usar el Sistema de Feedback

1. **Después de generar una HU**: En la sección de revisión, encontrarás un formulario de feedback
2. **Calificar**: Usa el sistema de estrellas (1-5) para calificar la respuesta
3. **Reportar Errores**: Si algo está mal, marca la casilla y describe el problema
4. **Proponer Correcciones**: Indica cómo debería haber sido la respuesta
5. **Enviar Feedback**: El sistema usará esta información para mejorar futuras respuestas

**Nota**: El sistema NO se entrena automáticamente con tus conversaciones privadas. Solo usa el feedback que explícitamente proporcionas a través del formulario de calificación.

## Mejoras Futuras

- [ ] Almacenamiento persistente de conversaciones en base de datos
- [ ] Historial de HUs generadas
- [ ] Exportación de HUs en diferentes formatos (PDF, Word)
- [ ] Integración con más sistemas de gestión de proyectos
- [ ] Templates personalizables de HUs
- [ ] Soporte para múltiples idiomas
- [ ] Fine-tuning de modelos usando feedback acumulado
- [ ] Dashboard de métricas de aprendizaje

## Licencia

Este proyecto es privado y confidencial.

## Soporte

Para problemas o preguntas, contacta al equipo de desarrollo.

