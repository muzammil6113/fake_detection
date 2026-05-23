"""
Pure Python blockchain engine — no Django imports.
Proof-of-Work: hash must start with '00' (difficulty=2).
"""
import hashlib
import json
import time

DIFFICULTY = 2
POW_PREFIX = "0" * DIFFICULTY


class Block:
    def __init__(self, index: int, data: dict, previous_hash: str, timestamp: float = None):
        self.index         = index
        self.data          = data
        self.previous_hash = previous_hash
        self.timestamp     = timestamp or time.time()
        self.nonce         = 0
        self.hash          = self._mine()

    def compute_hash(self) -> str:
        block_str = json.dumps({
            "index":         self.index,
            "data":          self.data,
            "previous_hash": self.previous_hash,
            "timestamp":     self.timestamp,
            "nonce":         self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()

    def _mine(self) -> str:
        h = self.compute_hash()
        while not h.startswith(POW_PREFIX):
            self.nonce += 1
            h = self.compute_hash()
        return h


def generate_product_hash(serial: str, model_id: int, ts: float = None) -> str:
    raw = f"{serial}::{model_id}::{ts or time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_unit_serial(model_code: str, index: int) -> str:
    code = model_code.upper().replace("-", "")[:8]
    return f"BV-{code}-{str(index).zfill(6)}"