# Guía Rápida de Configuración

Esta guía te ayudará a configurar el sistema paso a paso.

## 1. Requisitos Previos

- Python 3.8 o superior
- Cuenta de Azure con acceso a:
  - Azure OpenAI (resource con deployment GPT-4)
  - Azure DevOps (organización y proyecto)
  - Azure AD (opcional, para MSAL)

## 2. Configuración Inicial

### 2.1 Clonar/Descargar el Proyecto

```bash
cd TWAI-PERXIA-IDEATOR
```

### 2.2 Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2.3 Instalar Dependencias

```bash
pip install -r requirements.txt
```

## 3. Configurar Azure OpenAI

1. Ve a Azure Portal y crea un recurso de Azure OpenAI (si no lo tienes)
2. Crea un deployment de GPT-4 (o GPT-35-Turbo)
3. Obtén:
   - **Endpoint**: `https://tu-recurso.openai.azure.com/`
   - **API Key**: desde "Keys and Endpoint" en Azure Portal

## 4. Configurar Azure DevOps

1. Ve a Azure DevOps > User Settings > Personal Access Tokens
2. Crea un nuevo token con:
   - **Name**: HU Generator
   - **Scopes**: Work Items (Read & Write)
   - **Expiration**: Según tu política
3. Copia el token (solo se muestra una vez)
4. Obtén:
   - **Organization URL**: `https://dev.azure.com/tu-organizacion`
   - **Project Name**: El nombre de tu proyecto
   - **PAT**: El token que acabas de crear

## 5. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_API_KEY=tu-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure DevOps
AZURE_DEVOPS_ORG=https://dev.azure.com/tu-organizacion
AZURE_DEVOPS_PROJECT=tu-proyecto
AZURE_DEVOPS_PAT=tu-pat-token
AZURE_DEVOPS_WORK_ITEM_TYPE=User Story  # Opcional: User Story, Product Backlog Item, Issue, Task, Bug, etc.

# Server (puedes dejar estos valores por defecto)
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:8080
```

## 6. Configurar Frontend (Opcional - MSAL)

Si quieres usar autenticación con Azure AD:

1. Crea una App Registration en Azure AD
2. Configura Redirect URI: `http://localhost:8080`
3. Copia `config.example.js` a `config.js`:

```bash
cp frontend/config.example.js frontend/config.js
```

4. Edita `frontend/config.js`:

```javascript
window.AZURE_CLIENT_ID = 'tu-client-id';
window.AZURE_TENANT_ID = 'tu-tenant-id';
window.API_BASE_URL = 'http://localhost:8000';
```

**Nota**: Si no configuras MSAL, la aplicación funcionará sin autenticación.

## 7. Iniciar la Aplicación

### Terminal 1 - Backend

```bash
./start_backend.sh
```

O manualmente:
```bash
cd backend
python main.py
```

Verifica que el backend esté corriendo: `http://localhost:8000/health`

### Terminal 2 - Frontend

```bash
./start_frontend.sh
```

O manualmente:
```bash
cd frontend
python3 -m http.server 8080
```

## 8. Probar la Aplicación

1. Abre tu navegador en `http://localhost:8080`
2. Si configuraste MSAL, inicia sesión
3. Ingresa un requerimiento de ejemplo
4. Responde las preguntas si se te solicitan
5. Revisa la HU generada
6. Crea el work item en Azure DevOps

## Troubleshooting

### Error: "Azure OpenAI endpoint and API key must be set"
- Verifica que el archivo `.env` existe y tiene los valores correctos
- Asegúrate de estar ejecutando el backend desde el directorio correcto
- Verifica que el archivo `.env` está en la raíz del proyecto

### Error: "Azure DevOps API error"
- Verifica que el PAT tiene permisos de escritura para work items
- Confirma que la organización y proyecto están correctos
- El formato de `AZURE_DEVOPS_ORG` debe ser: `https://dev.azure.com/myorg` (sin barra final)

### Error de CORS
- Verifica que `CORS_ORIGINS` en `.env` incluye la URL del frontend
- Asegúrate de que el backend está corriendo

### MSAL no funciona
- Verifica que `config.js` existe y tiene los valores correctos
- Confirma que la Redirect URI en Azure AD coincide con tu URL del frontend
- Si no necesitas autenticación, puedes dejar `AZURE_CLIENT_ID` vacío en `config.js`

## Siguiente Paso

Lee el [README.md](README.md) completo para más detalles sobre el uso y las características del sistema.

