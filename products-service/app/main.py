from app.router import router
from fastapi import FastAPI

app = FastAPI(
    title='Product service',
    description='Сервис для CRUD операций с объявлениями',
    version='1.0.0'
)

app.include_router(router)


@app.get('/')
def root():
    """Корневой эндпоинт для проверки работоспособности"""
    return {
        'service': 'product service',
        'status': 'running',
        'endpoints': '/docs'
    }
