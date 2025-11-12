#  RetroCloud

**RetroCloud** es una plataforma experimental de *cloud gaming retro* inspirada en servicios como *GeForce Now*, pero centrada en la emulación de consolas clásicas mediante **RetroBat**, ejecutándose sobre infraestructura de **AWS**.

El proyecto fue diseñado como **prueba de concepto universitaria**, sin ánimo de lucro, para demostrar despliegue automático (CI/CD), almacenamiento distribuido y autenticación básica en la nube.

---

##  Arquitectura General

RetroCloud está compuesto por los siguientes módulos:

| Componente | Descripción |
|-------------|-------------|
| **RetroBat + NICE DCV (EC2 Windows)** | Máquina virtual Windows que ejecuta RetroBat y expone el escritorio por navegador (DCV). |
| **FastAPI Backend** | API ligera en Python (login, logout, sesiones únicas, validación de usuarios). |
| **AWS S3** | Almacenamiento de ROMs y BIOS replicado entre regiones. |
| **AWS DynamoDB** | Base de datos NoSQL que gestiona usuarios y sesiones activas. |
| **AWS CodeDeploy + GitHub Actions** | Automatiza el despliegue desde el repositorio (`main`) a la instancia EC2. |
| **AWS IAM Roles** | Control de acceso seguro para el pipeline y la instancia. |

---

##  Infraestructura AWS

| Servicio | Recurso | Nombre / Región |
|-----------|----------|----------------|
| **EC2** | Windows Server 2022 (t3.micro) + Elastic IP | `retrocloud-ec2` (`us-east-2`) |
| **S3** | Bucket principal ROMs | `retrocloud-roms-use2` |
| **S3** | Réplica (región secundaria) | `retrocloud-roms-use1` |
| **S3** | Bucket artefactos (deploy) | `retrocloud-artifacts-use2` |
| **DynamoDB** | Tabla usuarios | `retro_users` |
| **DynamoDB** | Tabla sesiones | `retro_sessions` |
| **CodeDeploy** | Aplicación | `retrocloud-app` |
| **CodeDeploy** | Deployment group | `retrocloud-dg` |
| **IAM Role (EC2)** | Permisos S3/DynamoDB | `RetroHostRole` |
| **IAM Role (OIDC)** | Permisos CI/CD (GitHub Actions) | `GitHubDeployRole` |

---

##  Autenticación y sesiones

- **Signup abierto**: cualquier usuario puede crear cuenta.
- **Política de contraseñas**: mínimo 8 caracteres, mayúsculas, minúsculas y símbolos.
- **Sesión única**: si un usuario ya tiene una sesión activa, no puede abrir otra hasta cerrarla.
- **Expiración**: 5 minutos de inactividad (TTL en DynamoDB).
- **Admin inicial**: `admin / 5896457`.

---
---

##  Despliegue Automático (CI/CD)

El pipeline utiliza **GitHub Actions → AWS CodeDeploy**.

1. Cada `push` a la rama **`main`**:
   - Empaqueta `/app`, `/scripts` y `appspec.yml` en un ZIP.
   - Sube el artefacto a `s3://retrocloud-artifacts-use2/releases/`.
   - Crea un deployment en CodeDeploy apuntando al grupo `retrocloud-dg`.
2. CodeDeploy en la instancia EC2:
   - Ejecuta `install.ps1` → instala dependencias.
   - Ejecuta `start.ps1` → inicia el servidor FastAPI.

---

##  Rutas del Backend (FastAPI)

| Endpoint | Método | Descripción |
|-----------|---------|-------------|
| `/signup` | POST | Crea un nuevo usuario. |
| `/login` | POST | Inicia sesión si no existe una activa. |
| `/logout` | POST | Cierra sesión actual. |
| `/play` | GET | Redirige al cliente web de **NICE DCV** (`https://<EIP>:8443/`). |

---

##  Dependencias principales

- **Python 3.11+**
- `fastapi`, `uvicorn`, `boto3`, `passlib[bcrypt]`, `python-dotenv`
- **Windows Server 2022**, **NICE DCV**, **RetroBat**
- **AWS CLI** (instalado en Actions)
- **rclone** + **WinFsp** (montaje S3 como unidad `D:`)

---

##  Configuración de entorno (`.env`)

Ejemplo (`app/.env.example`):

APP_ENV=prod
APP_PORT=8080
AWS_REGION=us-east-2
DDB_USERS_TABLE=retro_users
DDB_SESSIONS_TABLE=retro_sessions
SESSION_TTL_MINUTES=5
PASSWORD_BCRYPT_ROUNDS=12
DCV_HOSTNAME=<EIP_PUBLICA>
DCV_PORT=8443


---

##  Variables de entorno (GitHub Secrets)

El workflow obtiene las credenciales desde el **Environment `.env`**:

| Nombre | Descripción |
|---------|-------------|
| `AWS_ACCOUNT_ID` | ID de la cuenta AWS |
| `AWS_REGION` | Región AWS (`us-east-2`) |
| `ROLE_TO_ASSUME` | ARN del rol `GitHubDeployRole` |

---

##  Acceso al sistema

1. Accede a la API:  
   `http://<Elastic-IP>:8080/`
2. Inicia sesión con tu usuario o crea uno nuevo.
3. Una vez logueado, entra a:  
   `http://<Elastic-IP>:8080/play`  
   → Redirige al cliente web **NICE DCV** donde se ejecuta RetroBat.

---

##  Limitaciones del prototipo

- La instancia `t3.micro` **no posee GPU**, por lo que el rendimiento gráfico está limitado (solo consolas 8/16-bit).
- El certificado de DCV es **self-signed** (mostrar advertencia de navegador).
- Sin dominios personalizados ni HTTPS externos.
- Solo pruebas conceptuales y académicas (no producción).

---

##  Créditos y Licencia

Proyecto desarrollado como demostración académica.  
RetroBat y NICE DCV son productos de sus respectivos creadores.  
El uso de ROMs y BIOS es únicamente con fines educativos y bajo propiedad legal del usuario.

---
