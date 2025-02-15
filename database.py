import json
import random
from datetime import datetime, timedelta
from typing import Dict, Optional

from filelock import FileLock

from config import Config


class JSONDatabase:
    def __init__(self, filename: str):
        self.filename = filename
        self.file_lock = FileLock(self.filename + ".lock")

        self.data = self._load_data()

    def _load_data(self) -> Dict:
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "redirects": {},
                "temp_redirects": {},
                "users": {},
                "stats": {}
            }
        except json.JSONDecodeError:
            return {
                "redirects": {},
                "temp_redirects": {},
                "users": {},
                "stats": {}
            }

    def _reload_data(self):
        with self.file_lock:
            self.data = self._load_data()

    def _save_data(self):
        with self.file_lock:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    def generate_random_link(self, length: int) -> str:
        self._reload_data()

        while True:
            link = ''.join(random.choice(Config.RANDOM_CHARS) for _ in range(length))
            if link not in self.data["temp_redirects"] and link not in self.data["redirects"]:
                return link

    async def get_redirect(self, subdomain: str) -> Optional[Dict]:
        self._reload_data()
        return self.data["redirects"].get(subdomain)

    async def add_redirect(self, subdomain: str, url: str, owner_id: int):
        self._reload_data()
        self.data["redirects"][subdomain] = {
            "url": url,
            "owner_id": owner_id,
            "created_at": datetime.now().isoformat(),
            "stats": {
                "clicks": 0,
                "last_click": None,
                "referrers": {},
                "user_agents": {},
                "countries": {}
            }
        }
        self._save_data()

    async def add_temp_redirect(self, url: str, owner_id: int, expires_in_days: int, length: int = None) -> str:
        self._reload_data()

        link_length = length or random.randint(5, 10)
        link = self.generate_random_link(link_length)
        expires = datetime.now() + timedelta(days=expires_in_days)

        self.data["temp_redirects"][link] = {
            "url": url,
            "owner_id": owner_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires.isoformat(),
            "stats": {
                "clicks": 0,
                "last_click": None,
                "referrers": {},
                "user_agents": {},
                "countries": {}
            }
        }
        self._save_data()
        return link

    async def get_user_redirects(self, user_id: int) -> Dict[str, Dict]:
        self._reload_data()

        result = {}
        for subdomain, data in self.data["redirects"].items():
            if data.get("owner_id") == user_id:
                result[subdomain] = data

        for link, data in self.data["temp_redirects"].items():
            if data.get("owner_id") == user_id:
                result[link] = data

        return result

    async def get_temp_redirect(self, subdomain: str) -> Optional[Dict]:
        self._reload_data()
        return self.data["temp_redirects"].get(subdomain)

    async def delete_redirect(self, subdomain: str, owner_id: int) -> bool:
        self._reload_data()

        if subdomain in self.data["redirects"]:
            if self.data["redirects"][subdomain].get("owner_id") == owner_id:
                del self.data["redirects"][subdomain]
                self._save_data()
                return True
            else:
                return False

        if subdomain in self.data["temp_redirects"]:
            if self.data["temp_redirects"][subdomain].get("owner_id") == owner_id:
                del self.data["temp_redirects"][subdomain]
                self._save_data()
                return True
            else:
                return False

        return False

    async def update_stats(self, redirect_id: str, request_info: Dict):
        self._reload_data()

        redirect = (self.data["redirects"].get(redirect_id)
                    or self.data["temp_redirects"].get(redirect_id))

        if not redirect:
            return

        if "stats" not in redirect:
            redirect["stats"] = {
                "clicks": 0,
                "last_click": None,
                "referrers": {},
                "user_agents": {},
                "countries": {}
            }

        stats = redirect["stats"]
        stats["clicks"] += 1
        stats["last_click"] = datetime.now().isoformat()

        referrer = request_info.get("referrer", "direct")
        stats["referrers"][referrer] = stats["referrers"].get(referrer, 0) + 1

        user_agent = request_info.get("user_agent", "unknown")
        stats["user_agents"][user_agent] = stats["user_agents"].get(user_agent, 0) + 1

        country = request_info.get("country", "unknown")
        stats["countries"][country] = stats["countries"].get(country, 0) + 1

        self._save_data()

    async def cleanup_expired(self) -> int:
        self._reload_data()

        now = datetime.now()
        expired_keys = []
        for link, data in self.data["temp_redirects"].items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at < now:
                expired_keys.append(link)

        for link in expired_keys:
            del self.data["temp_redirects"][link]

        if expired_keys:
            self._save_data()

        return len(expired_keys)
