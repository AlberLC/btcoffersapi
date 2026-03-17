from enum import Enum


class Exchange(Enum):
    HODLHODL = 'HodlHodl'
    LNP2PBOT = 'lnp2pBot'
    ROBOSATS = 'RoboSats'


class NostrMessageType(Enum):
    CLOSE = 'CLOSE'
    EOSE = 'EOSE'
    EVENT = 'EVENT'
    NOTICE = 'NOTICE'
    REQ = 'REQ'


class PaymentMethod(Enum):
    BIZUM = 'Bizum'
    CARDLESS_CASH = 'Cardless cash'
    CREDIT_CARD = 'Credit card'
    INSTANT_SEPA = 'Instant SEPA'
    PAYPAL = 'PayPal'
    REVOLUT = 'Revolut'
    SEPA = 'SEPA'
    WISE = 'Wise'
