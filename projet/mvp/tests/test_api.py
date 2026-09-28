from patient_platform.api.app import app


def _collect_routes(routes):
    paths = set()
    for route in routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        elif hasattr(route, "original_router"):
            paths |= _collect_routes(route.original_router.routes)
        elif hasattr(route, "routes"):
            paths |= _collect_routes(route.routes)
    return paths


def test_api_exposes_read_only_patient_routes():
    routes = _collect_routes(app.routes)

    assert {"/health", "/metrics", "/patients",
            "/patients/{master_patient_id}"} <= routes


def test_api_exposes_governance_routes():
    routes = _collect_routes(app.routes)

    assert {"/consent", "/consent/{master_patient_id}",
            "/users", "/audit"} <= routes
