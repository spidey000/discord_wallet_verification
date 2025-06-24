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
