# Documento de Requisitos del Producto (PRD) - Versión 1.1 (Actualizado)

Título del Proyecto: Solana Wallet Verifier & Role-Gating Bot

Versión: 1.1

Fecha: 24 de Mayo de 2024

1. Resumen y Visión del Producto (Sin cambios)

El proyecto consiste en desarrollar un sistema integrado con Discord que permita a los miembros de una comunidad verificar la propiedad de una wallet de Solana. Una vez verificada, un bot asignará automáticamente roles en Discord basados en los activos (NFTs y tokens) que posea dicha wallet. El sistema utilizará Python para el bot y la lógica de backend, y Supabase como base de datos para almacenar la relación entre usuarios de Discord y wallets de Solana.

2. Objetivos del Proyecto (Sin cambios)

O1: Aumentar el engagement y el valor para los poseedores de activos digitales de la comunidad.

O2: Automatizar la gestión de roles en Discord, eliminando la necesidad de verificación manual.

O3: Crear una base de datos segura y consultable de los holders verificados de la comunidad.

O4: Proporcionar una experiencia de usuario fluida y segura para la verificación de wallets.

3. Requisitos Funcionales (FR) - Actualizados

FR1: Flujo de Verificación de Wallet

FR1.1: El bot deberá registrar un slash command global llamado /verify.

FR1.2: Al ejecutar /verify, el bot responderá con un mensaje efímero (solo visible para el usuario que ejecutó el comando). Este mensaje contendrá un botón con un enlace de verificación único.

FR1.3: El enlace de verificación será válido por 10 minutos. Si el usuario no completa el proceso en ese tiempo, deberá ejecutar /verify de nuevo.

FR1.4: El enlace llevará al usuario a una página web. La página mostrará un mensaje claro, como: "Estás verificando tu wallet para el servidor 'Mi Servidor'. Este proceso es seguro y solo requiere una firma para demostrar que eres el propietario. No es una transacción, no tiene coste ni consume gas."

FR1.5: Una vez el usuario firma el mensaje (que contendrá su discord_user_id y un nonce), el backend validará la firma.

FR1.6: Si la firma es válida, el sistema asociará la solana_address con el discord_user_id en la base de datos de Supabase.

