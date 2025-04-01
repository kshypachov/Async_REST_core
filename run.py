import logging
from config.config import load_config, configure_logging, get_logger

try:
    load_config("config.ini")
    configure_logging()
    logger = get_logger(__name__)
    logger.info("Configuration loaded")

except ValueError as e:
    print(f"Failed to load configuration: {e}")
    exit(1)

# Только теперь импортируем FastAPI и роутеры
from fastapi import FastAPI
from routers.external import external
from routers.internal import internal

app = FastAPI()
# app.mount("/external", external)
# app.mount("/internal", internal)
app.include_router(external, prefix="/external", tags=["external"])
app.include_router(internal, prefix="/internal", tags=["internal"])



if __name__ == "__main__":
    import uvicorn
    print("Starting REST APP as module")
    uvicorn.run(app, host="0.0.0.0", port=8000)