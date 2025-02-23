# prueba_tecnica_quo_digital

## Descripción
Sistema de integración bancaria que permite a los usuarios ver sus cuentas y balances de diferentes bancos en un solo lugar, utilizando la API de Belvo.

## Tabla de Contenidos
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requisitos Técnicos](#requisitos-técnicos)
- [Configuración del Entorno](#configuración-del-entorno)
- [Instalación](#instalación)
- [Ejecución Local](#ejecución-local)
- [Endpoints de la API](#endpoints-de-la-api)
- [Autenticación](#autenticación)
- [Integración con Belvo](#integración-con-belvo)
- [Manejo de Errores](#manejo-de-errores)
- [Pruebas](#pruebas)
- [Despliegue](#despliegue)

## Estructura del Proyecto
```
prueba_tecnica_quo_digital/
├── apps/
│   ├── authentication/
│   │   ├── __init__.py
│   │   ├── serializers/
│   │   │   └── authentication_serializer.py
│   │   └── views/
│   │       └── authentication_view.py
│   ├── belvo/
│   │   ├── __init__.py
│   │   ├── utils.py
│   │   ├── serializers/
│   │   │   └── belvo_serializer.py
│   │   └── views/
│   │       └── belvo_view.py
│   └── users/
│       ├── __init__.py
│       ├── models/
│       │   └── user.py
│       ├── serializers/
│       │   └── user_serializer.py
│       └── views/
│           └── user_view.py
├── prueba_tecnica_quo_digital/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

## Requisitos Técnicos
- Python 3.8+
- PostgreSQL 12+
- Git
- pip y virtualenv

### Dependencias Principales
```
Django==4.2.0
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
python-decouple==3.8
requests==2.31.0
drf-yasg==1.21.7
```

## Configuración del Entorno

1. **Clonar el Repositorio**
```bash
git clone https://github.com/Magno-12/prueba_tecnica_quo_digital
cd project_root
```

2. **Crear y Activar Entorno Virtual**
```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/MacOS
python3 -m venv env
source env/bin/activate
```

3. **Instalar Dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar Variables de Entorno**
```bash
# Editar .env con tus credenciales
nano .env
```

Ejemplo de `.env`:
```plaintext
# Django
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Belvo API
BELVO_SECRET_ID=your_belvo_secret_id
BELVO_SECRET_PASSWORD=your_belvo_secret_password
BELVO_API_URL=https://sandbox.belvo.com/api/
```

5. **Configurar Base de Datos**
```bash
# Crear base de datos PostgreSQL
createdb your_db_name

# Ejecutar migraciones
python manage.py migrate
```

## Ejecución Local

1. **Iniciar Servidor de Desarrollo**
```bash
python manage.py runserver
```

2. **Acceder a la Documentación de la API**
```
http://localhost:8000/swagger/
```

## Endpoints de la API

### Autenticación y Usuarios

1. **Registro de Usuario**
```http
POST /api/users/
Content-Type: application/json

{
    "email": "usuario@ejemplo.com",
    "password": "contraseña",
    "first_name": "Nombre",
    "last_name": "Apellido"
}
```

2. **Login**
```http
POST /api/auth/login/
Content-Type: application/json

{
    "email": "usuario@ejemplo.com",
    "password": "contraseña"
}
```

3. **Logout**
```http
POST /api/auth/logout/
Authorization: Bearer {token}
Content-Type: application/json

{
    "refresh_token": "token"
}
```

### Integración Belvo

1. **Crear Links de Prueba**
```http
POST /api/belvo/create_test_links/
Authorization: Bearer {token}
```

2. **Listar Todas las Cuentas**
```http
GET /api/belvo/all_accounts/
Authorization: Bearer {token}
```

3. **Obtener Cuentas por Banco**
```http
GET /api/belvo/accounts/?link_id={link_id}
Authorization: Bearer {token}
```

## Flujo de Uso Típico

1. **Registro y Autenticación**
```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/api/users/ \
-H "Content-Type: application/json" \
-d '{
    "email": "test@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe"
}'

# 2. Login para obtener token
curl -X POST http://localhost:8000/api/auth/login/ \
-H "Content-Type: application/json" \
-d '{
    "email": "test@example.com",
    "password": "secure_password"
}'
```

2. **Crear Links y Obtener Datos**
```bash
# 1. Crear links de prueba
curl -X POST http://localhost:8000/api/belvo/create_test_links/ \
-H "Authorization: Bearer {tu_token}"

# 2. Obtener todas las cuentas
curl -X GET http://localhost:8000/api/belvo/all_accounts/ \
-H "Authorization: Bearer {tu_token}"
```

## Manejo de Errores

La API utiliza códigos de estado HTTP estándar:

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Ejemplo de respuesta de error:
```json
{
    "error": "Mensaje descriptivo del error",
    "code": "ERROR_CODE"
}
```

## Licencia
[MIT](https://choosealicense.com/licenses/mit/)

## Contacto
Magno Stiven Martinez Bueno - magno12.mcmb@gmail.com

## Agradecimientos
- Belvo API
- Django REST Framework
- Otros contribuidores
