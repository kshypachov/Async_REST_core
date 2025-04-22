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
from fastapi import FastAPI, Request
from routers.external import external
from routers.internal import internal

app = FastAPI()
# app.mount("/external", external)
# app.mount("/internal", internal)
app.include_router(external, prefix="/external", tags=["external"])
app.include_router(internal, prefix="/internal", tags=["internal"])

@app.middleware("http")
async def log_request_headers(request: Request, call_next):
    headers = dict(request.headers)
    logger.info("Заголовки запиту:")
    for header_key, header_value in headers.items():
        logger.info(f"    {header_key}: {header_value}")

    # Отримання query параметрів
    query_params = request.query_params
    query_id = query_params.get("queryId")
    user_id = query_params.get("userId")

    if query_id:
        logger.info(f"Значення параметру запиту queryId: {query_id}")
    if user_id:
        logger.info(f"Значення параметру запиту userId: {user_id}")

    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    print("Starting REST APP as module")
    uvicorn.run(app, host="0.0.0.0", port=8000)