FR1.7: El bot enviará un mensaje de confirmación público a un canal específico y configurable (ej. #verificados). El mensaje podría ser: "¡Bienvenido! @usuario ha verificado con éxito su wallet 4sf...t5Y."

FR1.8: Inmediatamente después de la verificación, el bot realizará un chequeo de los activos del usuario y le asignará los roles correspondientes por primera vez.

FR2: Gestión Automática de Roles

FR2.1: Un proceso automatizado (cron job) se ejecutará a un intervalo configurable (ej. cada 24 horas) para sincronizar los roles.

FR2.2: El proceso iterará sobre todas las wallets verificadas. Para cada una, consultará sus activos en la blockchain de Solana.

FR2.3: Las reglas para la asignación de roles se definirán y almacenarán en una tabla en Supabase, permitiendo a los administradores añadirlas, modificarlas o eliminarlas sin necesidad de redesplegar el bot.

FR2.4: Un usuario puede acumular múltiples roles si cumple con los requisitos de cada uno.

FR2.5: Si un usuario ya no cumple con los requisitos para un rol (ej. vendió el NFT), el rol le será retirado durante el siguiente ciclo de sincronización.

FR3: Base de Datos y Seguridad (Supabase)

FR3.1: Las políticas de seguridad (RLS) garantizarán que los datos de un usuario solo sean accesibles por él mismo o por el servicio del bot.

FR3.2: El mensaje a firmar incluirá el discord_user_id y un nonce (identificador único de sesión) para prevenir ataques de repetición.

FR4: Comandos del Bot

FR4.1: /verify: Inicia el flujo de verificación para el usuario.

FR4.2: /status: Comando para que un usuario consulte su estado. Responderá con un mensaje efímero mostrando:

Estado de Verificación: (Verificado / No Verificado)

Wallet Vinculada: [La dirección de la wallet del usuario]

Roles Obtenidos por Activos: [Lista de roles que el bot le ha asignado]

FR4.3 (Admin): /setup: Un comando de administrador para configurar parámetros clave como el ID del canal de confirmación.

2. Arquitectura del Sistema y Flujo de Datos (Actualizado)

La arquitectura general se mantiene, pero los flujos específicos se adaptan a tus requisitos.

Flujo de Verificación (/verify)

```mermaid
graph TD
    A[Usuario Discord] -- 1. Ejecuta /verify --> B(Discord Bot (Python))
    B -- 2. Mensaje efímero --> A
    B -- 3. Genera sesión en Supabase (10 min) --> C(Supabase (PostgreSQL))
    D[Página Web (Firma segura)] -- 4. Envía Firma y PubKey --> E(Backend API (Python/Flask))
    E -- 5. Valida Firma y Guarda --> C
    E -- 6. Notificación (Verificación OK) --> B
    B -- 7. Mensaje público en canal #verificados y asignación de roles --> A
    A -- Clic en enlace de verificación --> D
```

Flujo de Estado (/status)

```mermaid
graph TD
    A[Usuario Discord] -- 1. Ejecuta /status --> B(Discord Bot (Python))
    B -- 2. Consulta DB --> C(Supabase (PostgreSQL))
    C -- Datos de estado --> B
    B -- 3. Mensaje efímero con la info --> A
```

3. Modelo de Datos (Supabase) - Esquemas Detallados

Aquí están los esquemas de las tablas que necesitarás en Supabase, diseñados para la flexibilidad que pides.

Tabla 1: verified_wallets (Sin cambios)

```sql
id (uuid, primary key)
created_at (timestamp with time zone)
discord_user_id (text, unique)
solana_address (text, unique)
last_roles_sync (timestamp with time zone)
```

Tabla 2: role_rules (Clave para la flexibilidad)
Esta tabla define las reglas dinámicas para asignar roles.

```sql
CREATE TABLE role_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ DEFAULT now(),
  
  -- Información del Rol en Discord
  discord_role_id TEXT NOT NULL,
  discord_role_name TEXT, -- Opcional, para legibilidad en la DB

  -- Tipo de Activo y Condición
  asset_type TEXT NOT NULL, -- Enum: 'TOKEN', 'NFT_COLLECTION'
  condition_type TEXT NOT NULL, -- Enum: 'GREATER_THAN_OR_EQUAL', 'HAS_ANY'
  
  -- Identificador del Activo
  asset_address TEXT NOT NULL, -- Mint del token o Update Authority/Creator de la colección
  
  -- Valor para la condición
  required_value NUMERIC NOT NULL,

  -- Descripción
  description TEXT
);

COMMENT ON COLUMN role_rules.asset_type IS 'Tipo de activo: TOKEN (un token fungible) o NFT_COLLECTION (cualquier NFT de una colección).';
COMMENT ON COLUMN role_rules.condition_type IS 'Tipo de condición: GREATER_THAN_OR_EQUAL (para tokens) o HAS_ANY (para NFTs).';
COMMENT ON COLUMN role_rules.asset_address IS 'Para TOKEN, es el mint address. Para NFT_COLLECTION, puede ser la verified creator address o la update authority.';
COMMENT ON COLUMN role_rules.required_value IS 'Para TOKEN, la cantidad mínima. Para NFT_COLLECTION, usualmente sería 1.';
```

Ejemplos de Filas en role_rules:

Regla 1 (Token): Para dar el rol "Whale" a quien tenga >= 500 $MYTOKEN.

```
discord_role_id: "9876543210"
asset_type: "TOKEN"
condition_type: "GREATER_THAN_OR_EQUAL"
asset_address: "MintAddressOfMyToken"
required_value: 500
```

Regla 2 (NFT): Para dar el rol "Holder" a quien tenga al menos 1 NFT de la colección "MyMonkeys".

```
discord_role_id: "1234567890"
asset_type: "NFT_COLLECTION"
condition_type: "HAS_ANY"
asset_address: "VerifiedCreatorAddressOfMyMonkeysCollection"
required_value: 1
```

Tabla 3: bot_config
Para manejar configuraciones sin tener que reiniciar el bot.

```sql
CREATE TABLE bot_config (
  config_key TEXT PRIMARY KEY,
  config_value TEXT NOT NULL,
  description TEXT
);

-- Insertar valores iniciales
INSERT INTO bot_config (config_key, config_value, description) VALUES
('CONFIRMATION_CHANNEL_ID', 'ID_DEL_CANAL_AQUI', 'ID del canal donde se publican las verificaciones exitosas.'),
('ROLE_SYNC_INTERVAL_HOURS', '24', 'Frecuencia en horas para la sincronización de roles.'),
('GUILD_ID', 'ID_DEL_SERVIDOR_DISCORD_AQUI', 'ID del servidor de Discord donde opera el bot.');
```

Tabla 4: verification_sessions
Para gestionar los intentos de verificación.

```sql
CREATE TABLE verification_sessions (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  discord_user_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);
```

Cuando creas una sesión, calculas expires_at como now() + interval '10 minutes'.

## Fase 2: Desarrollo del Flujo de Verificación

Esta fase se divide en tres partes:
A. El Backend API (Python Serverless en Vercel)
B. El Frontend de Firma (HTML/JS en Vercel)
C. La Lógica del Bot de Discord (Ejecución Local)

### Paso 0: Estructura del Proyecto

```
mi-proyecto-solana/
├── api/                  # Aquí irán las funciones serverless de Python
│   ├── generate_challenge.py
│   └── verify_signature.py
├── public/               # Aquí irá el frontend estático
│   ├── index.html
│   └── app.js
├── bot/                  # El código del bot (se desplegará en otro sitio)
│   └── bot.py
├── scripts/              # Scripts de ejecución independiente
│   └── role_sync.py
└── requirements.txt      # Dependencias de Python para Vercel y el bot
```

### Paso 1: Preparar Dependencias

`requirements.txt`

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
```

Instálalas en tu entorno virtual: `pip install -r requirements.txt`

### A. El Backend API (Funciones Serverless)

Usaremos FastAPI porque es muy fácil de integrar con Vercel. Vercel convertirá automáticamente cada archivo Python en la carpeta `api/` en un endpoint.

#### 1. Endpoint para Generar el Mensaje a Firmar

`api/generate_challenge.py`

```python
from fastapi import FastAPI, HTTPException, Query
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Carga las credenciales de Supabase desde las variables de entorno
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Usar la SERVICE KEY para el backend
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Vercel ejecutará esta instancia de FastAPI
app = FastAPI()

@app.get("/api/generate-challenge")
def generate_challenge(session_id: str = Query(...)):
    """
    Busca una sesión de verificación válida y genera un mensaje único para firmar.
    """
    try:
        # Busca la sesión en la base de datos
        query = supabase.table("verification_sessions").select("discord_user_id").eq("session_id", session_id).execute()
        
        if not query.data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada o inválida.")
        
        discord_user_id = query.data[0]['discord_user_id']
        
        # Construye el mensaje a firmar. ¡Debe ser único y determinista!
        message = f"Por favor, firma este mensaje para verificar tu cuenta de Discord {discord_user_id} para Mi Servidor.\n\nNonce: {session_id}"
        
        return {"message": message}

    except Exception as e:
        print(f"Error generando el reto: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
```

#### 2. Endpoint para Verificar la Firma

`api/verify_signature.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solders.message import Message
from solders.signature import Signature
import nacl.signing

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

class VerificationPayload(BaseModel):
    session_id: str
    public_key: str
    signature: list[int] # La firma viene como un array de bytes desde JS

@app.post("/api/verify-signature")
def verify_signature(payload: VerificationPayload):
    try:
        # 1. Obtener la sesión y el discord_user_id
        session_query = supabase.table("verification_sessions").select("discord_user_id, expires_at").eq("session_id", payload.session_id).execute()
        if not session_query.data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada o inválida.")
        
        # Aquí podrías añadir una comprobación de si la sesión ha expirado
        
        discord_user_id = session_query.data[0]['discord_user_id']
        solana_address = payload.public_key
        
        # 2. Reconstruir el mensaje EXACTO que se firmó
        message_to_verify = f"Por favor, firma este mensaje para verificar tu cuenta de Discord {discord_user_id} para Mi Servidor.\n\nNonce: {payload.session_id}"
        message_bytes = message_to_verify.encode('utf-8')

        # 3. Verificar la firma usando PyNaCl (para Ed25519)
        verify_key = nacl.signing.VerifyKey(bytes(Pubkey.from_string(solana_address)))
        signature_bytes = bytes(payload.signature)

        verify_key.verify(message_bytes, signature_bytes) # Esto lanzará una excepción si la firma es inválida

        # 4. Si la verificación es exitosa, guardar en la base de datos
        # Usamos upsert para que si el usuario ya existe, se actualice su wallet
        supabase.table("verified_wallets").upsert({
            "discord_user_id": discord_user_id,
            "solana_address": solana_address
        }, on_conflict="discord_user_id").execute()
        
        # 5. Eliminar la sesión para que no se pueda reutilizar
        supabase.table("verification_sessions").delete().eq("session_id", payload.session_id).execute()

        return {"status": "success", "message": "Wallet verificada correctamente."}

    except nacl.exceptions.BadSignatureError:
        raise HTTPException(status_code=400, detail="Firma inválida.")
    except Exception as e:
        print(f"Error en la verificación: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")
```

### B. El Frontend de Firma (Página Estática)

Esta es la página que el usuario verá. Usaremos HTML y JavaScript puro con la librería `@solana/wallet-adapter` cargada desde un CDN para simplificar.

#### 1. El HTML Básico

`public/index.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación de Wallet Solana</title>
    <style>
        body { font-family: sans-serif; background: #2c2f33; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { text-align: center; padding: 2rem; background: #23272a; border-radius: 8px; }
        button { background-color: #7289da; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:disabled { background-color: #4f5f98; cursor: not-allowed; }
        #status { margin-top: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Verificación de Wallet</h1>
        <p>Conecta tu wallet y firma un mensaje para verificar tu propiedad.</p>
        <p><strong>Este proceso es seguro, no es una transacción y no tiene coste.</strong></p>
        <button id="verifyButton">Conectar y Firmar</button>
        <div id="status"></div>
    </div>

    <!-- Dependencias de Solana Wallet Adapter -->
    <script src="https://unpkg.com/@solana/web3.js@latest/lib/index.iife.js"></script>
    <script src="https://unpkg.com/@solana/wallet-adapter-base@latest/lib/index.iife.js"></script>
    <script src="https://unpkg.com/@solana/wallet-adapter-wallets@latest/lib/index.iife.js"></script>
    <script src="https://unpkg.com/@solana/wallet-adapter-react@latest/lib/index.iife.js"></script>
    
    <!-- Nuestro script -->
    <script src="app.js"></script>
</body>
</html>
```

#### 2. El JavaScript de Lógica

`public/app.js`

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const verifyButton = document.getElementById('verifyButton');
    const statusDiv = document.getElementById('status');
    let wallet = null;

    // Obtener session_id de la URL
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
        statusDiv.textContent = "Error: Falta el ID de sesión. Por favor, vuelve a intentarlo desde Discord.";
        verifyButton.disabled = true;
        return;
    }

    // Usamos el wallet adapter de Phantom como ejemplo, puedes añadir más
    const { PhantomWalletAdapter } = window.solanaWalletAdapterWallets;
    const walletAdapter = new PhantomWalletAdapter();

    walletAdapter.on('connect', () => {
        statusDiv.textContent = `Wallet conectada: ${walletAdapter.publicKey.toBase58()}`;
        verifyButton.textContent = 'Firmar Mensaje';
    });

    walletAdapter.on('disconnect', () => {
        statusDiv.textContent = 'Wallet desconectada.';
        verifyButton.textContent = 'Conectar y Firmar';
    });

    verifyButton.addEventListener('click', async () => {
        try {
            if (!walletAdapter.connected) {
                await walletAdapter.connect();
            }

            statusDiv.textContent = 'Obteniendo mensaje para firmar...';
            verifyButton.disabled = true;

            // 1. Pedir el mensaje al backend
            const challengeResponse = await fetch(`/api/generate-challenge?session_id=${sessionId}`);
            if (!challengeResponse.ok) {
                const error = await challengeResponse.json();
                throw new Error(error.detail || 'No se pudo obtener el reto.');
            }
            const { message } = await challengeResponse.json();

            // 2. Firmar el mensaje
            statusDiv.textContent = 'Por favor, firma el mensaje en tu wallet.';
            const encodedMessage = new TextEncoder().encode(message);
            const signature = await walletAdapter.signMessage(encodedMessage);

            // 3. Enviar la firma al backend para verificación
            statusDiv.textContent = 'Verificando firma...';
            const verificationResponse = await fetch('/api/verify-signature', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    public_key: walletAdapter.publicKey.toBase58(),
                    signature: Array.from(signature) // Convertir Uint8Array a Array
                }),
            });

            if (!verificationResponse.ok) {
                const error = await verificationResponse.json();
                throw new Error(error.detail || 'La verificación falló.');
            }
            
            const result = await verificationResponse.json();
            statusDiv.textContent = `✅ ¡Éxito! ${result.message} Ya puedes cerrar esta ventana.`;
            verifyButton.style.display = 'none';

        } catch (error) {
            console.error('Error en el proceso de verificación:', error);
            statusDiv.textContent = `❌ Error: ${error.message}`;
            verifyButton.disabled = false;
        }
    });
});
```

### C. La Lógica del Bot de Discord (Ejecución Local)

`bot/bot.py`

```python
import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime

load_dotenv()

# Carga las credenciales
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
VERCEL_APP_URL = os.environ.get("VERCEL_APP_URL") # ej: https://mi-proyecto.vercel.app

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración del bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} se ha conectado a Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(e)

@bot.tree.command(name="verify", description="Verifica tu wallet de Solana para obtener roles.")
async def verify(interaction: discord.Interaction):
    try:
        # 1. Crear una sesión de verificación en Supabase
        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
        
        session_data = {
            "discord_user_id": str(interaction.user.id),
            "expires_at": expires_at
        }
        
        query = supabase.table("verification_sessions").insert(session_data).execute()
        session_id = query.data[0]['session_id']
        
        # 2. Construir el enlace de verificación
        verification_link = f"{VERCEL_APP_URL}/?session_id={session_id}"
        
        # 3. Enviar el mensaje efímero al usuario
        embed = discord.Embed(
            title="Verificación de Wallet",
            description=f"Haz clic en el botón de abajo para verificar tu wallet de Solana. Este enlace es válido por 10 minutos.",
            color=discord.Color.blue()
        )
        
        view = discord.ui.View()
        button = discord.ui.Button(label="Verificar Mi Wallet", url=verification_link, style=discord.ButtonStyle.link)
        view.add_item(button)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        print(f"Error en /verify: {e}")
        await interaction.response.send_message("Hubo un error al iniciar el proceso. Por favor, inténtalo de nuevo más tarde.", ephemeral=True)

@bot.tree.command(name="status", description="Consulta el estado de tu verificación de wallet.")
async def status(interaction: discord.Interaction):
    try:
        discord_user_id = str(interaction.user.id)
        
        # 1. Consultar la tabla verified_wallets
        wallet_query = supabase.table("verified_wallets").select("solana_address, last_roles_sync").eq("discord_user_id", discord_user_id).execute()
        
        embed = discord.Embed(title="Estado de Verificación de Wallet", color=discord.Color.purple())
        
        if not wallet_query.data:
            embed.description = "Estado de Verificación: **No Verificado**\n\nPara verificar tu wallet, usa el comando `/verify`."
        else:
            wallet_info = wallet_query.data[0]
            solana_address = wallet_info['solana_address']
            last_sync = wallet_info['last_roles_sync']
            
            embed.description = f"Estado de Verificación: **Verificado**\n" \
                                f"Wallet Vinculada: `{solana_address}`\n"
            
            # 2. Obtener los roles actuales del usuario en Discord
            member = interaction.user
            current_role_names = [role.name for role in member.roles if role.name != "@everyone"] # Excluir el rol por defecto
            
            # 3. Obtener las reglas de roles desde Supabase para mostrar los roles obtenidos por activos
            role_rules = supabase.table("role_rules").select("discord_role_name, discord_role_id").execute().data
            
            roles_by_assets = []
            for rule in role_rules:
                # Comprobar si el usuario tiene el rol que esta regla gestiona
                if str(rule['discord_role_id']) in [str(r.id) for r in member.roles]:
                    roles_by_assets.append(rule.get('discord_role_name', f"ID: {rule['discord_role_id']}"))
            
            if roles_by_assets:
                embed.add_field(name="Roles Obtenidos por Activos", value="\n".join(roles_by_assets), inline=False)
            else:
                embed.add_field(name="Roles Obtenidos por Activos", value="Ninguno (o aún no sincronizado).", inline=False)
            
            if last_sync:
                embed.set_footer(text=f"Última sincronización de roles: {last_sync}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        print(f"Error en /status: {e}")
        await interaction.response.send_message("Hubo un error al consultar tu estado. Por favor, inténtalo de nuevo más tarde.", ephemeral=True)

@bot.tree.command(name="setup", description="[ADMIN] Configura parámetros clave del bot.")
@commands.has_permissions(administrator=True) # Solo administradores pueden usar este comando
async def setup(interaction: discord.Interaction, confirmation_channel_id: str = None, guild_id: str = None, role_sync_interval_hours: int = None):
    try:
        updates = []
        if confirmation_channel_id:
            supabase.table("bot_config").upsert({"config_key": "CONFIRMATION_CHANNEL_ID", "config_value": confirmation_channel_id, "description": "ID del canal donde se publican las verificaciones exitosas."}, on_conflict="config_key").execute()
            updates.append(f"Canal de confirmación establecido a: `{confirmation_channel_id}`")
        
        if guild_id:
            supabase.table("bot_config").upsert({"config_key": "GUILD_ID", "config_value": guild_id, "description": "ID del servidor de Discord donde opera el bot."}, on_conflict="config_key").execute()
            updates.append(f"ID del servidor establecido a: `{guild_id}`")

        if role_sync_interval_hours:
            supabase.table("bot_config").upsert({"config_key": "ROLE_SYNC_INTERVAL_HOURS", "config_value": str(role_sync_interval_hours), "description": "Frecuencia en horas para la sincronización de roles."}, on_conflict="config_key").execute()
            updates.append(f"Intervalo de sincronización de roles establecido a: `{role_sync_interval_hours}` horas")

        if not updates:
            await interaction.response.send_message("No se proporcionaron parámetros para configurar.", ephemeral=True)
            return

        await interaction.response.send_message("Configuración actualizada:\n" + "\n".join(updates), ephemeral=True)

    except Exception as e:
        print(f"Error en /setup: {e}")
        await interaction.response.send_message("Hubo un error al configurar el bot. Asegúrate de tener permisos de administrador.", ephemeral=True)

@setup.error
async def setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Ocurrió un error inesperado: {error}", ephemeral=True)

bot.run(DISCORD_TOKEN)
```

## Fase 3: Desarrollo de la Sincronización de Roles

### Paso 1: Dependencias Adicionales y RPC de Solana

Aunque ya tenemos `solana` y `solders` en `requirements.txt`, para obtener los activos de una wallet de manera eficiente, especialmente NFTs, es altamente recomendable usar un proveedor de RPC con APIs avanzadas. Las APIs RPC estándar de Solana (`getTokenAccountsByOwner`) son lentas e ineficientes para esto.

Opción Recomendada: Helius
Helius ofrece una API (`getAssetsByOwner`) que es perfecta para este caso de uso. Su plan gratuito es muy generoso y simplificará enormemente el código.

Regístrate en Helius y obtén tu URL de API.

Añade una nueva dependencia a tu `requirements.txt`:

```
requests
```

Y ejecuta `pip install requests`.

Añade la URL de Helius a tus variables de entorno (archivo `.env`):

```
HELIUS_API_URL=https://mainnet.helius-rpc.com/?api-key=TU_API_KEY
```

### Paso 2: El Script de Sincronización (`role_sync.py`)

Vamos a crear un nuevo archivo, `role_sync.py`, que contendrá toda la lógica. Este script se ejecutará de forma independiente. Puedes colocarlo en la raíz del proyecto o en una nueva carpeta `scripts/`.

`scripts/role_sync.py`

```python
import os
import json
import time
import requests
from supabase import create_client, Client
import discord
from dotenv import load_dotenv

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

load_dotenv()

# Credenciales de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Credenciales de Discord
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID")) # El ID de tu servidor

# API de Helius
HELIUS_API_URL = os.environ.get("HELIUS_API_URL")

# Cliente de Discord (sin necesidad de intents complejos para esto)
intents = discord.Intents.default()
intents.members = True # Necesario para obtener miembros y gestionar roles
client = discord.Client(intents=intents)

# --- LÓGICA DE HELIUS PARA OBTENER ACTIVOS ---

def get_wallet_assets(wallet_address: str):
    """
    Obtiene todos los activos (NFTs y tokens) de una wallet usando la API de Helius.
    """
    headers = {'Content-Type': 'application/json'}
    payload = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getAssetsByOwner",
        "params": {
            "ownerAddress": wallet_address,
            "page": 1,
            "limit": 1000
        }
    }
    try:
        response = requests.post(HELIUS_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        assets = response.json().get('result', {}).get('items', [])
        return assets
    except requests.exceptions.RequestException as e:
        print(f"Error al contactar con Helius API para la wallet {wallet_address}: {e}")
        return []

# --- LÓGICA PRINCIPAL DE SINCRONIZACIÓN ---

async def sync_roles():
    """
    Función principal que orquesta la sincronización de roles.
    """
    await client.wait_until_ready()
    print("Iniciando sincronización de roles...")
    
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"Error: No se pudo encontrar el servidor con ID {GUILD_ID}. Asegúrate de que el bot está en el servidor.")
        return

    # 1. Obtener todas las reglas de roles y wallets verificadas desde Supabase
    try:
        role_rules = supabase.table("role_rules").select("*").execute().data
        verified_wallets = supabase.table("verified_wallets").select("*").execute().data
    except Exception as e:
        print(f"Error al obtener datos de Supabase: {e}")
        return
        
    print(f"Se encontraron {len(verified_wallets)} wallets verificadas y {len(role_rules)} reglas de roles.")

    # 2. Iterar sobre cada wallet verificada
    for wallet_info in verified_wallets:
        discord_user_id = int(wallet_info['discord_user_id'])
        solana_address = wallet_info['solana_address']
        
        try:
            member = await guild.fetch_member(discord_user_id)
        except discord.NotFound:
            print(f"Usuario {discord_user_id} no encontrado en el servidor. Saltando...")
            continue
        except discord.HTTPException as e:
            print(f"Error al obtener miembro {discord_user_id}: {e}")
            continue

        print(f"\nProcesando a @{member.name} ({solana_address})...")
        
        # 3. Obtener los activos de la wallet actual
        assets = get_wallet_assets(solana_address)
        if not assets:
            print(f"No se encontraron activos o hubo un error para la wallet {solana_address}.")
            # Antes de continuar, hay que asegurarse de quitarle los roles si ya no tiene activos
        
        # Construir un mapa de los activos que tiene el usuario para una búsqueda rápida
        user_tokens = {asset['id']: asset['token_info']['balance'] / (10 ** asset['token_info']['decimals']) for asset in assets if asset.get('token_info')}
        user_nfts_by_collection = {}
        for asset in assets:
            if asset.get('grouping'):
                collection_address = asset['grouping'][0].get('group_value')
                if collection_address:
                    if collection_address not in user_nfts_by_collection:
                        user_nfts_by_collection[collection_address] = 0
                    user_nfts_by_collection[collection_address] += 1
        
        roles_to_assign_ids = set()
        
        # 4. Evaluar cada regla contra los activos del usuario
        for rule in role_rules:
            role_id = int(rule['discord_role_id'])
            asset_address = rule['asset_address']
            
            user_has_role = False
            
            # Regla de TOKEN
            if rule['asset_type'] == 'TOKEN' and rule['condition_type'] == 'GREATER_THAN_OR_EQUAL':
                user_balance = user_tokens.get(asset_address, 0)
                if user_balance >= rule['required_value']:
                    user_has_role = True
            
            # Regla de NFT por Colección
            elif rule['asset_type'] == 'NFT_COLLECTION' and rule['condition_type'] == 'HAS_ANY':
                # Helius usa la 'collection mint address' como 'group_value'
                # La regla en la DB debe usar la misma dirección (ej. la de Magic Eden)
                nft_count = user_nfts_by_collection.get(asset_address, 0)
                if nft_count >= rule['required_value']:
                    user_has_role = True
            
            if user_has_role:
                roles_to_assign_ids.add(role_id)
                print(f"  [+] CUMPLE REQUISITO para rol '{rule.get('discord_role_name', role_id)}'")
        
        # 5. Sincronizar los roles en Discord
        current_role_ids = {role.id for role in member.roles}
        managed_role_ids = {int(r['discord_role_id']) for r in role_rules}
        
        roles_to_add = {guild.get_role(rid) for rid in roles_to_assign_ids if rid not in current_role_ids and guild.get_role(rid) is not None}
        roles_to_remove = {guild.get_role(rid) for rid in (managed_role_ids - roles_to_assign_ids) if rid in current_role_ids and guild.get_role(rid) is not None}
        
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Sincronización de activos de Solana")
                print(f"  -> Roles añadidos: {[r.name for r in roles_to_add]}")
            except discord.Forbidden:
                print("  [ERROR] El bot no tiene permisos para añadir roles.")
            except discord.HTTPException as e:
                print(f"  [ERROR] Error de Discord al añadir roles: {e}")


        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason="Sincronización de activos de Solana")
                print(f"  -> Roles eliminados: {[r.name for r in roles_to_remove]}")
            except discord.Forbidden:
                print("  [ERROR] El bot no tiene permisos para quitar roles.")
            except discord.HTTPException as e:
                print(f"  [ERROR] Error de Discord al quitar roles: {e}")

        # Pequeña pausa para no saturar las APIs
        time.sleep(1)
        
    print("\nSincronización de roles completada.")
    await client.close()

# --- Punto de Entrada del Script ---

@client.event
async def on_ready():
    """
    Una vez que el cliente de Discord está listo, ejecuta la sincronización y luego se cierra.
    """
    print(f'{client.user} se ha conectado a Discord para la sincronización.')
    await sync_roles()

if __name__ == "__main__":
    print("Ejecutando script de sincronización de roles...")
    # El script se conecta, hace su trabajo y se desconecta.
    # No necesita mantenerse corriendo como el bot principal.
    client.run(DISCORD_TOKEN)
```

### Paso 3: Cómo Ejecutar el Script

Tienes dos opciones principales para automatizar la ejecución de este script:

#### Opción 1: GitHub Actions (Recomendado y Gratuito)

GitHub Actions puede ejecutar tu script en un horario programado.

Crea un archivo en tu repositorio en la ruta `.github/workflows/role_sync.yml`.

`.github/workflows/role_sync.yml`

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

Configura los Secrets en GitHub:

Ve a tu repositorio en GitHub -> Settings -> Secrets and variables -> Actions.

Crea un "New repository secret" para cada una de las variables de entorno (DISCORD_BOT_TOKEN, GUILD_ID, SUPABASE_URL, etc.).

#### Opción 2: Cron Job en un Servidor

Si decides desplegar tu bot en un VPS o en un servicio como Railway, puedes configurar un cron job tradicional para ejecutar el script.

Ejemplo de línea de crontab:

```bash
# Ejecutar cada día a las 4 AM
0 4 * * * /usr/bin/python3 /ruta/a/tu/proyecto/scripts/role_sync.py >> /ruta/a/logs/sync.log 2>&1
```

## Fase 4: Finalización, Pruebas y Despliegue del Bot

Ahora tienes todos los componentes. Los últimos pasos son:

Completar los Comandos del Bot: Añade el comando `/status` y el comando de admin `/setup` a tu archivo `bot/bot.py`. La lógica del comando `/status` será muy similar a la del script de sincronización, pero solo para un usuario.

Desplegar el Bot de Discord:

Servicio Recomendado: Railway.app. Tienen un plan gratuito, es muy fácil de usar y soporta procesos de larga duración (como un bot de Discord).

Proceso:

Sube tu código a GitHub.

Crea un nuevo proyecto en Railway y vincúlalo a tu repositorio.

Railway detectará el `requirements.txt` y preguntará por el comando de inicio. Introduce `python bot/bot.py`.

Configura las variables de entorno en el panel de Railway.

¡Despliega! Railway construirá y ejecutará tu bot.

Pruebas End-to-End:

Verifica un usuario con `/verify`.

Ejecuta manualmente el workflow de GitHub Actions para ver si asigna los roles correctamente.

Vende un activo y vuelve a ejecutar el workflow para confirmar que el rol se retira.

Usa el comando `/status` para comprobar la información que devuelve.

Asegúrate de que los permisos del bot en tu servidor de Discord son correctos (especialmente el permiso de "Gestionar Roles" y que la jerarquía de roles del bot está por encima de los roles que gestiona).
