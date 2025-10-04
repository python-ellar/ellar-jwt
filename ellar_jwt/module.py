import json
import typing as t
from datetime import timedelta

from ellar.common import IModuleSetup, Module
from ellar.core import Config, ModuleSetup
from ellar.core.modules import DynamicModule, ModuleBase, ModuleRefBase
from ellar.di import ProviderConfig
from pydantic import AnyHttpUrl

from .schemas import JWTConfiguration
from .services import JWTService


@Module(exports=[JWTService, JWTConfiguration])
class JWTModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(
        cls,
        signing_secret_key: str,
        verifying_secret_key: str = "",
        algorithm: str = "HS256",
        audience: t.Optional[str] = None,
        issuer: t.Optional[str] = None,
        jwk_url: t.Optional[AnyHttpUrl] = None,
        leeway: t.Union[float, int, timedelta] = 0,
        jti: str = "jti",
        lifetime: t.Optional[timedelta] = None,
        json_encoder: t.Any = json.JSONEncoder,
    ) -> DynamicModule:
        configuration = JWTConfiguration(
            signing_secret_key=signing_secret_key,
            algorithm=algorithm,  # type: ignore[arg-type]
            audience=audience,
            issuer=issuer,
            jwk_url=jwk_url,
            leeway=leeway,
            jti=jti,
            lifetime=lifetime or timedelta(minutes=5),
            json_encoder=json_encoder,
        )

        return DynamicModule(
            cls,
            providers=[
                ProviderConfig(JWTService),
                ProviderConfig(JWTConfiguration, use_value=configuration),
            ],
        )

    @classmethod
    def register_setup(cls) -> ModuleSetup:
        return ModuleSetup(cls, inject=[Config], factory=cls.register_setup_factory)

    @staticmethod
    def register_setup_factory(
        module_ref: ModuleRefBase, config: Config
    ) -> DynamicModule:
        if config.get("JWT_CONFIG") and isinstance(config.JWT_CONFIG, dict):
            schema = JWTConfiguration(**dict(config.JWT_CONFIG))
            return DynamicModule(
                module_ref.module,
                providers=[
                    ProviderConfig(JWTService),
                    ProviderConfig(JWTConfiguration, use_value=schema),
                ],
            )
        raise RuntimeError("Could not find `JWT_CONFIG` in application config.")
