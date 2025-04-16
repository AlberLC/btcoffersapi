import datetime
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from btcoffersapi.api.schemas.enums import PaymentMethod


class Config(BaseSettings):
    api_host: str | None = None
    api_port: int | None = None
    database_lock_expiration: datetime.timedelta = datetime.timedelta(seconds=30)
    database_lock_sleep: float = 0.5
    database_name: str = 'btcoffers'
    fetch_offers_every: datetime.timedelta = datetime.timedelta(minutes=1)
    hodlhodl_offers_endpoint: str = 'https://hodlhodl.com/api/v1/offers'
    hodlhodl_payment_methods: dict[str, PaymentMethod] = {
        '4': PaymentMethod.SEPA,
        '7': PaymentMethod.CREDIT_CARD,
        '16': PaymentMethod.PAYPAL,
        '52': PaymentMethod.REVOLUT,
        '414': PaymentMethod.HALCASH,
        '501': PaymentMethod.BIZUM,
        '9081': PaymentMethod.SEPA_INSTANT
    }
    lnp2pbot_payment_methods: dict[str, PaymentMethod] = {
        'credit': PaymentMethod.CREDIT_CARD,
        'credito': PaymentMethod.CREDIT_CARD,
        'paypal': PaymentMethod.PAYPAL,
        'revolut': PaymentMethod.REVOLUT,
        'halcash': PaymentMethod.HALCASH,
        'bizum': PaymentMethod.BIZUM,
        'sepa instant': PaymentMethod.SEPA_INSTANT,
        'instant sepa': PaymentMethod.SEPA_INSTANT,
        'sepa': PaymentMethod.SEPA  # check SEPA after Instant SEPA
    }
    mongo_username: str | None = None
    mongo_password: str | None = None
    robosats_coordinator_endpoint_template: str = '{}/api/book/?format=json'
    robosats_coordinators_url: str = 'https://raw.githubusercontent.com/RoboSats/robosats/refs/heads/main/frontend/static/federation.json'
    robosats_payment_methods: dict[str, PaymentMethod] = {
        'Paypal Friends & Family': PaymentMethod.PAYPAL,
        'Revolut': PaymentMethod.REVOLUT,
        'HalCash': PaymentMethod.HALCASH,
        'Bizum': PaymentMethod.BIZUM,
        'Instant SEPA': PaymentMethod.SEPA_INSTANT
    }
    telegram_api_hash: str | None = None
    telegram_api_id: int | None = None
    telegram_user_session: str | None = None
    tor_proxy_url: str = 'socks5://localhost:9050'
    yadio_api_endpoint: str = 'https://api.yadio.io/exrates/EUR'

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / '.env')


config = Config()
