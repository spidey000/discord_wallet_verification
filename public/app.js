document.addEventListener('DOMContentLoaded', () => {
    const verifyButton = document.getElementById('verifyButton');
    const statusDiv = document.getElementById('status');
    const walletSelect = document.getElementById('wallet-select');
    const connectedWalletInfo = document.getElementById('connected-wallet-info');

    let currentWalletAdapter = null;

    // Obtener session_id de la URL
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
        statusDiv.textContent = "Error: Falta el ID de sesión. Por favor, vuelve a intentarlo desde Discord.";
        verifyButton.disabled = true;
        walletSelect.disabled = true;
        return;
    }

    // Inicializar adaptadores de wallet
    const { PhantomWalletAdapter } = window.solanaWalletAdapterPhantom;
    const { SolflareWalletAdapter } = window.solanaWalletAdapterSolflare;
    const { LedgerWalletAdapter } = window.solanaWalletAdapterLedger;

    const wallets = {
        Phantom: new PhantomWalletAdapter(),
        Solflare: new SolflareWalletAdapter(),
        Ledger: new LedgerWalletAdapter(),
    };

    // Función para actualizar el adaptador de wallet activo
    const updateWalletAdapter = (walletName) => {
        if (currentWalletAdapter) {
            currentWalletAdapter.removeAllListeners(); // Limpiar listeners del adaptador anterior
            if (currentWalletAdapter.connected) {
                currentWalletAdapter.disconnect(); // Desconectar si estaba conectado
            }
        }
        currentWalletAdapter = wallets[walletName];
        
        if (currentWalletAdapter) {
            currentWalletAdapter.on('connect', () => {
                statusDiv.textContent = `Wallet conectada: ${currentWalletAdapter.publicKey.toBase58()}`;
                connectedWalletInfo.textContent = `Conectado con: ${walletName} (${currentWalletAdapter.publicKey.toBase58()})`;
                verifyButton.textContent = 'Firmar Mensaje';
                verifyButton.disabled = false;
            });

            currentWalletAdapter.on('disconnect', () => {
                statusDiv.textContent = 'Wallet desconectada.';
                connectedWalletInfo.textContent = '';
                verifyButton.textContent = 'Conectar Wallet';
                verifyButton.disabled = false;
            });

            currentWalletAdapter.on('error', (error) => {
                console.error('Error del adaptador de wallet:', error);
                statusDiv.textContent = `❌ Error de wallet: ${error.message}`;
                verifyButton.disabled = false;
            });

            // Intentar conectar automáticamente si ya estaba autorizado (ej. Phantom)
            if (!currentWalletAdapter.connected && currentWalletAdapter.readyState === 'Installed') {
                // No llamar a connect aquí directamente, esperar al click del usuario
                // o manejarlo de forma más sofisticada si se desea auto-conexión.
            }
        }
        statusDiv.textContent = `Wallet seleccionada: ${walletName}. Haz clic en "Conectar Wallet".`;
        connectedWalletInfo.textContent = '';
        verifyButton.textContent = 'Conectar Wallet';
        verifyButton.disabled = false;
    };

    // Manejar cambio de selección de wallet
    walletSelect.addEventListener('change', (event) => {
        updateWalletAdapter(event.target.value);
    });

    // Inicializar con la wallet seleccionada por defecto (Phantom)
    updateWalletAdapter(walletSelect.value);

    verifyButton.addEventListener('click', async () => {
        if (!currentWalletAdapter) {
            statusDiv.textContent = "Error: No se ha seleccionado un adaptador de wallet.";
            return;
        }

        try {
            if (!currentWalletAdapter.connected) {
                statusDiv.textContent = 'Conectando wallet...';
                verifyButton.disabled = true;
                await currentWalletAdapter.connect();
                // Si la conexión falla, el error se capturará en el catch
                // Si tiene éxito, el listener 'connect' actualizará el estado
            }

            if (!currentWalletAdapter.connected) {
                throw new Error("No se pudo conectar la wallet.");
            }

            statusDiv.textContent = 'Obteniendo mensaje para firmar...';
            verifyButton.disabled = true;
            walletSelect.disabled = true;

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
            const signature = await currentWalletAdapter.signMessage(encodedMessage);

            // 3. Enviar la firma al backend para verificación
            statusDiv.textContent = 'Verificando firma...';
            const verificationResponse = await fetch('/api/verify-signature', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    public_key: currentWalletAdapter.publicKey.toBase58(),
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
            walletSelect.style.display = 'none';
            connectedWalletInfo.style.display = 'none';

        } catch (error) {
            console.error('Error en el proceso de verificación:', error);
            statusDiv.textContent = `❌ Error: ${error.message}`;
            verifyButton.disabled = false;
            walletSelect.disabled = false;
            // Si el error es de conexión, el botón debe volver a "Conectar Wallet"
            if (error.name === 'WalletNotConnectedError' || error.name === 'WalletConnectionError') {
                verifyButton.textContent = 'Conectar Wallet';
            } else if (error.name === 'WalletSignMessageError') {
                // Si el usuario cancela la firma, el botón debe volver a "Firmar Mensaje"
                verifyButton.textContent = 'Firmar Mensaje';
            }
        }
    });
});
