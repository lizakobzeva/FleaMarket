import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.metrics import REQUEST_COUNT, REQUEST_LATENCY

correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

_LOG_RECORD_STANDARD = frozenset(logging.LogRecord('', 0, '', 0, '', (), None).__dict__)


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        correlation_id = getattr(record, 'correlation_id', None) or correlation_id_var.get()
        if correlation_id:
            log_entry['correlation_id'] = correlation_id

        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_STANDARD or key.startswith('_') or value is None:
                continue
            if key in log_entry:
                continue
            log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def setup_logging() -> None:
    if logging.root.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    handler.addFilter(CorrelationFilter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)


logger = logging.getLogger('rating-service')


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        return response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get('X-Request-ID', str(uuid4()))
        request.state.correlation_id = correlation_id
        token = correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(token)

        response.headers['X-Request-ID'] = correlation_id
        return response
