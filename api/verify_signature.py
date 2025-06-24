from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solders.message import Message
from solders.hash import Hash as Signature
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
