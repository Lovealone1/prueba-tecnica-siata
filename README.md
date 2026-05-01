# Prueba Técnica SIATA - Sistema de Gestión Logística 

Este repositorio contiene la solución a la prueba técnica enfocada en la creación de un sistema backend robusto para la gestión logística de mercancías marítimas y terrestres. 

El proyecto fue desarrollado utilizando un enfoque de **Clean Architecture**, asegurando escalabilidad, mantenibilidad y un alto estándar de calidad de código.

---

## Arquitectura y Tecnologías

### 1. Clean Architecture
Se implementó una arquitectura limpia separando estrictamente las responsabilidades en capas:
- **Domain:** Entidades de negocio centrales y contratos de interfaces.
- **Repository (Data Access):** Implementación del patrón *Repository* para abstraer el acceso a la base de datos, facilitando posibles migraciones de motores en el futuro sin afectar la lógica de negocio.
- **Service (Business Logic):** Dónde reside toda la lógica de negocio, validaciones complejas y cálculos (ej. cálculo de descuentos).
- **Routers / Controllers (API):** Capa de presentación que maneja las solicitudes HTTP y delega la ejecución a los servicios.

### 2. Inyección de Dependencias
Se utilizó la librería `dependency-injector` para gestionar la creación e inyección de servicios y repositorios. Esto elimina el acoplamiento fuerte, facilita enormemente la creación de *Mocks* durante el testing unitario y evita los problemas de importaciones circulares en proyectos grandes.

### 3. ¿Por qué FastAPI sobre Django?
Se eligió **FastAPI** en lugar de Django por las siguientes razones:
- **Asincronismo Nativo (Async/Await):** Ideal para aplicaciones I/O bound (bases de datos, llamadas externas), mejorando significativamente el throughput.
- **Validación Automática:** Integración profunda con *Pydantic*, lo que garantiza que los datos entrantes sean validados de forma estricta y declarativa antes de tocar la lógica de negocio.
- **Rendimiento:** Es uno de los frameworks web más rápidos para Python, acercándose a NodeJS y Go.
- **Documentación Autogenerada:** Generación nativa de OpenAPI (Swagger/ReDoc) sin configuraciones adicionales.
- **Microservicios Friendly:** A diferencia de Django que es altamente monolítico y viene con "baterías incluidas" (muchas veces innecesarias), FastAPI permite diseñar arquitecturas más ligeras y modulares.

### 4. Gestor de Paquetes: Poetry
Se optó por **Poetry** como gestor de dependencias en lugar del tradicional `pip` + `requirements.txt`:
- **Resolución Determinística:** Utiliza un `poetry.lock` para asegurar que las versiones instaladas sean exactamente las mismas en todos los entornos (Dev, CI/CD, Prod).
- **Gestión de Entornos Virtuales:** Poetry administra automáticamente el entorno virtual del proyecto.
- **Separación Clara:** Permite separar fácilmente las dependencias principales de las dependencias de desarrollo (pytest, ruff, mypy).

### 5. Patrones de Diseño Implementados
- **Repository Pattern:** Centraliza y aísla la lógica de acceso a datos (SQLAlchemy/Alembic).
- **Dependency Injection Pattern:** Desacopla la instanciación de objetos de su uso.
- **Middleware Pattern:** Interceptores de peticiones HTTP para manejar autenticación, autorización y registro de auditoría.
- **DTO Pattern (Data Transfer Object):** Uso de esquemas Pydantic para transferir datos entre la capa de red y la capa de negocio sin exponer las entidades de base de datos directamente.

---

## Funcionalidades Base Implementadas

El sistema cumple rigurosamente con las reglas de negocio establecidas:

1. **Relación Envío-Cliente:** Cada envío (`Shipment`) está fuertemente vinculado a un cliente (`Customer`) para seguimiento exhaustivo.
2. **Descuentos Terrestres:** Se aplica un descuento automático del **5%** al precio de envío para logística terrestre si la cantidad de productos supera las 10 unidades.
3. **Descuentos Marítimos:** Se aplica un descuento automático del **3%** al precio de envío para logística marítima si la cantidad supera las 10 unidades.
4. **Número de Guía Único:** El campo `tracking_number` (número de guía) garantiza unicidad a nivel de base de datos y validación de aplicación.
5. **Cantidades Válidas:** Validación estricta para garantizar que `cantidad_producto` sea siempre mayor que 0.
6. **Validación de Flotas y Placas:** Uso de expresiones regulares (Regex) para validar el formato correcto del número de flota marítima y las placas de los camiones terrestres.
7. **CRUD Completo:** Funcionalidades completas de creación, lectura (con filtros), actualización y eliminación para las entidades: **Productos, Envíos, Clientes, Puertos y Bodegas**.
8. **Motor de Base de Datos:** Se implementó utilizando **PostgreSQL** (con operaciones asíncronas).
   - *Scripts y Migraciones:* Se utiliza **Alembic** con scripts puros `_up` y `_down` de SQL para tener un control granular sobre las entidades de la base de datos (Ej: uso de `uuid-ossp` y `citext` para correos).

