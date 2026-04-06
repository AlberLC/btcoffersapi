import datetime
import hashlib
import json
from collections.abc import Sequence
from typing import Any

import coincurve


class NostrEvent:
    def __init__(self, raw_event: dict[str, Any]) -> None:
        self.content: str | None = raw_event.get('content')
        self.created_at: int | None = raw_event.get('created_at')
        self.id: str | None = raw_event.get('id')
        self.kind: int | None = raw_event.get('kind')
        self.public_key: str | None = raw_event.get('pubkey')
        self.signature: str | None = raw_event.get('sig')
        self.raw_tags: Sequence[Sequence[str]] = raw_event.get('tags', ())
        self.tags: dict[str, Any] = {tag[0]: self._normalize_tag_values(tag[1:]) for tag in self.raw_tags}

    @staticmethod
    def _normalize_tag_values(tag_values: Sequence) -> tuple:
        if len(tag_values) == 1:
            tag_value = tag_values[0]
            return tag_value.lower() if isinstance(tag_value, str) else tag_value
        else:
            return tuple(tag_value.lower() if isinstance(tag_value, str) else tag_value for tag_value in tag_values)

    def compute_event_id(self) -> str:
        serialized = json.dumps(
            [0, self.public_key, self.created_at, self.kind, self.raw_tags, self.content],
            separators=(',', ':'),
            ensure_ascii=False
        )

        return hashlib.sha256(serialized.encode()).hexdigest()

    @property
    def is_valid(self) -> bool:
        if not self.id or not self.public_key or not self.signature:
            return False

        computed_event_id = self.compute_event_id()

        if computed_event_id != self.id:
            return False

        public_key_bytes = bytes.fromhex(self.public_key)
        signature_bytes = bytes.fromhex(self.signature)
        computed_event_id_bytes = bytes.fromhex(computed_event_id)

        return coincurve.PublicKeyXOnly(public_key_bytes).verify(signature_bytes, computed_event_id_bytes)


class NostrOfferEvent(NostrEvent):
    @property
    def is_valid(self) -> bool:
        return (
            super().is_valid
            and
            self.tags
            and
            self.tags.get('d')
            and
            self.tags.get('s')
            and
            self.tags.get('k') == 'sell'
            and
            self.tags.get('f') == 'eur'
            and
            (
                not (expiration := self.tags.get('expiration'))
                or
                expiration.isdigit()
                and
                datetime.datetime.now(datetime.UTC) < datetime.datetime.fromtimestamp(int(expiration), datetime.UTC)
            )
            and
            'mainnet' in self.tags.get('network', ())
        )
