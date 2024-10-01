# main.py
import logging
from config.config import load_config, configure_logging
from fastapi import FastAPI



try:
    load_config("config.ini")
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded")
    logger.info("Starting REST APP")
except ValueError as e:
    logging.critical(f"Failed to load configuration: {e}")
    exit(1)

from routers.external import external
from routers.internal import internal
# Инициализация основного приложения FastAPI
app = FastAPI()

# Включение приложения для внешних пользователей с документацией по адресу /external/docs
app.mount("/external", external)

# Включение приложения для внутренней системы с документацией по адресу /internal/docs
app.mount("/internal", internal)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)