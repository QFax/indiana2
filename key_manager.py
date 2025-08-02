import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import config

class APIKeyManager:
    def __init__(self, api_keys):
        self.keys = deque(api_keys)
        self.key_usage = {
            key: {
                "requests_last_minute": deque(),
                "requests_today": 0,
                "is_exhausted_minute": False,
                "is_exhausted_day": False,
                "exhausted_until": None,
            }
            for key in api_keys
        }
        self.lock = asyncio.Lock()
        self.pacific_time = ZoneInfo("America/Los_Angeles")

    async def get_next_key(self):
        async with self.lock:
            for _ in range(len(self.keys)):
                key = self.keys[0]
                self.keys.rotate(-1)
                if not self._is_key_exhausted(key):
                    self._record_request(key)
                    return key
            return None

    def _is_key_exhausted(self, key):
        usage = self.key_usage[key]
        now = time.time()

        if usage["exhausted_until"] and now < usage["exhausted_until"]:
            return True
        
        usage["is_exhausted_minute"] = False
        usage["is_exhausted_day"] = False
        usage["exhausted_until"] = None

        self._prune_old_requests(key)

        if len(usage["requests_last_minute"]) >= 60:
            usage["is_exhausted_minute"] = True
            usage["exhausted_until"] = now + 60
            return True

        today = datetime.now(self.pacific_time).date()
        if usage["requests_today"] >= 1000 and datetime.fromtimestamp(usage["requests_last_minute"][-1]).astimezone(self.pacific_time).date() == today:
            usage["is_exhausted_day"] = True
            tomorrow = today + timedelta(days=1)
            usage["exhausted_until"] = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=self.pacific_time).timestamp()
            return True

        return False

    def _record_request(self, key):
        now = time.time()
        usage = self.key_usage[key]
        usage["requests_last_minute"].append(now)
        usage["requests_today"] += 1

    def _prune_old_requests(self, key):
        now = time.time()
        usage = self.key_usage[key]
        while usage["requests_last_minute"] and usage["requests_last_minute"] < now - 60:
            usage["requests_last_minute"].popleft()

    async def handle_resource_exhausted(self, key, quota_id):
        async with self.lock:
            now = time.time()
            usage = self.key_usage[key]
            if "PerDay" in quota_id:
                usage["is_exhausted_day"] = True
                today = datetime.now(self.pacific_time).date()
                tomorrow = today + timedelta(days=1)
                usage["exhausted_until"] = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=self.pacific_time).timestamp()
            else:
                usage["is_exhausted_minute"] = True
                usage["exhausted_until"] = now + 60
    
    def get_status(self):
        total_requests_last_minute = 0
        total_requests_today = 0
        now = time.time()
        today = datetime.now(self.pacific_time).date()

        for key in self.key_usage:
            self._prune_old_requests(key)
            total_requests_last_minute += len(self.key_usage[key]["requests_last_minute"])
            
            last_request_day = None
            if self.key_usage[key]["requests_last_minute"]:
                last_request_day = datetime.fromtimestamp(self.key_usage[key]["requests_last_minute"][-1]).astimezone(self.pacific_time).date()

            if last_request_day == today:
                total_requests_today += self.key_usage[key]["requests_today"]
            else:
                self.key_usage[key]["requests_today"] = 0


        return {
            "total_requests_last_60_seconds": total_requests_last_minute,
            "total_requests_today_pacific_time": total_requests_today,
        }

key_manager = APIKeyManager(config.GEMINI_API_KEYS)