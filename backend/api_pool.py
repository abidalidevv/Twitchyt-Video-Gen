import time
from typing import Optional, Tuple, Dict, Any, List
from groq import Groq

from .config import load_api_keys, save_api_keys


class GroqPoolManager:
    def __init__(self):
        self.load_keys()

    def load_keys(self):
        data = load_api_keys()
        self.keys: List[Dict[str, Any]] = data.get("keys", [])
        self.current_idx: int = data.get("active_key_index", 0)
        if self.keys and self.current_idx >= len(self.keys):
            self.current_idx = 0

    def get_client(self) -> Tuple[Groq, str]:
        """Returns the next healthy Groq client and key ID."""
        self.load_keys()
        if not self.keys:
            raise ValueError("No Groq API keys available in the API Pool! Please add a key in the API Pool tab.")

        now = time.time()
        for i in range(len(self.keys)):
            idx = (self.current_idx + i) % len(self.keys)
            k = self.keys[idx]

            # Recover from rate limit cooldown after 60s
            if k.get("status") == "RATE_LIMITED":
                cooldown = k.get("rate_limited_until", 0)
                if now > cooldown:
                    k["status"] = "HEALTHY"
                    k["last_error"] = None

            if k.get("status") != "RATE_LIMITED":
                self.current_idx = idx
                k["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                k["total_transcriptions"] = k.get("total_transcriptions", 0) + 1
                self.save_keys()
                return Groq(api_key=k["key"]), k["id"]

        # If all rate limited, pick the first one and try
        k = self.keys[self.current_idx]
        return Groq(api_key=k["key"]), k["id"]

    def rotate_to_next(self, failed_key_id: str, reason: str = "Rate Limited (429)"):
        """Rotates to next available healthy key upon rate limit or failure."""
        self.load_keys()
        for k in self.keys:
            if k["id"] == failed_key_id:
                k["status"] = "RATE_LIMITED"
                k["last_error"] = reason
                k["rate_limited_until"] = time.time() + 60.0  # 60s cooldown

        if self.keys:
            self.current_idx = (self.current_idx + 1) % len(self.keys)
        self.save_keys()

    def test_key(self, api_key: str) -> Tuple[bool, int, str]:
        """Tests key validity and records round-trip latency in ms."""
        try:
            t0 = time.time()
            client = Groq(api_key=api_key)
            client.models.list()
            latency = int((time.time() - t0) * 1000)
            return True, latency, "Healthy"
        except Exception as e:
            return False, 0, str(e)

    def add_key(self, key_str: str, label: Optional[str] = None) -> Dict[str, Any]:
        self.load_keys()
        valid, latency, msg = self.test_key(key_str)
        key_id = f"key_{len(self.keys) + 1:02d}"
        new_entry = {
            "id": key_id,
            "label": label or f"Groq Key {len(self.keys) + 1}",
            "key": key_str,
            "status": "HEALTHY" if valid else "INVALID",
            "latency_ms": latency,
            "total_transcriptions": 0,
            "last_used": None,
            "last_error": None if valid else msg
        }
        self.keys.append(new_entry)
        self.save_keys()
        return new_entry

    def remove_key(self, key_id: str):
        self.load_keys()
        self.keys = [k for k in self.keys if k.get("id") != key_id and k.get("key") != key_id]
        if self.current_idx >= len(self.keys):
            self.current_idx = 0
        self.save_keys()


    def get_all_keys(self) -> List[Dict[str, Any]]:
        self.load_keys()
        masked = []
        for k in self.keys:
            item = dict(k)
            # Mask key for UI safety
            raw = item.get("key", "")
            if len(raw) > 12:
                item["masked_key"] = f"{raw[:6]}...{raw[-4:]}"
            else:
                item["masked_key"] = "gsk_***"
            masked.append(item)
        return masked

    def save_keys(self):
        data = load_api_keys()
        data["keys"] = self.keys
        data["active_key_index"] = self.current_idx
        save_api_keys(data)


groq_pool = GroqPoolManager()