---

## Funcionalidades Bonus Logradas

Se dio especial énfasis en cubrir todas las funcionalidades bonus, elevando el proyecto a estándares de producción:

3. **Documentación API REST:** Documentación interactiva completa autogenerada disponible en `/docs` (Swagger UI) y `/redoc`.
4. **Registro y Autenticación:** Sistema de autenticación de usuarios implementando flujo de registro y login.
5. **Seguridad con Token Bearer:** La API está protegida. Se validan estrictamente los tokens JWT tipo Bearer en cada petición a rutas protegidas.
6. **Manejo de Errores y Validaciones:** Respuestas estructuradas utilizando los códigos HTTP apropiados:
   - `400 Bad Request` para reglas de negocio no cumplidas.
   - `401 Unauthorized` para tokens inválidos o expirados.
   - `403 Forbidden` para permisos insuficientes.
   - `422 Unprocessable Entity` para validaciones de esquema (Pydantic).
   - `500 Internal Server Error` controlados de forma global.
7. **Autorización y Roles (RBAC):** Funcionalidad de autorización que distingue accesos según los roles del usuario (Ej: `admin`, `user`).

---

## Lógica Extra y Valor Agregado

Más allá de los requisitos, se implementaron soluciones que enriquecen el ecosistema:

- **Redis - Caché, Sesiones y OTP:**
  - **¿Por qué Redis?** Para mitigar la carga en la base de datos transaccional y manejar datos efímeros con alta velocidad.
  - **¿Para qué se usó?** 
    1. Caché de perfiles de usuario para autenticación ultra rápida.
    2. Manejo de códigos One-Time Password (OTP) seguros y con expiración nativa (TTL).
    3. Gestión de sesiones, mejorando la seguridad general.

- **Middlewares Avanzados:**
  - **Audit Logging Middleware:** Interceptor que captura el contexto de la petición y los cambios de estado (diffs) en la lógica de negocio utilizando `ContextVars`. Permite llevar una bitácora exacta de *quién modificó qué*.
  - **Context Middleware:** Inyecta identificadores de correlación para el rastreo de peticiones a lo largo de todos los servicios.
  - **Role Middleware:** Validación dinámica de permisos antes de alcanzar los *endpoints*.

- **Automatizaciones y Helpers Propios:**
  - **Mapeo de Continentes:** Lógica automática en Pydantic (`LocationHelper`) que deduce el continente según el país ingresado, manteniendo la consistencia de los datos geográficos en puertos y almacenes.
  - **Generadores Extras:** Creación estandarizada de números de rastreo (`tracking_number`) y manejo automático de husos horarios (Timezones de Colombia) para la auditoría.
  - **Pipeline CI/CD:** Preparación multi-stage de Docker para despliegue  e integración de GitHub Actions para ejecución de tests.

---

## Decisiones Arquitectónicas (Good To Know)

A lo largo del desarrollo se tomaron múltiples decisiones arquitectónicas evaluando pros y contras. Para una visión más profunda sobre:
- Simplificación de entidades vs. Complejidad empresarial real.
- Paginación basada en Offset vs. Cursores.
- Uso de Enums para dimensiones de productos.
- Estructura del entorno productivo.

**Te invito a leer el documento adjunto:** [**good-to-know.md**](./good-to-know.md)

---

### Instrucciones para levantar el proyecto localmente
*(El proyecto cuenta con scripts bash listos para su uso)*

1. Configurar las variables de entorno:
Crea un archivo `.env` en la raíz del proyecto basándote en el siguiente mock:
```env
ENVIRONMENT=development
PORT=8000
API_BASE_URL="http://localhost:8000/api"
FRONTEND_URL="http://localhost:3000"

# Database
DATABASE_URL="postgresql://postgres:password@localhost:5434/pt-siata"
DIRECT_URL="postgresql://postgres:password@localhost:5434/pt-siata"

# Redis
REDIS_ENABLED=true
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=secret
REDIS_DB=0
REDIS_TTL_SECONDS=300
REDIS_KEY_PREFIX=pt-siata

# JWT (Seguridad)
JWT_SECRET=super_secret_jwt_key_please_change
JWT_EXPIRES_IN_MINUTES=10080

# Logging
LOG_LEVEL=INFO
```

2. Ejecutar la base de datos y Redis (Requiere Docker):
```bash
docker-compose up -d
```

3. Instalar dependencias con Poetry:
```bash
poetry install
```

4. Aplicar migraciones:
```bash
./scripts/db-manage.sh up
```

5. Ejecutar el servidor backend:
```bash
./scripts/run-backend.sh
# O manualmente: poetry run uvicorn src.main:app --reload
```

> La API estará disponible en `http://localhost:8000` y la documentación en `http://localhost:8000/docs`.
