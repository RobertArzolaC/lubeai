# ETL Application

Aplicación Django para operaciones de Extracción, Transformación y Carga (ETL) de datos desde servicios externos.

## Características

- **Cliente API de Intertek OILCM**: Servicio para autenticación y descarga de reportes de inspección
- **Gestión de Tokens JWT**: Caché automático y renovación de tokens de autenticación
- **Descarga de Archivos**: Descarga de reportes en múltiples formatos (CSV, PDF, Excel)
- **Manejo de Errores**: Excepciones personalizadas para diferentes tipos de errores
- **Testing Completo**: Suite de tests con 100% de cobertura

## Configuración

### Variables de Configuración

Las credenciales del API se configuran a través de Django Constance en el admin de Django:

1. Acceder al admin: `/admin/constance/config/`
2. Buscar la sección "2. Intertek API Configuration"
3. Configurar:
   - `INTERTEK_API_ENABLED`: Habilitar/deshabilitar la integración
   - `INTERTEK_API_USERNAME`: Usuario de la API
   - `INTERTEK_API_PASSWORD`: Contraseña de la API

## Uso del Servicio

### Ejemplo Básico

```python
from apps.etl import utils

# Obtener cliente configurado
client = utils.get_intertek_client()

# Descargar reporte de inspección
file_path = client.download_inspection_report(
    search_text="",
    lab_number="",
    page_size=50,
    file_type=3  # 1=CSV, 2=PDF, 3=Excel
)

print(f"Reporte descargado en: {file_path}")

# Cerrar conexión
client.close()
```

## Comando de Management

### Descargar Reportes

```bash
# Descargar reporte en formato Excel (default)
python manage.py download_intertek_report

# Descargar reporte con filtros
python manage.py download_intertek_report --lab-number LAB123 --page-size 100

# Descargar en formato CSV
python manage.py download_intertek_report --file-type 1

# Ver ayuda
python manage.py download_intertek_report --help
```

## Arquitectura

### Servicios

- **IntertekAPIClient** (`services/intertek_client.py`): Cliente principal para comunicación con API de Intertek
  - Autenticación con JWT
  - Gestión de caché de tokens
  - Renovación automática de tokens expirados
  - Descarga de archivos
  - Consulta de datos JSON

### Excepciones

- **ETLException**: Excepción base para todas las operaciones ETL
- **AuthenticationError**: Error en autenticación con API
- **TokenExpiredError**: Token JWT expirado
- **APIRequestError**: Error en peticiones HTTP
- **FileDownloadError**: Error al descargar archivos

### Utilities

- **get_intertek_client()**: Función helper para obtener cliente configurado desde Django Constance

## Testing

```bash
# Ejecutar todos los tests de ETL
python manage.py test apps.etl.tests --settings=config.settings.testing

# Ejecutar tests específicos
python manage.py test apps.etl.tests.test_intertek_client --settings=config.settings.testing

# Con cobertura
coverage run manage.py test apps.etl.tests --settings=config.settings.testing
coverage report -m
```

## Caché de Tokens

Los tokens JWT se almacenan en caché con las siguientes características:

- **Duración**: Basada en el tiempo de expiración del token (típicamente 24 horas)
- **Buffer de renovación**: Los tokens se renuevan 5 minutos antes de expirar
- **Backend**: Utiliza el backend de caché configurado en Django (Redis recomendado)
- **Keys de caché**:
  - `intertek_api_token`: Token JWT
  - `intertek_api_token_expiry`: Fecha/hora de expiración

## Integración con Celery

El servicio puede integrarse con Celery para operaciones asíncronas:

```python
from celery import shared_task
from apps.etl import utils

@shared_task
def download_daily_report():
    """Tarea para descargar reporte diario."""
    client = utils.get_intertek_client()

    try:
        file_path = client.download_inspection_report(page_size=1000)
        # Procesar archivo...
        return str(file_path)
    finally:
        client.close()
```

## Mejores Prácticas

1. **Siempre cerrar el cliente**: Usar `try/finally` o context managers para cerrar conexiones
2. **Manejo de excepciones**: Capturar excepciones específicas para mejor control de errores
3. **Logging**: El servicio incluye logging detallado para debugging
4. **Caché**: El caché de tokens reduce llamadas innecesarias a la API
5. **Configuración**: Usar Django Constance para credenciales en lugar de hardcodearlas

## API Endpoints de Intertek

### Autenticación
- **URL**: `https://servicesintertek.sigcomt.com:2012/oilcm/api/Account/Login`
- **Método**: POST
- **Payload**: `{"userName": "...", "password": "..."}`

### Descarga de Reportes
- **URL**: `https://servicesintertek.sigcomt.com:2012/oilcm/api/Report/InspectionDetailExport`
- **Método**: GET
- **Parámetros**:
  - `searchText`: Texto de búsqueda
  - `labNumber`: Número de laboratorio
  - `pageNumber`: Número de página
  - `pageSize`: Registros por página
  - `sortField`: Campo de ordenamiento
  - `sortType`: Tipo de ordenamiento (1=ASC, 0=DESC)
  - `download`: `true` para descarga
  - `fileType`: Tipo de archivo (1=CSV, 2=PDF, 3=Excel)

### Consulta de Detalles
- **URL**: `https://servicesintertek.sigcomt.com:2012/oilcm/api/Report/InspectionDetail`
- **Método**: GET
- **Parámetros**: Similar a InspectionDetailExport sin `download` y `fileType`

## Troubleshooting

### Error: "Intertek API integration is disabled"
**Solución**: Habilitar `INTERTEK_API_ENABLED` en configuración de Constance

### Error: "Intertek API credentials not configured"
**Solución**: Configurar `INTERTEK_API_USERNAME` y `INTERTEK_API_PASSWORD` en Constance

### Error: "Token expired"
**Solución**: El servicio renueva tokens automáticamente. Si persiste, verificar conectividad con API

### Archivos no se descargan
**Solución**: Verificar permisos de escritura en directorio temporal del sistema
