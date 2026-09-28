import asyncio

from patient_platform.api.audit import AuditMiddleware


def async_result(coro):
    return asyncio.run(coro)


def test_audit_middleware_records_access(monkeypatch):
    inserted = []

    class Cursor:
        def __init__(self):
            self.executed = None

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, query, params=None):
            inserted.append((query, params))

    class Connection:
        def __init__(self):
            self.committed = False
            self.closed = False

        def cursor(self):
            return Cursor()

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    conn = Connection()

    from patient_platform.api import audit as audit_module
    monkeypatch.setattr(audit_module, "connection_factory", lambda: conn)

    async def downstream(scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        })
        await send({"type": "http.response.body", "body": b""})

    middleware = AuditMiddleware(downstream)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/metrics",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "query_string": b"",
        "scheme": "http",
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        pass

    asyncio.run(middleware(scope, receive, send))

    assert inserted, "L'audit doit etre enregistre"
    query, params = inserted[0]
    assert "INSERT INTO access_audit" in query
    assert params[1] == "anonymous"
    assert params[2] == "/metrics"
    assert params[3] == "GET"
    assert conn.committed is True
