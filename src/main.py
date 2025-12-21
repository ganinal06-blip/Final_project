import asyncio
from .bot_app import BotApp

async def main():
    app = BotApp()
    await app.start()

if __name__ == "__main__":
    asyncio.run(main())