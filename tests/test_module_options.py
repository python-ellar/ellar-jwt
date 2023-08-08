from datetime import timedelta

import pytest
from ellar.testing import Test

from ellar_jwt import JWTModule, JWTService


def test_jwt_module_configuration_case_1():
    tm = Test.create_test_module(
        modules=[
            JWTModule.setup(
                algorithm="HS256",
                signing_secret_key="no_secret",
                issuer="https://ellar.com",
                lifetime=timedelta(minutes=30),
                leeway=timedelta(minutes=30),
                audience="openid-client-id",
            )
        ]
    )
    jwt_service: JWTService = tm.get(JWTService)

    token = jwt_service.sign({"sub": 23})
    payload = jwt_service.decode(token)

    assert payload["sub"] == 23


def test_jwt_module_configuration_case_2():
    tm = Test.create_test_module(
        modules=[JWTModule.register_setup()],
        config_module=dict(
            JWT_CONFIG=dict(
                algorithm="HS256",
                signing_secret_key="no_secret",
                issuer="https://ellar.com",
                lifetime=timedelta(minutes=30),
                leeway=None,
            )
        ),
    )
    jwt_service: JWTService = tm.get(JWTService)

    token = jwt_service.sign({"sub": 23})
    payload = jwt_service.decode(token)

    assert payload["sub"] == 23


def test_jwt_module_configuration_case_2_fails():
    tm = Test.create_test_module(
        modules=[JWTModule.register_setup()],
    )
    with pytest.raises(
        RuntimeError, match="Could not find `JWT_CONFIG` in application config."
    ):
        tm.get(JWTService)
