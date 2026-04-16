"""
Точка входа для запуска Rating Service.
Импортирует приложение из app.main для работы с Docker.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)