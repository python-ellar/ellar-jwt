import functools
import typing as t
from datetime import timedelta

import anyio
import jwt
from ellar.common import serialize_object
from ellar.core import Config
from ellar.di import injectable
from jwt import InvalidAlgorithmError, InvalidTokenError, PyJWKClient, PyJWKClientError

from .exceptions import JWTTokenException
from .schemas import JWTConfiguration
from .token import Token

__all__ = ["JWTService"]


@injectable
class JWTService:
    def __init__(self, jwt_config: JWTConfiguration, config: Config) -> None:
        self.jwt_config = jwt_config
        self._encoders = config.SERIALIZER_CUSTOM_ENCODER

    def get_jwks_client(self, jwt_config: JWTConfiguration) -> t.Optional[PyJWKClient]:
        jwks_client = (
            PyJWKClient(str(jwt_config.jwk_url)) if jwt_config.jwk_url else None
        )
        return jwks_client

    def get_leeway(self, jwt_config: JWTConfiguration) -> timedelta:
        if jwt_config.leeway is None:
            return timedelta(seconds=0)
        elif isinstance(jwt_config.leeway, (int, float)):
            return timedelta(seconds=jwt_config.leeway)
        elif isinstance(jwt_config.leeway, timedelta):
            return jwt_config.leeway

    def get_verifying_key(self, token: t.Any, jwt_config: JWTConfiguration) -> bytes:
        if self.jwt_config.algorithm.startswith("HS"):
            return jwt_config.signing_secret_key.encode()

        jwks_client = self.get_jwks_client(jwt_config)
        if jwks_client:
            try:
                p_jwk = jwks_client.get_signing_key_from_jwt(token)
                return p_jwk.key  # type:ignore[no-any-return]
            except PyJWKClientError as ex:
                raise JWTTokenException("Token is invalid or expired") from ex

        return jwt_config.verifying_secret_key.encode()

    def _merge_configurations(self, **jwt_config: t.Any) -> JWTConfiguration:
        jwt_config_default = self.jwt_config.dict()
        jwt_config_default.update(jwt_config)
        return JWTConfiguration(**jwt_config_default)

    def sign(
        self,
        payload: dict,
        headers: t.Optional[t.Dict[str, t.Any]] = None,
        **jwt_config: t.Any,
    ) -> str:
        """
        Returns an encoded token for the given payload dictionary.
        """
        _jwt_config = self._merge_configurations(**jwt_config)
        jwt_payload = Token(jwt_config=_jwt_config).build(
            serialize_object(payload.copy(), encoders=self._encoders)
        )

        return jwt.encode(
            jwt_payload,
            _jwt_config.signing_secret_key,
            algorithm=_jwt_config.algorithm,
            json_encoder=_jwt_config.json_encoder,
            headers=headers,
        )

    async def sign_async(
        self,
        payload: dict,
        headers: t.Optional[t.Dict[str, t.Any]] = None,
        **jwt_config: t.Any,
    ) -> str:
        func = self.sign
        if jwt_config:
            func = functools.partial(self.sign, **jwt_config)
        return await anyio.to_thread.run_sync(func, payload, headers)

    def decode(
        self, token: str, verify: bool = True, **jwt_config: t.Any
    ) -> t.Dict[str, t.Any]:
        """
        Performs a validation of the given token and returns its payload
        dictionary.

        Raises a `TokenBackendError` if the token is malformed, if its
        signature check fails, or if its 'exp' claim indicates it has expired.
        """
        try:
            _jwt_config = self._merge_configurations(**jwt_config)
            return jwt.decode(
                token,
                self.get_verifying_key(token, _jwt_config),  # type:ignore[arg-type]
                algorithms=[_jwt_config.algorithm],
                audience=_jwt_config.audience,
                issuer=_jwt_config.issuer,
                leeway=self.get_leeway(_jwt_config),
                options={
                    "verify_aud": _jwt_config.audience is not None,
                    "verify_signature": verify,
                },
            )
        except InvalidAlgorithmError as ex:
            raise JWTTokenException("Invalid algorithm specified") from ex
        except InvalidTokenError as ex:
            raise JWTTokenException("Token is invalid or expired") from ex

    async def decode_async(
        self, token: str, verify: bool = True, **jwt_config: t.Any
    ) -> t.Dict[str, t.Any]:
        func = self.decode
        if jwt_config:
            func = functools.partial(self.decode, **jwt_config)
        return await anyio.to_thread.run_sync(func, token, verify)
