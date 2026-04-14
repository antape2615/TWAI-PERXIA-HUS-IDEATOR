# Troubleshooting

## Problemas de Instalación de Dependencias

### Error: `pydantic-core` no compila en Python 3.14

Si estás usando Python 3.14 y tienes problemas compilando `pydantic-core`, puedes intentar:

1. **Usar Python 3.11 o 3.12** (recomendado):
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **O instalar versiones más recientes sin versiones fijas**:
   ```bash
   pip install fastapi uvicorn python-dotenv openai azure-identity httpx pydantic python-multipart msal --upgrade
   ```

### Error: "ModuleNotFoundError: No module named 'fastapi'"

Asegúrate de:
1. Estar en el entorno virtual correcto:
   ```bash
   source .venv/bin/activate  # o venv/bin/activate
   ```

2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Verificar que estás usando el Python correcto:
   ```bash
   which python3
   python3 --version
   ```

### Error: "requirements.txt not found"

El archivo `requirements.txt` debe estar en la raíz del proyecto, no en `backend/`. 

Para instalar desde la raíz:
```bash
cd /path/to/TWAI-PERXIA-IDEATOR
pip install -r requirements.txt
```

### Error: "Azure OpenAI endpoint and API key must be set"

1. Verifica que el archivo `.env` existe en la raíz del proyecto
2. Asegúrate de que tiene las variables correctas:
   ```env
   AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
   AZURE_OPENAI_API_KEY=tu-api-key
   ```
3. Verifica que estás ejecutando el backend desde el directorio correcto

### Error: "Azure DevOps API error"

1. Verifica que el PAT tiene permisos de **Work Items (Read & Write)**
2. Confirma que `AZURE_DEVOPS_ORG` tiene el formato correcto: `https://dev.azure.com/tu-organizacion` (sin barra final)
3. Verifica que el proyecto existe en la organización

### Error de CORS

1. Verifica que `CORS_ORIGINS` en `.env` incluye la URL exacta del frontend
2. Asegúrate de que no hay espacios adicionales en la lista de orígenes
3. Si usas `http://localhost:8080`, asegúrate de que el backend permite ese origen

### MSAL no funciona

1. Verifica que `frontend/static/config.js` existe y tiene valores correctos
2. Confirma que la Redirect URI en Azure AD coincide exactamente con tu URL
3. Si no necesitas autenticación, deja `AZURE_CLIENT_ID` vacío en `frontend/static/config.js`

## Problemas Comunes de Python 3.14

Python 3.14 es muy reciente y algunas librerías pueden no tener soporte completo. Si encuentras problemas:

1. **Usa Python 3.11 o 3.12** (más estable y ampliamente soportado)
2. **Actualiza pip**:
   ```bash
   python3 -m pip install --upgrade pip
   ```
3. **Instala dependencias una por una** para identificar cuál falla:
   ```bash
   pip install fastapi
   pip install uvicorn
   pip install pydantic
   # etc.
   ```

