# Guía de Despliegue Completa para Solana Wallet Verifier & Role-Gating Bot

Este documento proporciona instrucciones detalladas para desplegar y ejecutar todos los componentes del sistema: el servidor FastAPI, el bot de Discord, la aplicación web estática y el script de sincronización de roles.

## 1. Configuración de Variables de Entorno (`.env`)

Crea un archivo `.env` en la raíz de tu proyecto si no existe. Este archivo contendrá todas las variables de entorno necesarias para que los diferentes componentes funcionen correctamente.

```
# Supabase Credentials
SUPABASE_URL="https://bnpqjqzviwgpgidbxqdt.supabase.co"
SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJucHFqcXp2aXdncGdpZGJ4cWR0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDgwOTA2MywiZXhwIjoyMDY2Mzg1MDYzfQ.nJV2U6DWuPpLw172a-7HsmolP2ome4nrRTc9zXG4tG0"

# Discord Bot Token
DISCORD_BOT_TOKEN="7877227635:AAGNgCYLfACFaSW1gC_FcB1SoICudQnpsZc"

# Vercel App URL (URL pública donde se desplegará el frontend)
VERCEL_APP_URL="https://tu-app-de-vercel.vercel.app" # Ejemplo: https://mi-proyecto.vercel.app

# Helius API URL (para obtener activos de Solana)
HELIUS_API_URL="https://mainnet.helius-rpc.com/?api-key=TU_API_KEY_DE_HELIUS"

# Discord Guild ID (ID de tu servidor de Discord)
GUILD_ID="ID_DE_TU_SERVIDOR_DE_DISCORD"
```

**Importante:**
- Reemplaza los valores de ejemplo con tus credenciales reales.
- `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` son esenciales para la comunicación con tu base de datos Supabase.
- `DISCORD_BOT_TOKEN` es necesario para que el bot se conecte a Discord.
- `VERCEL_APP_URL` debe ser la URL pública de tu frontend desplegado (por ejemplo, en Vercel).
- `HELIUS_API_URL` es crucial para el script de sincronización de roles. Regístrate en Helius para obtener tu API Key.
- `GUILD_ID` es el ID de tu servidor de Discord donde el bot operará.

## 2. Instalación de Dependencias de Python

Asegúrate de tener Python 3.8+ y `pip` instalados. Se recomienda usar un entorno virtual.

1.  **Crea un entorno virtual (opcional pero recomendado):**
    ```bash
    python -m venv venv
    ```
2.  **Activa el entorno virtual:**
    -   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
3.  **Instala las dependencias:**
    El archivo `requirements.txt` contiene todas las dependencias necesarias:
    ```
    fastapi
    uvicorn
    pydantic
    supabase-py
    python-dotenv
    pynacl
    solana
    discord.py
    requests
    solders
    ```
    Instálalas usando pip:
    ```bash
    pip install -r requirements.txt
    ```
    **Nota sobre `uvicorn` y `solana`:**
    -   Si encuentras problemas con `uvicorn` (ej. "uvicorn no se encuentra"), asegúrate de que está instalado en el entorno Python correcto. Puedes intentar instalarlo explícitamente con la ruta completa a tu intérprete Python:
        ```bash
        "C:\tools\Anaconda3\python.exe" -m pip install uvicorn --break-system-packages
        ```
        (Ajusta la ruta a tu instalación de Python si es diferente).
    -   El paquete `solana` puede tener dependencias (`construct`) que causen problemas de instalación. Si `solders` se instala correctamente, el sistema debería funcionar, ya que `solders` es la dependencia principal para la verificación de firmas.

## 3. Ejecución del Servidor FastAPI

El servidor FastAPI maneja la generación de desafíos y la verificación de firmas.

1.  **Asegúrate de que tu entorno virtual esté activado.**
2.  **Navega a la raíz de tu proyecto** (donde se encuentra la carpeta `api/`).
3.  **Ejecuta el servidor Uvicorn:**
    ```bash
    uvicorn api.verify_signature:app --host 0.0.0.0 --port 8000 --reload
    ```
    Esto iniciará el servidor en `http://0.0.0.0:8000`. El flag `--reload` es útil para el desarrollo, ya que reinicia el servidor automáticamente con los cambios en el código.

    **Verificación:** Una vez iniciado, deberías ver mensajes en la consola indicando que Uvicorn está corriendo.

## 4. Ejecución del Bot de Discord

El bot de Discord gestiona los comandos `/verify`, `/status` y `/setup`.

1.  **Asegúrate de que tu entorno virtual esté activado.**
2.  **Navega a la raíz de tu proyecto.**
3.  **Ejecuta el script del bot:**
    ```bash
    python bot/bot.py
    ```
    **Verificación:** En la consola, deberías ver un mensaje como `[TuBotUser] se ha conectado a Discord!`. El bot también intentará sincronizar los comandos slash.

    **Despliegue en Producción (Recomendado):** Para un despliegue 24/7, considera usar servicios como Railway.app, Heroku, o un VPS, ya que ejecutarlo localmente requiere que tu máquina esté siempre encendida.

