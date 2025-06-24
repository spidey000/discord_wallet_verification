# Discord Wallet Verification

A Discord bot and web API system for verifying cryptocurrency wallets and managing user verification processes.

## Features

- Discord bot integration for user interaction
- Wallet verification system
- Web API for external integrations
- User management and verification tracking
- Secure authentication and authorization

## Project Structure

```
discord_verification/
├── api/           # FastAPI web application
├── bot/           # Discord bot implementation
├── public/        # Static files and frontend assets
├── scripts/       # Utility scripts and tools
├── requirements.txt
├── documentation.md
└── README.md
```

## Prerequisites

- Python 3.8+
- Discord Bot Token
- Supabase account and credentials
- Solana wallet integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord_wallet_verification.git
cd discord_wallet_verification
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Configure your Discord bot and Supabase credentials in the environment file.

## Usage

### Running the Discord Bot
```bash
python bot/main.py
```

### Running the Web API
```bash
uvicorn api.main:app --reload
```

## Configuration

Create a `.env` file with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SOLANA_RPC_URL=your_solana_rpc_url
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team. 