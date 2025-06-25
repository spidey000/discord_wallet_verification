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
VERCEL_APP_URL = os.environ.get("VERCEL_APP_URL").strip('"') if os.environ.get("VERCEL_APP_URL") else None # ej: https://mi-proyecto.vercel.app

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
        print(f"DEBUG: Verification Link: {verification_link}")
        
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
