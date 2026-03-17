from collections import defaultdict

import flanautils

from config import config
from enums import PaymentMethod


def _generate_ngrams(text: str, max_n: int) -> defaultdict[int, set[str]]:
    ngrams = defaultdict(set)

    words = text.split()

    for n in range(1, max_n + 1):
        n_ngrams = set()

        for i in range(len(words) - n + 1):
            n_ngrams.add(' '.join(words[i:i + n]))

        if n_ngrams:
            ngrams[n] = n_ngrams

    return ngrams


def _normalize_text(text: str) -> str:
    return ' '.join(
        ''.join(
            character if character.isalnum() or character.isspace() else ' '
            for character in flanautils.remove_accents(text.lower(), lazy=True)
        ).split()
    )


def find_payment_methods(text: str) -> list[PaymentMethod]:
    normalized_text = _normalize_text(text)
    text_ngrams = _generate_ngrams(normalized_text, config.payment_method_keyword_max_words)
    payment_methods = []

    for payment_method, payment_method_keywords_groups in config.payment_methods_keywords_groups.items():
        for group_word_count, payment_method_keywords_group in payment_method_keywords_groups:
            for payment_method_keyword in payment_method_keywords_group:
                for text_ngram in text_ngrams[group_word_count]:
                    if flanautils.cartesian_product_string_matching(
                        (payment_method_keyword,),
                        (text_ngram,),
                        min_score=config.keyword_matching_min_score
                    ):
                        if payment_method not in payment_methods:
                            payment_methods.append(payment_method)

                        normalized_text = normalized_text.replace(text_ngram, '')
                        text_ngrams = _generate_ngrams(normalized_text, config.payment_method_keyword_max_words)

    return payment_methods
