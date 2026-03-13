import asyncio

from app.telegram.bot import TenderBotApp


def main() -> None:
    app = TenderBotApp()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
