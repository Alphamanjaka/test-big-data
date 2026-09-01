from patient_platform.load.postgres_loader import PostgresLoader
from patient_platform.pipeline import run_pipeline


class FakeCursor:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, parameters):
        self.calls.append((query, parameters))


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_postgres_loader_writes_masters_and_identity_map(tmp_path):
    result = run_pipeline("data/raw", tmp_path /
                          "runtime.log", tmp_path / "audit.md")
    connection = FakeConnection()

    PostgresLoader(lambda: connection).load(
        result.patients, result.identity_map)

    assert len(connection.cursor_instance.calls) == 8
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert connection.cursor_instance.calls[0][1][0] == "PAT-0001"
    assert connection.cursor_instance.calls[-1][1][0] == "PAT-0002"
