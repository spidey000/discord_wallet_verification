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
