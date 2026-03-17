import datetime
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from enums import PaymentMethod


class AppSettings(BaseSettings):
    api_host: str | None = None
    api_port: int | None = None

    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / '.env')


class HodlHodlSettings(AppSettings):
    hodlhodl_offers_api_endpoint: str = 'https://hodlhodl.com/api/v1/offers'
    hodlhodl_offers_web_base_url: str = 'https://hodlhodl.com/offers'
    hodlhodl_pagination_size: int = 100
    hodlhodl_pagination_sleep: float = 1.0
    hodlhodl_payment_methods_ids: dict[PaymentMethod, set[str]] = {
        PaymentMethod.BIZUM: {'501'},
        PaymentMethod.CARDLESS_CASH: {'414', '571'},
        PaymentMethod.CREDIT_CARD: {'7'},
        PaymentMethod.INSTANT_SEPA: {'9081'},
        PaymentMethod.PAYPAL: {'16'},
        PaymentMethod.REVOLUT: {'52'},
        PaymentMethod.SEPA: {'4'},
        PaymentMethod.WISE: {'7559'}
    }


class LnP2pBotSettings(AppSettings):
    lnp2pbot_api_endpoint: str = 'https://api.lnp2pbot.com/orders'
    lnp2pbot_channel_name: str = 'p2plightning'
    lnp2pbot_loading_selector_timeout: float = 1000.0
    lnp2pbot_max_rating: float = 5.0
    lnp2pbot_message_selector_timeout: float = 5000.0
    lnp2pbot_nostr_fetch_attempts: int = 3
    lnp2pbot_nostr_events_limit: int = 300
    lnp2pbot_nostr_event_kind: int = 38383
    lnp2pbot_nostr_pagination_sleep: float = 0.3
    lnp2pbot_nostr_public_key: str = 'fcc2a0bd8f5803f6dd8b201a1ddb67a4b6e268371fe7353d41d2b6684af7a61e'
    lnp2pbot_nostr_relay_reconnect_sleep: float = datetime.timedelta(hours=1).total_seconds()
    lnp2pbot_nostr_relay_urls: tuple[str, ...] = (
        'wss://nos.lol',
        'wss://nostr-pub.wellorder.net',
        'wss://relay.damus.io',
        'wss://relay.mostro.network',
        'wss://relay.nostr.band'
    )
    lnp2pbot_nostr_subscription_id: str = 'offers'
    lnp2pbot_nostr_timeout: float = 5.0
    lnp2pbot_nostr_ws_heartbeat: float = 30.0
    lnp2pbot_scrape_attempts: int = 5
    lnp2pbot_web_url: str = f'https://t.me/s/{lnp2pbot_channel_name}?q=%23SELLEUR'


class MongoSettings(AppSettings):
    database_lock_expiration: datetime.timedelta = datetime.timedelta(seconds=30)
    database_name: str = 'btcoffers'
    indexes: dict[str, list[dict]] = {'offer': [{'name': 'id_1', 'keys': 'id', 'unique': True}]}
    mongo_username: str | None = None
    mongo_password: str | None = None


class RoboSatstSettings(AppSettings):
    robosats_coordinator_api_endpoint_template: str = '{}/api/book/?format=json'
    robosats_coordinators_url: str = (
        'https://raw.githubusercontent.com/RoboSats/robosats/refs/heads/main/frontend/static/federation.json'
    )
    robosats_coordinators_urls_attempts: int = 5
    robosats_readme_url: str = (
        'https://raw.githubusercontent.com/RoboSats/robosats/dc98a8e68cbe1793bb285d890ad4ca4bcaae499b/README.md'
    )
    robosats_url: str = 'http://RoboSatsy56bwqn56qyadmcxkx767hnabg4mihxlmgyt6if5gnuxvzad.onion'


class Config(HodlHodlSettings, LnP2pBotSettings, MongoSettings, RoboSatstSettings):
    offers_fetch_sleep: float = datetime.timedelta(minutes=5).total_seconds()
    payment_method_keywords: dict[PaymentMethod, tuple[str, ...]] = {
        PaymentMethod.BIZUM: ('bizum',),
        PaymentMethod.CREDIT_CARD: ('credit', 'credito'),
        PaymentMethod.HALCASH: ('cajero', 'efectivo', 'halcash'),
        PaymentMethod.INSTANT_SEPA: ('instant sepa', 'sepa instant'),  # check INSTANT_SEPA before SEPA
        PaymentMethod.PAYPAL: ('paypal',),
        PaymentMethod.REVOLUT: ('revolut',),
        PaymentMethod.SEPA: ('sepa',),
        PaymentMethod.WISE: ('wise',)
    }
    telegram_api_hash: str | None = None
    telegram_api_id: int | None = None
    telegram_user_session: str | None = None
    tor_proxy_url: str = 'socks5://localhost:9050'
    tor_request_sleep: float = 1.0
    yadio_api_endpoint: str = 'https://api.yadio.io/exrates/EUR'


config = Config()
