import logging
from config.config import load_config, configure_logging

try:
    load_config("config.ini")
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded")
    logger.info("Starting REST APP")

except ValueError as e:
    logging.critical(f"Failed to load configuration: {e}")
    exit(1)

# Только теперь импортируем FastAPI и роутеры
from fastapi import FastAPI
from routers.external import external
from routers.internal import internal

app = FastAPI()
app.mount("/external", external)
app.mount("/internal", internal)



if __name__ == "__main__":
    import uvicorn
    print("Starting REST APP as module")
    uvicorn.run(app, host="0.0.0.0", port=8000)