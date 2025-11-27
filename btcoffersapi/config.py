import datetime
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from api.schemas.enums import PaymentMethod


class Config(BaseSettings):
    api_host: str | None = None
    api_port: int | None = None
    database_lock_expiration: datetime.timedelta = datetime.timedelta(seconds=30)
    database_name: str = 'btcoffers'
    fetch_offers_every: datetime.timedelta = datetime.timedelta(minutes=5)
    hodlhodl_offers_endpoint: str = 'https://hodlhodl.com/api/v1/offers'
    hodlhodl_pagination_size: int = 100
    hodlhodl_payment_methods: dict[str, PaymentMethod] = {
        '4': PaymentMethod.SEPA,
        '7': PaymentMethod.CREDIT_CARD,
        '16': PaymentMethod.PAYPAL,
        '52': PaymentMethod.REVOLUT,
        '414': PaymentMethod.HALCASH,
        '501': PaymentMethod.BIZUM,
        '9081': PaymentMethod.SEPA_INSTANT
    }
    lnp2pbot_api_endpoint: str = 'https://api.lnp2pbot.com/orders'
    lnp2pbot_channel_name: str = 'p2plightning'
    lnp2pbot_payment_method_keywords: dict[PaymentMethod, tuple[str, ...]] = {
        PaymentMethod.CREDIT_CARD: ('credit', 'credito'),
        PaymentMethod.PAYPAL: ('paypal',),
        PaymentMethod.REVOLUT: ('revolut',),
        PaymentMethod.HALCASH: ('cajero', 'efectivo', 'halcash'),
        PaymentMethod.BIZUM: ('bizum',),
        PaymentMethod.SEPA_INSTANT: ('instant sepa', 'sepa instant'),
        PaymentMethod.SEPA: ('sepa',)  # check SEPA after Instant SEPA
    }
    lnp2pbot_web_url: str = f'https://t.me/s/{lnp2pbot_channel_name}?q=%23SELLEUR'
    mongo_username: str | None = None
    mongo_password: str | None = None
    robosats_coordinator_api_endpoint_template: str = '{}/api/book/?format=json'
    robosats_coordinators_url: str = 'https://raw.githubusercontent.com/RoboSats/robosats/refs/heads/main/frontend/static/federation.json'
    robosats_coordinators_urls_attempts: int = 5
    robosats_payment_method_keywords: dict[PaymentMethod, tuple[str, ...]] = {
        PaymentMethod.PAYPAL: ('Paypal Friends & Family',),
        PaymentMethod.REVOLUT: ('Revolut',),
        PaymentMethod.HALCASH: ('HalCash',),
        PaymentMethod.BIZUM: ('Bizum',),
        PaymentMethod.SEPA_INSTANT: ('Instant SEPA',)
    }
    telegram_api_hash: str | None = None
    telegram_api_id: int | None = None
    telegram_user_session: str | None = None
    tor_proxy_url: str = 'socks5://localhost:9050'
    tor_request_delay: float = 1
    yadio_api_endpoint: str = 'https://api.yadio.io/exrates/EUR'

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / '.env')


config = Config()
