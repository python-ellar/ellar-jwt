import json
import typing as t
from datetime import timedelta

from ellar.common import Serializer
from ellar.pydantic import AnyUrl, Field, field_validator
from jwt import algorithms


class JWTConfiguration(Serializer):
    algorithm: t.Literal[
        "HS256",
        "HS384",
        "HS512",
        "RS256",
        "RS384",
        "RS512",
        "ES256",
        "ES384",
        "ES512",
    ] = "HS256"
    verifying_secret_key: str = ""
    leeway: t.Optional[t.Union[float, int, timedelta]] = 0

    signing_secret_key: str
    audience: t.Optional[str] = Field(None)

    issuer: t.Optional[str] = Field(None)
    jwk_url: t.Optional[AnyUrl] = Field(None)

    jti: t.Optional[str] = Field("jti")
    lifetime: timedelta = Field(timedelta(minutes=5))

    json_encoder: t.Any = Field(default=json.JSONEncoder)

    @field_validator("algorithm", mode="before")
    def _validate_algorithm(cls, value: str) -> str:
        """
        Ensure that the nominated algorithm is recognized, and that cryptography is installed for those
        algorithms that require it
        """

        if value in algorithms.requires_cryptography and not algorithms.has_crypto:
            raise ValueError(f"You must have cryptography installed to use {value}.")

        return value
