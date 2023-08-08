import typing as t
from datetime import datetime, timedelta
from uuid import uuid4

from .schemas import JWTConfiguration
from .util import aware_utcnow, datetime_to_epoch


class Token:
    __slots__ = ("current_time", "lifetime", "jwt_config", "payload")

    def __init__(self, jwt_config: JWTConfiguration) -> None:
        self.current_time = aware_utcnow()
        self.lifetime = jwt_config.lifetime
        self.jwt_config = jwt_config
        self.payload: t.Dict = {}

    def build(self, payload: t.Dict) -> t.Dict:
        # Set "exp" and "iat" claims with default value
        self.set_exp()
        self.set_iat()

        # Set "jti" claim
        self.set_jti()
        self.payload.update(payload)

        if self.jwt_config.audience is not None:
            self.payload["aud"] = self.jwt_config.audience
        if self.jwt_config.issuer is not None:
            self.payload["iss"] = self.jwt_config.issuer

        return self.payload

    def set_jti(self) -> None:
        """
        Populates the configured jti claim of a token with a string where there
        is a negligible probability that the same string will be chosen at a
        later time.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.7
        """
        self.payload[self.jwt_config.jti] = uuid4().hex

    def set_exp(
        self,
        claim: str = "exp",
        from_time: t.Optional[datetime] = None,
        lifetime: t.Optional[t.Union[datetime, timedelta]] = None,
    ) -> None:
        """
        Updates the expiration time of a token.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.4
        """
        if from_time is None:
            from_time = self.current_time

        if lifetime is None:
            lifetime = self.lifetime

        self.payload[claim] = datetime_to_epoch(
            from_time + lifetime  # type:ignore[operator]
        )

    def set_iat(self, claim: str = "iat", at_time: t.Optional[datetime] = None) -> None:
        """
        Updates the time at which the token was issued.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.6
        """
        if at_time is None:
            at_time = self.current_time

        self.payload[claim] = datetime_to_epoch(at_time)
