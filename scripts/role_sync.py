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