## 5. Servir la Aplicación Web Estática (`public/`)

La carpeta `public/` contiene el frontend HTML/JS para el proceso de firma.

**Opción Recomendada: Vercel**
Vercel es ideal para desplegar sitios estáticos y funciones serverless (como tus endpoints FastAPI).

1.  **Sube tu código a un repositorio de GitHub/GitLab/Bitbucket.**
2.  **Conecta tu repositorio a Vercel.**
3.  **Configura las variables de entorno en Vercel:** Asegúrate de añadir `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `DISCORD_BOT_TOKEN`, `VERCEL_APP_URL`, `HELIUS_API_URL`, y `GUILD_ID` como variables de entorno en tu proyecto de Vercel.
4.  Vercel detectará automáticamente las carpetas `api/` y `public/` y las desplegará como funciones serverless y un sitio estático, respectivamente.
5.  Una vez desplegado, la `VERCEL_APP_URL` en tu `.env` (y en las variables de entorno del bot) debe apuntar a la URL que Vercel te proporcione.

**Opción Alternativa (para pruebas locales):**
Puedes usar un servidor web simple para servir los archivos estáticos.

1.  **Navega a la raíz de tu proyecto.**
2.  **Usa un servidor HTTP de Python:**
    ```bash
    python -m http.server 8001
    ```
    Esto servirá los archivos en `http://localhost:8001`. Sin embargo, para que el frontend se comunique con el backend FastAPI (que probablemente estará en `http://0.0.0.0:8000` o una URL de Vercel), necesitarás configurar CORS o usar un proxy inverso. Para un despliegue completo, Vercel es la solución más sencilla.

## 6. Ejecución del Script de Sincronización de Roles (`scripts/role_sync.py`)

Este script se encarga de sincronizar los roles de Discord de los usuarios basándose en sus activos de Solana. Está diseñado para ejecutarse periódicamente.

**Opción Recomendada: GitHub Actions**
Ideal para automatizar la ejecución en la nube sin necesidad de un servidor dedicado.

1.  **Crea el archivo de workflow:** En tu repositorio de GitHub, crea el archivo `.github/workflows/role_sync.yml` con el siguiente contenido:
    ```yaml
    name: Sync Solana Roles

    on:
      workflow_dispatch: # Permite ejecutarlo manualmente desde la UI de GitHub
      schedule:
        - cron: '0 4 * * *' # Se ejecuta todos los días a las 4:00 AM UTC

    jobs:
      sync:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout repository
            uses: actions/checkout@v3

          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.10' # O la versión que estés usando

          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
          
          - name: Run role sync script
            env:
              DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
              GUILD_ID: ${{ secrets.GUILD_ID }}
              SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
              SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
              HELIUS_API_URL: ${{ secrets.HELIUS_API_URL }}
            run: python scripts/role_sync.py
    ```
2.  **Configura los Secrets en GitHub:**
    Ve a tu repositorio en GitHub -> Settings -> Secrets and variables -> Actions.
    Crea un "New repository secret" para cada una de las variables de entorno: `DISCORD_BOT_TOKEN`, `GUILD_ID`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `HELIUS_API_URL`.

**Opción Alternativa: Cron Job en un Servidor (VPS/Railway)**
Si tienes un servidor donde ya despliegas el bot, puedes configurar un cron job.

1.  **Asegúrate de que el script `role_sync.py` esté en tu servidor.**
2.  **Edita tu crontab:**
    ```bash
    crontab -e
    ```
3.  **Añade la siguiente línea (ejecuta cada día a las 4 AM):**
    ```bash
    0 4 * * * /usr/bin/python3 /ruta/a/tu/proyecto/scripts/role_sync.py >> /ruta/a/logs/sync.log 2>&1
    ```
    Asegúrate de reemplazar `/usr/bin/python3` con la ruta a tu intérprete Python y `/ruta/a/tu/proyecto/` con la ruta real de tu proyecto.

## 7. Pruebas End-to-End y Consideraciones Finales

-   **Permisos del Bot:** Asegúrate de que tu bot de Discord tenga los permisos necesarios en tu servidor, especialmente "Gestionar Roles", y que su rol esté por encima de los roles que intentará asignar o quitar.
-   **Prueba el flujo completo:**
    1.  Usa `/verify` en Discord.
    2.  Completa la verificación en la página web.
    3.  Verifica que el bot envía el mensaje de confirmación.
    4.  Ejecuta manualmente el workflow de GitHub Actions (o el cron job) para la sincronización de roles.
    5.  Usa `/status` para verificar el estado de tu wallet y los roles asignados.
    6.  (Opcional) Cambia tus activos (ej. vende un NFT) y vuelve a ejecutar la sincronización para confirmar que los roles se retiran correctamente.
