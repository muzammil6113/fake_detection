"""
Django ORM bridge for blockchain engine.
All writes are atomic + thread-safe via select_for_update.
"""
import time
from django.db import transaction
from .engine import Block, POW_PREFIX
from .models import BlockRecord


def get_last_block():
    return BlockRecord.objects.order_by("-index").first()


@transaction.atomic
def add_block(event_type, product_unit_serial, actor_username, actor_role, extra_data=None):
    last          = BlockRecord.objects.select_for_update().order_by("-index").first()
    index         = (last.index + 1) if last else 0
    previous_hash = last.block_hash if last else ("0" * 64)

    data = {
        "event":  event_type,
        "serial": product_unit_serial,
        "actor":  actor_username,
        "role":   actor_role,
        "ts":     time.time(),
        **(extra_data or {}),
    }

    block = Block(index=index, data=data, previous_hash=previous_hash)

    return BlockRecord.objects.create(
        index=block.index,
        block_hash=block.hash,
        previous_hash=block.previous_hash,
        nonce=block.nonce,
        timestamp=block.timestamp,
        event_type=event_type,
        product_unit_serial=product_unit_serial,
        actor_username=actor_username,
        actor_role=actor_role,
        extra_data=extra_data or {},
    )


def validate_chain():
    records = list(BlockRecord.objects.order_by("index"))
    if not records:
        return True, "Chain is empty."

    for i, rec in enumerate(records):
        b               = Block.__new__(Block)
        b.index         = rec.index
        b.previous_hash = rec.previous_hash
        b.timestamp     = rec.timestamp
        b.nonce         = rec.nonce
        b.data          = {
            "event": rec.event_type, "serial": rec.product_unit_serial,
            "actor": rec.actor_username, "role": rec.actor_role,
            "ts": rec.timestamp, **rec.extra_data,
        }
        b.hash = rec.block_hash

        if b.compute_hash() != rec.block_hash:
            return False, f"Block #{rec.index} hash mismatch — chain tampered!"
        if not rec.block_hash.startswith(POW_PREFIX):
            return False, f"Block #{rec.index} fails Proof-of-Work!"
        if i > 0 and rec.previous_hash != records[i - 1].block_hash:
            return False, f"Block #{rec.index} broken link — chain corrupted!"

    return True, f"Chain VALID — {len(records)} blocks verified successfully."


def get_unit_history(serial):
    return list(BlockRecord.objects.filter(product_unit_serial=serial).order_by("index"))