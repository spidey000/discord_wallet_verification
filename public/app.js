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
    const { getWallets } = window.solanaWalletAdapterWallets;
    const wallets = getWallets();
    const walletMap = new Map();

    // Populate the dropdown with available wallets
    wallets.forEach(wallet => {
        const option = document.createElement('option');
        option.value = wallet.adapter.name;
        option.textContent = wallet.adapter.name;
        walletSelect.appendChild(option);
        walletMap.set(wallet.adapter.name, wallet.adapter);
    });

    // Function to update the active wallet adapter
    const updateWalletAdapter = (walletName) => {
        if (currentWalletAdapter) {
            currentWalletAdapter.removeAllListeners(); // Clean up listeners from previous adapter
            if (currentWalletAdapter.connected) {
                currentWalletAdapter.disconnect(); // Disconnect if it was connected
            }
        }
        currentWalletAdapter = walletMap.get(walletName);
        
        if (currentWalletAdapter) {
            currentWalletAdapter.on('connect', () => {
                statusDiv.textContent = `Wallet connected: ${currentWalletAdapter.publicKey.toBase58()}`;
                connectedWalletInfo.textContent = `Connected with: ${walletName} (${currentWalletAdapter.publicKey.toBase58()})`;
                verifyButton.textContent = 'Sign Message';
                verifyButton.disabled = false;
            });

            currentWalletAdapter.on('disconnect', () => {
                statusDiv.textContent = 'Wallet disconnected.';
                connectedWalletInfo.textContent = '';
                verifyButton.textContent = 'Connect Wallet';
                verifyButton.disabled = false;
            });

            currentWalletAdapter.on('error', (error) => {
                console.error('Wallet adapter error:', error);
                statusDiv.textContent = `❌ Wallet error: ${error.message}`;
                verifyButton.disabled = false;
            });

            // Attempt to auto-connect if already authorized (e.g., Phantom)
            if (!currentWalletAdapter.connected && currentWalletAdapter.readyState === 'Installed') {
                // Do not call connect here directly, wait for user click
            }
        }
        statusDiv.textContent = `Wallet selected: ${walletName}. Click "Connect Wallet".`;
        connectedWalletInfo.textContent = '';
        verifyButton.textContent = 'Connect Wallet';
        verifyButton.disabled = false;
    };

    // Handle wallet selection change
    walletSelect.addEventListener('change', (event) => {
        updateWalletAdapter(event.target.value);
    });

    // Initialize with the default selected wallet (first in the list)
    if (walletSelect.options.length > 0) {
        updateWalletAdapter(walletSelect.value);
    } else {
        statusDiv.textContent = "No Solana wallets found. Please install a wallet extension.";
        verifyButton.disabled = true;
        walletSelect.disabled = true;
    }

    verifyButton.addEventListener('click', async () => {
        if (!currentWalletAdapter) {
            statusDiv.textContent = "Error: No wallet adapter selected.";
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
