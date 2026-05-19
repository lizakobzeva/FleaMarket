import time

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.observability import (
    CorrelationIDMiddleware,
    MetricsMiddleware,
    logger,
    setup_logging,
)
from app.router import router

setup_logging()

app = FastAPI(
    title='Product service',
    description='Сервис для CRUD операций с объявлениями',
    version='1.0.0',
)

app.add_middleware(MetricsMiddleware)
app.add_middleware(CorrelationIDMiddleware)

app.include_router(router)


@app.get('/')
def root():
    """Корневой эндпоинт для проверки работоспособности"""
    logger.info('Health check')
    return {
        'service': 'product service',
        'status': 'running',
        'endpoints': '/docs',
    }


@app.get('/metrics')
async def get_metrics():
    """Эндпоинт для Prometheus."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get('/test/error')
async def test_error():
    """Тестовый эндпоинт: всегда 500 (проверка error rate)."""
    logger.error('Test error endpoint invoked')
    raise HTTPException(status_code=500, detail='Тестовая ошибка')


@app.get('/test/slow')
async def test_slow():
    """Тестовый эндпоинт: задержка 2 с (проверка latency)."""
    logger.info('Slow test endpoint started')
    time.sleep(2)
    logger.info('Slow test endpoint finished')
    return {'status': 'ok', 'message': 'Медленный ответ после 2 секунд'}
