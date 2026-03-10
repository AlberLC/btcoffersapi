import flanautils

from config import config
from enums import PaymentMethod


def find_payment_methods(text: str) -> list[PaymentMethod]:
    payment_methods = []
    normalized_text = flanautils.remove_accents(text.lower())

    for payment_method, payment_method_names in config.payment_method_keywords.items():
        if payment_method in payment_methods:
            continue

        for payment_method_name in payment_method_names:
            if payment_method_name in normalized_text:
                if payment_method_name == 'instant sepa':
                    normalized_text = normalized_text.replace('instant sepa', '')

                if payment_method_name == 'sepa instant':
                    normalized_text = normalized_text.replace('sepa instant', '')

                payment_methods.append(payment_method)
                break

    return payment_methods
