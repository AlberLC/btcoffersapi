from enum import Enum


class Exchange(Enum):
    HODLHODL = 'HodlHodl'
    LNP2PBOT = 'lnp2pBot'
    ROBOSATS = 'RoboSats'


class PaymentMethod(Enum):
    CREDIT_CARD = 'Credit card'
    BIZUM = 'Bizum'
    HALCASH = 'HalCash'
    PAYPAL = 'PayPal'
    REVOLUT = 'Revolut'
    SEPA = 'SEPA'
    SEPA_INSTANT = 'Instant SEPA'
