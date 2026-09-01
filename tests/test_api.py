from patient_platform.api.app import app


def test_api_exposes_read_only_patient_routes():
    routes = {route.path for route in app.routes}

    assert {"/health", "/metrics", "/patients",
            "/patients/{master_patient_id}"} <= routes
