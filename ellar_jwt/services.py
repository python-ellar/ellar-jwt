import typing as t
from datetime import timedelta

import anyio
import jwt
from ellar.di import injectable
from jwt import InvalidAlgorithmError, InvalidTokenError, PyJWKClient, PyJWKClientError

from .exceptions import JWTTokenException
from .schemas import JWTConfiguration
from .token import Token

__all__ = ["JWTService"]


@injectable
class JWTService:
    def __init__(self, jwt_config: JWTConfiguration) -> None:
        self.jwt_config = jwt_config

        self.jwks_client = (
            PyJWKClient(self.jwt_config.jwk_url) if self.jwt_config.jwk_url else None
        )
        self.leeway = self.jwt_config.leeway

    def get_leeway(self) -> timedelta:
        if self.leeway is None:
            return timedelta(seconds=0)
        elif isinstance(self.leeway, (int, float)):
            return timedelta(seconds=self.leeway)
        elif isinstance(self.leeway, timedelta):
            return self.leeway

    def get_verifying_key(self, token: t.Any) -> bytes:
        if self.jwt_config.algorithm.startswith("HS"):
            return self.jwt_config.signing_secret_key.encode()

        if self.jwks_client:
            try:
                p_jwk = self.jwks_client.get_signing_key_from_jwt(token)
                return p_jwk.key  # type:ignore[no-any-return]
            except PyJWKClientError as ex:
                raise JWTTokenException("Token is invalid or expired") from ex

        return self.jwt_config.verifying_secret_key.encode()

    def sign(self, payload: dict, headers: t.Dict[str, t.Any] = None) -> str:
        """
        Returns an encoded token for the given payload dictionary.
        """

        jwt_payload = Token(jwt_config=self.jwt_config).build(payload.copy())

        return jwt.encode(
            jwt_payload,
            self.jwt_config.signing_secret_key,
            algorithm=self.jwt_config.algorithm,
            json_encoder=self.jwt_config.json_encoder,
            headers=headers,
        )

    async def sign_async(
        self, payload: dict, headers: t.Dict[str, t.Any] = None
    ) -> str:
        return await anyio.to_thread.run_sync(self.sign, payload, headers)

    def decode(self, token: str, verify: bool = True) -> t.Dict[str, t.Any]:
        """
        Performs a validation of the given token and returns its payload
        dictionary.

        Raises a `TokenBackendError` if the token is malformed, if its
        signature check fails, or if its 'exp' claim indicates it has expired.
        """
        try:
            return jwt.decode(  # type: ignore[no-any-return]
                token,
                self.get_verifying_key(token),
                algorithms=[self.jwt_config.algorithm],
                audience=self.jwt_config.audience,
                issuer=self.jwt_config.issuer,
                leeway=self.get_leeway(),
                options={
                    "verify_aud": self.jwt_config.audience is not None,
                    "verify_signature": verify,
                },
            )
        except InvalidAlgorithmError as ex:
            raise JWTTokenException("Invalid algorithm specified") from ex
        except InvalidTokenError as ex:
            raise JWTTokenException("Token is invalid or expired") from ex

    async def decode_async(self, token: str, verify: bool = True) -> t.Dict[str, t.Any]:
        return await anyio.to_thread.run_sync(self.decode, token, verify)
