# 👤 Asignación Automática de Work Items

## Cambio Implementado

Ahora todas las HUs creadas en Azure DevOps se asignarán automáticamente a **angiepena@cbit-online.com** por defecto.

---

## ✅ Cómo Funciona

### **1. Configuración por Defecto**
El sistema asigna automáticamente las HUs a `angiepena@cbit-online.com` si no se especifica otro usuario.

### **2. Variable de Entorno (Opcional)**
Puedes personalizar el usuario por defecto agregando esta línea a tu archivo `.env`:

```env
AZURE_DEVOPS_DEFAULT_ASSIGNED_TO=angiepena@cbit-online.com
```

### **3. Asignación Dinámica (API)**
También puedes especificar un usuario diferente al crear el work item mediante la API:

```json
POST /api/devops/create-work-item
{
  "title": "Mi HU",
  "hu_content": "...",
  "assigned_to": "otro.usuario@cbit-online.com"
}
```

---

## 📋 Archivos Modificados

1. **`backend/services/azure_devops_service.py`**
   - Agregado parámetro `assigned_to` en `create_user_story()`
   - Campo `System.AssignedTo` agregado a los work item patches

2. **`backend/main.py`**
   - Agregado `assigned_to` al modelo `CreateWorkItemRequest`
   - Configuración por defecto a `angiepena@cbit-online.com`
   - Lectura de variable de entorno `AZURE_DEVOPS_DEFAULT_ASSIGNED_TO`

3. **`README.md`**
   - Documentación de la nueva variable de entorno

---

## 🎯 Uso

### **Opción 1: Usar el valor por defecto (Recomendado)**
No hagas nada. Todas las HUs se asignarán automáticamente a `angiepena@cbit-online.com`.

### **Opción 2: Personalizar en .env**
Agrega a tu archivo `.env`:
```env
AZURE_DEVOPS_DEFAULT_ASSIGNED_TO=tu.email@cbit-online.com
```

### **Opción 3: Especificar por HU**
Al crear el work item desde el frontend, el sistema usará el valor por defecto. Si necesitas asignar a otro usuario, deberás modificar el frontend para incluir un selector de usuario.

---

## 🔍 Validación

Para verificar que funciona:

1. **Genera una nueva HU** en el frontend
2. **Créala en Azure DevOps**
3. **Abre el work item** en Azure DevOps
4. **Verifica** que el campo "Assigned To" muestre `Angie Pena <angiepena@cbit-online.com>`

---

## ⚠️ Notas Importantes

### **Formato del Email**
Azure DevOps acepta el email del usuario tal como está registrado en la organización. Asegúrate de que:
- ✅ El email existe en tu organización de Azure DevOps
- ✅ El usuario tiene permisos en el proyecto
- ✅ El formato es exactamente como aparece en Azure DevOps

### **Permisos Requeridos**
El Personal Access Token (PAT) debe tener permisos de:
- ✅ **Work Items (Read, write, & manage)**

### **Usuario No Encontrado**
Si el usuario no existe o no tiene permisos:
- El work item se creará sin asignación
- Azure DevOps mostrará un warning pero no fallará la creación
- Puedes asignar manualmente después

---

## 🚀 Próximas Mejoras

Posibles mejoras futuras:
- [ ] Selector de usuario en el frontend
- [ ] Lista desplegable con usuarios del proyecto
- [ ] Asignación basada en área o tipo de HU
- [ ] Asignación round-robin para distribuir carga
- [ ] Notificación al usuario asignado

---

## 📝 Ejemplo de Uso

### **Crear HU con asignación por defecto:**
```bash
# El sistema automáticamente asignará a angiepena@cbit-online.com
curl -X POST http://localhost:8000/api/devops/create-work-item \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nueva HU",
    "hu_content": "Contenido de la HU..."
  }'
```

### **Crear HU con asignación personalizada:**
```bash
curl -X POST http://localhost:8000/api/devops/create-work-item \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nueva HU",
    "hu_content": "Contenido de la HU...",
    "assigned_to": "otro.usuario@cbit-online.com"
  }'
```

---

## ✅ Estado

- ✅ **Implementado**: Asignación automática por defecto
- ✅ **Configuración**: Variable de entorno opcional
- ✅ **API**: Parámetro `assigned_to` disponible
- ✅ **Documentación**: README actualizado
- ⏳ **Frontend**: Selector de usuario (pendiente)

---

**¡Listo! Todas las HUs ahora se asignarán automáticamente a angiepena@cbit-online.com** 👤✨



