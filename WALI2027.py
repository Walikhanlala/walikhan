# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import re
import threading
import copy
import os
import sys
import random
import uuid
import base64
import shutil
import json
import hashlib
import platform
import logging
import time
import requests
from time import sleep

# -------------------------
# Configuration / Globals
# -------------------------

# App data directory (per-user, cross-platform)
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".dmg_brand_tool")
if not os.path.exists(APP_DATA_DIR):
    try:
        os.makedirs(APP_DATA_DIR, exist_ok=True)
    except Exception:
        APP_DATA_DIR = os.getcwd()

ERROR_LOG_PATH = os.path.join(APP_DATA_DIR, "error.txt")

# Logging: only error-level logs go to error.txt
logger = logging.getLogger("dmg_brand_tool")
logger.setLevel(logging.ERROR)
if not logger.handlers:
    fh = logging.FileHandler(ERROR_LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
logger.propagate = False

# Lock for protecting global counters
COUNTER_LOCK = threading.Lock()

# pfbid cache — ek baar fetch, baaki accounts reuse karein
_PFBID_CACHE = {}   # post_link -> encoded_feedback_id
_PFBID_LOCK  = threading.Lock()

# Global counters
count = 0
cp = 0
ok = 0
reaction_count = 0
comment_count = 0
follow_count = 0
page_like_count = 0
join_count = 0
page_create_count = 0
page_activate_count = 0
poll_vote_count = 0
poll_comment_count = 0

# Colors
colors = ["\033[38;5;213m", "\033[38;5;81m", "\033[38;5;118m", "\033[38;5;220m", "\033[38;5;171m"]
reset = "\033[0m"
NEON_CYAN = "\033[38;5;87m"
NEON_PINK = "\033[38;5;213m"
NEON_PURPLE = "\033[38;5;141m"
NEON_ORANGE = "\033[38;5;214m"
NEON_GREEN = "\033[38;5;118m"
NEON_BLUE = "\033[38;5;81m"
NEON_RED = "\033[38;5;196m"
NEON_YELLOW = "\033[38;5;226m"
ELECTRIC_BLUE = "\033[38;5;45m"
HOT_PINK = "\033[38;5;198m"
LIME_GREEN = "\033[38;5;154m"
GOLD = "\033[38;5;220m"
SILVER = "\033[38;5;189m"
MAGENTA = "\033[38;5;207m"
BOLD = "\033[1m"

neon_cyan = NEON_CYAN
neon_pink = NEON_PINK
neon_purple = NEON_PURPLE
neon_orange = NEON_ORANGE
neon_green = NEON_GREEN
neon_red = NEON_RED
neon_yellow = NEON_YELLOW
electric_blue = ELECTRIC_BLUE
hot_pink = HOT_PINK
lime_green = LIME_GREEN
gold = GOLD
silver = SILVER

HEART_SYMBOL = f"{HOT_PINK}=>{reset}"

# Global EMOJIS list - har call pe rebuild nahi hogi
EMOJIS = [
    "😍","🔥","💯","❤️","😘","🥰","💪","👌","🌹","😎","💥","🎉","👏","🙌","⚡","🌟","😻","🤩",
    "💝","💖","<3","💓","💞","~*~","🎊","🏆","👑","🦋","😇","🥳","🤍","💎","🌺","🍀","🎯","🚀","💐","🌈",
    "😂","🤣","😅","😆","😄","😃","😀","🙃","😉","😋","😛","😜","🤪","😝","🤑","🤗","🤭","🤫","🤔","🤐",
    "😐","😑","😶","😏","😒","🙄","😬","🤥","😌","😔","😪","🤤","😴","😷","🤒","🤕","🤢","🤧","🥵","🥶",
    "😲","🤯","🥱","😵","🤠","🥸","🤓","🧐","😕","😟","🙁","☹️","😮","😯","😳","🥺","😦","😧","😨",
    "😰","😥","😢","😭","😱","😖","😣","😞","😓","😩","😫","😤","😡","😠","🤬","💀","☠️","💩","🤡",
    "👹","👺","👻","👽","👾","🤖","😺","😸","😹","😼","😽","🙀","😿","😾","🙈","🙉","🙊","💋","💌","💘",
    "~*~","❣️","💕","💟","❤️‍🔥","❤️‍🩹","🧡","💛","💚","💙","💜","🖤","🤎","🤍","💯","💢","💬","💭","💤","💦",
    "💨","🕳️","💣","🗯️","💥","🌟","⭐","🌙","☀️","🌤️","⛅","🌈","🌊","🌀","🌪️","🌼","🌻","🌺","🌹","🥀",
    "🌷","🌱","🌿","🍃","🍂","🍁","🍀","🎋","🎍","🪴","🌵","🌴","🌲","🌳","🪵","🪨",
    "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🐔","🐧",
    "🐦","🦆","🦅","🦉","🦇","🐺","🐗","🐴","🦄","🐝","🪱","🐛","🦋","🐌","🐞","🐜","🦟","🦗","🦂","🐢",
    "🐍","🦎","🦖","🦕","🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳","🐋","🦈","🦭","🐊","🦢","🦩",
    "🕊️","🐓","🦚","🦜","🦝","🦙","🦘","🦬","🐃","🐂",
    "🍎","🍊","🍋","🍇","🍓","🫐","🍈","🍒","🍑","🥭","🍍","🥥","🥝","🍅","🫒","🥑","🍆","🌽","🌶️","🫑",
    "🍕","🍔","🌮","🌯","🥙","🧆","🍜","🍝","🍛","🍣","🍱","🥟","🦪","🍤","🍙","🍚","🍘","🍥","🥮","🍡",
    "🧁","🍰","🎂","🍮","🍭","🍬","🍫","🍿","🍩","🍪","🌰","🥜","🍯","🧃","🥤","🧋","☕","🍵","🧉","🍺",
    "⚽","🏀","🏈","⚾","🥎","🎾","🏐","🏉","🎱","🏓","🏸","🥊","🥋","🎯","🥅","⛳","🎣","🤿","🎽","🎿",
    "🛷","🥌","🎮","🕹️","🎲","🧩","🪆","🎭","🎨","🖼️","🎪","🎠","🎡","🎢","🎬","🎤","🎧","🎼","🎹",
    "🥁","🎷","🎺","🎸","🎻","🪕","🎙️","📻","📺","📷",
]

# ── 25 Mixed User Agents ──
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Samsung Galaxy S23) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; OnePlus 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy A54) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Xiaomi 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Realme GT 2 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Oppo Reno 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Vivo V25 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.8 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Android 14; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
]

# -------------------------
# Helpers
# -------------------------

def fix_windows_encoding():
    if os.name == "nt":
        try:
            os.system("chcp 65001 > nul")
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception as e:
            logger.exception("Failed to set Windows encoding: %s", e)
        # Windows 10+ mein ANSI colors enable karo
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
        # Fallback: colorama (agar installed ho)
        try:
            import colorama
            colorama.init(autoreset=False)
        except Exception:
            pass
    else:
        try:
            import locale
            locale.setlocale(locale.LC_ALL, '')
        except Exception:
            pass

fix_windows_encoding()

def parse_cookie_string(cookie_str):
    cookies = {}
    try:
        if not cookie_str:
            return cookies
        # "cookie: " ya "Cookie: " prefix hata do
        cookie_str = cookie_str.strip()
        if cookie_str.lower().startswith("cookie:"):
            cookie_str = cookie_str[7:].strip()
        parts = cookie_str.split(";")
        for p in parts:
            p = p.strip()
            if not p or "=" not in p:
                continue
            k, v = p.split("=", 1)
            k = k.strip()
            v = v.strip()
            # Key mein space ya "cookie:" na ho
            if " " in k or ":" in k:
                continue
            cookies[k] = v
    except Exception as e:
        logger.exception("parse_cookie_string error: %s", e)
    return cookies

def safe_search_group1(pattern, text):
    try:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    except Exception as e:
        logger.exception("safe_search_group1 pattern=%s error=%s", pattern, e)
    return ""

# -------------------------
# Async connector helper
# -------------------------

def _make_connector():
    """Create aiohttp TCPConnector with sensible defaults."""
    return aiohttp.TCPConnector(limit=100, limit_per_host=30, ttl_dns_cache=300)

def _make_timeout():
    return aiohttp.ClientTimeout(connect=24, sock_read=24, total=60)

# -------------------------
# Real Feedback ID Fetcher (pfbid fix)
# -------------------------

async def get_real_feedback_id(post_url, cookie="", user_agent=None, numeric_post_id=None):
    """
    Facebook ab numeric post_id se feedback_id accept nahi karta (group posts etc).
    Yeh function post ki actual page se real 'feedback:pfbid...' wala ID fetch karta hai.
    Returns: base64-encoded feedback_id string (ready to use in GraphQL variables)

    numeric_post_id: agar diya gaya ho (jaise URL se nikala gaya /permalink/<id>/),
    to proximity-matching use hogi — jo feedback_id us numeric ID ke SABSE QAREEB
    (same JSON block) milay, wahi post ka apna feedback_id hota hai. Comments ke
    feedback_ids page mein door hote hain, isliye woh match nahi karenge.
    """
    if not post_url or not post_url.startswith("http"):
        print(f"\033[38;5;196m[DEBUG][PFBID] FAIL: post_url invalid => '{post_url}'{reset}")
        return None
    # Cache check — same post ke liye dobara fetch mat karo
    cache_key = f"{post_url}|{numeric_post_id or ''}"
    with _PFBID_LOCK:
        if cache_key in _PFBID_CACHE:
            print(f"\033[38;5;87m[DEBUG][PFBID] Cache HIT => {_PFBID_CACHE[cache_key][:40]}...{reset}")
            return _PFBID_CACHE[cache_key]
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "cookie": cookie,
        "referer": "https://www.facebook.com/",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
    }
    try:
        print(f"\033[38;5;87m[DEBUG][PFBID] Fetching URL: {post_url}{reset}")
        connector = _make_connector()
        async with aiohttp.ClientSession(connector=connector, timeout=_make_timeout()) as session:
            async with session.get(post_url, headers=headers, allow_redirects=True) as resp:
                http_status = resp.status
                text = await resp.text()
        print(f"\033[38;5;87m[DEBUG][PFBID] HTTP Status={http_status} | Page size={len(text)} chars{reset}")

        result = None

        all_p1 = [(m.start(), m.group(1)) for m in re.finditer(r'"feedback_id"\s*:\s*"(feedback:pfbid[^"]+)"', text)]
        print(f"\033[38;5;87m[DEBUG][PFBID] Pattern1 matches={len(all_p1)}{reset}")

        if numeric_post_id and all_p1:
            pid_positions = [m.start() for m in re.finditer(re.escape(str(numeric_post_id)), text)]
            print(f"\033[38;5;87m[DEBUG][PFBID] numeric_post_id='{numeric_post_id}' found at {len(pid_positions)} position(s) in page{reset}")
            if pid_positions:
                best_fid = None
                best_dist = None
                for pos, fid in all_p1:
                    nearest = min(abs(pos - pp) for pp in pid_positions)
                    if best_dist is None or nearest < best_dist:
                        best_dist = nearest
                        best_fid = fid
                if best_fid:
                    result = base64.b64encode(best_fid.encode()).decode("utf-8")
                    print(f"\033[38;5;87m[DEBUG][PFBID] Proximity match => {best_fid} (dist={best_dist}){reset}")

        if not result and all_p1:
            raw_fid = all_p1[0][1]
            result = base64.b64encode(raw_fid.encode()).decode("utf-8")
            print(f"\033[38;5;87m[DEBUG][PFBID] Fallback P1 first-match => {raw_fid}{reset}")

        if not result:
            all_p2 = [(m.start(), m.group(1)) for m in re.finditer(r'feedback_id\\?":\s*\\?"(feedback:pfbid[^"\\]+)', text)]
            print(f"\033[38;5;87m[DEBUG][PFBID] Pattern2 matches={len(all_p2)}{reset}")
            if numeric_post_id and all_p2:
                pid_positions = [m.start() for m in re.finditer(re.escape(str(numeric_post_id)), text)]
                if pid_positions:
                    best_fid = None; best_dist = None
                    for pos, fid in all_p2:
                        nearest = min(abs(pos - pp) for pp in pid_positions)
                        if best_dist is None or nearest < best_dist:
                            best_dist = nearest; best_fid = fid
                    if best_fid:
                        result = base64.b64encode(best_fid.encode()).decode("utf-8")
                        print(f"\033[38;5;87m[DEBUG][PFBID] P2 proximity => {best_fid}{reset}")
            if not result and all_p2:
                raw_fid = all_p2[0][1]
                result = base64.b64encode(raw_fid.encode()).decode("utf-8")
                print(f"\033[38;5;87m[DEBUG][PFBID] Fallback P2 first-match => {raw_fid}{reset}")

        if not result:
            all_p3 = [(m.start(), m.group(1)) for m in re.finditer(r'"feedback_id"\s*:\s*"(Zm[A-Za-z0-9+/=]{20,})"', text)]
            print(f"\033[38;5;87m[DEBUG][PFBID] Pattern3 matches={len(all_p3)}{reset}")
            decoded_candidates = []
            for pos, candidate in all_p3:
                try:
                    decoded = base64.b64decode(candidate).decode("utf-8")
                    if decoded.startswith("feedback:pfbid"):
                        decoded_candidates.append((pos, candidate, decoded))
                except Exception:
                    pass
            if numeric_post_id and decoded_candidates:
                pid_positions = [m.start() for m in re.finditer(re.escape(str(numeric_post_id)), text)]
                if pid_positions:
                    best = None; best_dist = None
                    for pos, candidate, decoded in decoded_candidates:
                        nearest = min(abs(pos - pp) for pp in pid_positions)
                        if best_dist is None or nearest < best_dist:
                            best_dist = nearest; best = (candidate, decoded)
                    if best:
                        result = best[0]
                        print(f"\033[38;5;87m[DEBUG][PFBID] P3 proximity => {best[1]}{reset}")
            if not result and decoded_candidates:
                best = decoded_candidates[0]
                result = best[1]
                print(f"\033[38;5;87m[DEBUG][PFBID] Fallback P3 first-match => {best[2]}{reset}")

        if result:
            with _PFBID_LOCK:
                _PFBID_CACHE[cache_key] = result
            print(f"\033[38;5;87m[DEBUG][PFBID] FINAL result => {result[:60]}...{reset}")
            return result

        print(f"\033[38;5;196m[DEBUG][PFBID] FAIL: Koi bhi pattern match nahi hua! URL={post_url}{reset}")
        return None
    except Exception as e:
        print(f"\033[38;5;196m[DEBUG][PFBID] EXCEPTION: {type(e).__name__}: {e}{reset}")
        import traceback; traceback.print_exc()
        return None


# -------------------------
# Post ID Extractor
# -------------------------

async def extract_post_id(user_input):
    user_input = user_input.strip()

    if re.match(r'^\d+$', user_input):
        return user_input

    m = re.search(r'/posts/(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'/permalink/(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'story_fbid=(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'fbid=(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'/(?:videos|photos)/(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'profile\.php\?id=(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'[?&]v=(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'[/=](\d{10,})(?:[/?&]|$)', user_input)
    if m: return m.group(1)

    if '/share/' in user_input:
        try:
            print("\033[96mResolving link please wait...\033[0m")
            hdrs = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            connector = _make_connector()
            async with aiohttp.ClientSession(connector=connector, timeout=_make_timeout()) as session:
                async with session.get(user_input, headers=hdrs, allow_redirects=True) as resp:
                    final_url = str(resp.url)
                    text = await resp.text()

            for pat, src in [
                (r'/posts/(\d+)', final_url),
                (r'story_fbid=(\d+)', final_url),
                (r'/(?:videos|photos)/(\d+)', final_url),
                (r'profile\.php\?id=(\d+)', final_url),
                (r'facebook\.com/(\d{8,})', final_url),
                (r'"story_id"\s*:\s*"(\d+)"', text),
                (r'"post_id"\s*:\s*"(\d+)"', text),
                (r'"userID"\s*:\s*"(\d+)"', text),
                (r'"actorID"\s*:\s*"(\d+)"', text),
            ]:
                m = re.search(pat, src)
                if m:
                    return m.group(1)

            print("\033[91m[!] ID extract nahi hui. Manually daalo.\033[0m")
            return input("\033[96m-> Post ID manually: \033[0m").strip()

        except Exception as e:
            print(f"\033[91m[!] Error: {e}\033[0m")
            return input("\033[96m-> Post ID manually: \033[0m").strip()

    m = re.search(r'/(\d{10,})', user_input)
    if m: return m.group(1)

    return user_input


async def extract_profile_id(user_input, cookie=None):
    user_input = user_input.strip()

    if re.match(r'^\d+$', user_input):
        return user_input

    m = re.search(r'profile\.php\?id=(\d+)', user_input)
    if m: return m.group(1)

    m = re.search(r'facebook\.com/(\d{8,})(?:[/?]|$)', user_input)
    if m: return m.group(1)

    try:
        print("\033[38;5;51m[*] Profile link resolve ho raha hai...\033[0m")
        hdrs = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if cookie:
            hdrs["Cookie"] = cookie

        if not user_input.startswith("http"):
            user_input = "https://www.facebook.com/" + user_input.lstrip("/")

        connector = _make_connector()
        async with aiohttp.ClientSession(connector=connector, timeout=_make_timeout()) as session:
            async with session.get(user_input, headers=hdrs, allow_redirects=True) as resp:
                final_url = str(resp.url)
                text = await resp.text()

        m = re.search(r'profile\.php\?id=(\d+)', final_url)
        if m: return m.group(1)

        m = re.search(r'facebook\.com/(\d{8,})(?:[/?]|$)', final_url)
        if m: return m.group(1)

        for pat in [
            r'"userID":"(\d+)"', r'"actorID":"(\d+)"', r'"USER_ID":"(\d+)"',
            r'"ownerID":"(\d+)"', r'"pageID":"(\d+)"', r'"entity_id":"(\d+)"',
            r'entity_id=(\d+)', r'"id":"(\d{8,})"',
        ]:
            m = re.search(pat, text)
            if m: return m.group(1)

        m = re.search(r'c_user=(\d+)', text)
        if m: return m.group(1)

    except Exception:
        pass

    return None


# -------------------------
# Poll Data Fetcher (SIDD method - sync sequential)
# -------------------------

def _get_fb_dtsg(cookie):
    """
    dtsg fetch karo — 2 methods:
        pass
    METHOD 1: business.facebook.com/plugins/page.php?source=mobile  (List #1 - fastest 0.759s)
    METHOD 2: mbasic.facebook.com full method  (name=fb_dtsg value= se)
    Har step pe debug print hai
    """

    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.133 Safari/537.36"

    DTSG_PATTERNS = [
        r'"DTSGInitialData",\[\],{"token":"(.*?)"}',
        r'name="fb_dtsg" value="(.*?)"',
        r'"fb_dtsg"\s*:\s*"([^"]+)"',
        r'\["DTSGInitData",\[\],{"token":"(.*?)"}',
        r'"dtsg":\s*{\s*"token":\s*"(.*?)"',
    ]

    def try_extract(html):
        for pat in DTSG_PATTERNS:
            m = re.search(pat, html)
            if m:
                return m.group(1)
        return None

    # ─────────────────────────────────────────────
    # METHOD 1: business.facebook.com/plugins/page.php  (Rank #7 - SAFEST)
    # No extra params — cleanest request — hardest to detect/block
    # ─────────────────────────────────────────────
    try:
        headers_m1 = {
            "cookie": cookie,
            "user-agent": UA,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
        }
        resp_m1 = requests.get(
            "https://business.facebook.com/plugins/page.php",
            headers=headers_m1,
            timeout=10,
            allow_redirects=True
        )
        token_m1 = try_extract(resp_m1.text)
        if token_m1:
            return token_m1
    except Exception as e:
        pass

    # ─────────────────────────────────────────────
    # METHOD 2: business.facebook.com/plugins/page.php?source=mobile  (Rank #1 - FASTEST)
    # Speed backup — 0.759s
    # ─────────────────────────────────────────────
    try:
        headers_m2 = {
            "cookie": cookie,
            "user-agent": UA,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
        }
        resp_m2 = requests.get(
            "https://business.facebook.com/plugins/page.php?source=mobile",
            headers=headers_m2,
            timeout=10,
            allow_redirects=True
        )
        token_m2 = try_extract(resp_m2.text)
        if token_m2:
            return token_m2
    except Exception as e:
        pass

    return None


def fetch_poll_options(poll_link, cookies):
    """Share link resolve karo, phir poll options fetch karo"""
    poll_headers = {
        "authority": "www.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,vi;q=0.9,fr;q=0.8,vi-VN;q=0.7,fr-FR;q=0.6,en-US;q=0.5",
        "cache-control": "max-age=0",
        "dpr": "1",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": '"Google Chrome";v="114", "Chromium";v="114", "Not?A_Brand";v="8"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="114.0.5735.133", "Chromium";v="114.0.5735.133", "Not?A_Brand";v="8.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"10.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.133 Safari/537.36",
        "viewport-width": "559",
    }

    def _extract_question_id(html):
        patterns = [
            r'Question","id":"(\d+)"',
            r'"question_id"\s*:\s*"(\d+)"',
            r'"questionID"\s*:\s*"(\d+)"',
            r'"id":"(\d+)","__typename":"Question"',
            r'question\\u005Fid":"(\d+)"',
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if m:
                return m.group(1)
        return None

    for cookie in cookies:
        try:
            print("\033[96mFetching poll options...\033[0m")
            fb_dtsg = _get_fb_dtsg(cookie)
            if not fb_dtsg:
                continue

            headers = {**poll_headers, "cookie": cookie}

            # STEP-1 hataya — /share/ link 400 deta hai, resolve nahi hota, time waste
            real_link = poll_link

            # Step 2: stream se question_id nikalo — milte hi stop, 907KB puri mat utaro
            question_id = None
            try:
                resp_s = requests.get(real_link, headers=headers, timeout=15, stream=True)
                buffer = ""
                downloaded_kb = 0
                for chunk in resp_s.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded_kb += len(chunk) / 1024
                        buffer += chunk.decode("utf-8", errors="ignore")
                        question_id = _extract_question_id(buffer)
                        if question_id:
                            resp_s.close()
                            break
                else:
                    resp_s.close()
                if not question_id:
                    pass
            except Exception as e:
                pass

            if not question_id:
                continue

            # Step 3: GraphQL se options fetch karo
            data = {
                "fb_dtsg": fb_dtsg,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometUFIVoteCountDialogQuery",
                "variables": f'{{"questionID":"{question_id}","scale":1}}',
                "server_timestamps": "true",
                "doc_id": "6080954902008459",
            }
            api_resp = requests.post(
                "https://www.facebook.com/api/graphql/",
                headers=headers,
                data=data,
                timeout=15
            )
            try:
                api_json = api_resp.json()
                raw_options = api_json["data"]["question"]["options"]["nodes"]
                options = [(opt["id"], opt["text"], opt["voters"]["count"]) for opt in raw_options]
                return question_id, options
            except Exception as e:
                continue

        except Exception as e:
            continue
    return "", []


# -------------------------
# Core Functions
# -------------------------

def banner():
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass
    try:
        width = shutil.get_terminal_size().columns
        if width < 60:
            width = 60
    except Exception:
        width = 100

    _THEMES = [
        {"BC":"\033[38;5;57m","FILL":"\033[38;5;99m","SHADE":"\033[38;5;63m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;213m","\033[38;5;207m","\033[38;5;201m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;57m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;20m","FILL":"\033[38;5;45m","SHADE":"\033[38;5;19m","ROWS":["\033[38;5;159m","\033[38;5;123m","\033[38;5;87m","\033[38;5;81m","\033[38;5;75m","\033[38;5;69m"],"TOP1":"\033[38;5;159m","TOP2":"\033[38;5;20m","OWN2":"\033[38;5;123m","OWN3":"\033[38;5;159m","ALI":"\033[38;5;87m"},
        {"BC":"\033[38;5;28m","FILL":"\033[38;5;118m","SHADE":"\033[38;5;22m","ROWS":["\033[38;5;231m","\033[38;5;194m","\033[38;5;157m","\033[38;5;120m","\033[38;5;83m","\033[38;5;47m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;28m","OWN2":"\033[38;5;194m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;157m"},
        {"BC":"\033[38;5;89m","FILL":"\033[38;5;161m","SHADE":"\033[38;5;53m","ROWS":["\033[38;5;225m","\033[38;5;212m","\033[38;5;206m","\033[38;5;200m","\033[38;5;164m","\033[38;5;128m"],"TOP1":"\033[38;5;225m","TOP2":"\033[38;5;89m","OWN2":"\033[38;5;212m","OWN3":"\033[38;5;225m","ALI":"\033[38;5;206m"},
        {"BC":"\033[38;5;130m","FILL":"\033[38;5;220m","SHADE":"\033[38;5;94m","ROWS":["\033[38;5;231m","\033[38;5;230m","\033[38;5;229m","\033[38;5;228m","\033[38;5;222m","\033[38;5;216m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;130m","OWN2":"\033[38;5;229m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;228m"},
        {"BC":"\033[38;5;54m","FILL":"\033[38;5;135m","SHADE":"\033[38;5;53m","ROWS":["\033[38;5;219m","\033[38;5;183m","\033[38;5;177m","\033[38;5;171m","\033[38;5;141m","\033[38;5;105m"],"TOP1":"\033[38;5;219m","TOP2":"\033[38;5;54m","OWN2":"\033[38;5;183m","OWN3":"\033[38;5;219m","ALI":"\033[38;5;177m"},
        {"BC":"\033[38;5;26m","FILL":"\033[38;5;81m","SHADE":"\033[38;5;20m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;159m","\033[38;5;123m","\033[38;5;117m","\033[38;5;111m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;26m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;159m"},
        {"BC":"\033[38;5;124m","FILL":"\033[38;5;196m","SHADE":"\033[38;5;88m","ROWS":["\033[38;5;229m","\033[38;5;223m","\033[38;5;217m","\033[38;5;211m","\033[38;5;205m","\033[38;5;199m"],"TOP1":"\033[38;5;229m","TOP2":"\033[38;5;124m","OWN2":"\033[38;5;223m","OWN3":"\033[38;5;229m","ALI":"\033[38;5;217m"},
        {"BC":"\033[38;5;23m","FILL":"\033[38;5;86m","SHADE":"\033[38;5;17m","ROWS":["\033[38;5;159m","\033[38;5;122m","\033[38;5;86m","\033[38;5;50m","\033[38;5;44m","\033[38;5;38m"],"TOP1":"\033[38;5;159m","TOP2":"\033[38;5;23m","OWN2":"\033[38;5;122m","OWN3":"\033[38;5;159m","ALI":"\033[38;5;86m"},
        {"BC":"\033[38;5;91m","FILL":"\033[38;5;141m","SHADE":"\033[38;5;55m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;189m","\033[38;5;183m","\033[38;5;147m","\033[38;5;111m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;91m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;189m"},
        {"BC":"\033[38;5;58m","FILL":"\033[38;5;154m","SHADE":"\033[38;5;64m","ROWS":["\033[38;5;228m","\033[38;5;192m","\033[38;5;156m","\033[38;5;120m","\033[38;5;84m","\033[38;5;48m"],"TOP1":"\033[38;5;228m","TOP2":"\033[38;5;58m","OWN2":"\033[38;5;192m","OWN3":"\033[38;5;228m","ALI":"\033[38;5;156m"},
        {"BC":"\033[38;5;197m","FILL":"\033[38;5;213m","SHADE":"\033[38;5;161m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;213m","\033[38;5;207m","\033[38;5;201m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;197m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;31m","FILL":"\033[38;5;117m","SHADE":"\033[38;5;25m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;159m","\033[38;5;153m","\033[38;5;117m","\033[38;5;81m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;31m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;159m"},
        {"BC":"\033[38;5;202m","FILL":"\033[38;5;214m","SHADE":"\033[38;5;166m","ROWS":["\033[38;5;231m","\033[38;5;230m","\033[38;5;228m","\033[38;5;222m","\033[38;5;214m","\033[38;5;208m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;202m","OWN2":"\033[38;5;230m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;228m"},
        {"BC":"\033[38;5;61m","FILL":"\033[38;5;105m","SHADE":"\033[38;5;55m","ROWS":["\033[38;5;225m","\033[38;5;219m","\033[38;5;183m","\033[38;5;147m","\033[38;5;141m","\033[38;5;135m"],"TOP1":"\033[38;5;225m","TOP2":"\033[38;5;61m","OWN2":"\033[38;5;219m","OWN3":"\033[38;5;225m","ALI":"\033[38;5;183m"},
        {"BC":"\033[38;5;34m","FILL":"\033[38;5;82m","SHADE":"\033[38;5;28m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;158m","\033[38;5;121m","\033[38;5;84m","\033[38;5;48m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;34m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;158m"},
        {"BC":"\033[38;5;53m","FILL":"\033[38;5;91m","SHADE":"\033[38;5;17m","ROWS":["\033[38;5;231m","\033[38;5;218m","\033[38;5;212m","\033[38;5;206m","\033[38;5;170m","\033[38;5;134m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;53m","OWN2":"\033[38;5;218m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;212m"},
        {"BC":"\033[38;5;95m","FILL":"\033[38;5;173m","SHADE":"\033[38;5;59m","ROWS":["\033[38;5;231m","\033[38;5;224m","\033[38;5;217m","\033[38;5;180m","\033[38;5;173m","\033[38;5;137m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;95m","OWN2":"\033[38;5;224m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;217m"},
        {"BC":"\033[38;5;19m","FILL":"\033[38;5;75m","SHADE":"\033[38;5;17m","ROWS":["\033[38;5;189m","\033[38;5;153m","\033[38;5;117m","\033[38;5;81m","\033[38;5;75m","\033[38;5;69m"],"TOP1":"\033[38;5;189m","TOP2":"\033[38;5;19m","OWN2":"\033[38;5;153m","OWN3":"\033[38;5;189m","ALI":"\033[38;5;117m"},
        {"BC":"\033[38;5;128m","FILL":"\033[38;5;170m","SHADE":"\033[38;5;92m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;177m","\033[38;5;171m","\033[38;5;135m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;128m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;66m","FILL":"\033[38;5;109m","SHADE":"\033[38;5;60m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;159m","\033[38;5;153m","\033[38;5;116m","\033[38;5;109m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;66m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;153m"},
        {"BC":"\033[38;5;208m","FILL":"\033[38;5;226m","SHADE":"\033[38;5;172m","ROWS":["\033[38;5;231m","\033[38;5;230m","\033[38;5;229m","\033[38;5;228m","\033[38;5;227m","\033[38;5;221m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;208m","OWN2":"\033[38;5;230m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;229m"},
        {"BC":"\033[38;5;36m","FILL":"\033[38;5;85m","SHADE":"\033[38;5;29m","ROWS":["\033[38;5;159m","\033[38;5;122m","\033[38;5;86m","\033[38;5;85m","\033[38;5;79m","\033[38;5;43m"],"TOP1":"\033[38;5;159m","TOP2":"\033[38;5;36m","OWN2":"\033[38;5;122m","OWN3":"\033[38;5;159m","ALI":"\033[38;5;86m"},
        {"BC":"\033[38;5;164m","FILL":"\033[38;5;207m","SHADE":"\033[38;5;128m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;213m","\033[38;5;171m","\033[38;5;135m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;164m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;33m","FILL":"\033[38;5;69m","SHADE":"\033[38;5;27m","ROWS":["\033[38;5;159m","\033[38;5;123m","\033[38;5;117m","\033[38;5;81m","\033[38;5;75m","\033[38;5;69m"],"TOP1":"\033[38;5;159m","TOP2":"\033[38;5;33m","OWN2":"\033[38;5;123m","OWN3":"\033[38;5;159m","ALI":"\033[38;5;117m"},
        {"BC":"\033[38;5;167m","FILL":"\033[38;5;209m","SHADE":"\033[38;5;131m","ROWS":["\033[38;5;231m","\033[38;5;224m","\033[38;5;218m","\033[38;5;211m","\033[38;5;204m","\033[38;5;167m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;167m","OWN2":"\033[38;5;224m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;218m"},
        {"BC":"\033[38;5;25m","FILL":"\033[38;5;69m","SHADE":"\033[38;5;19m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;159m","\033[38;5;123m","\033[38;5;87m","\033[38;5;81m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;25m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;159m"},
        {"BC":"\033[38;5;136m","FILL":"\033[38;5;214m","SHADE":"\033[38;5;100m","ROWS":["\033[38;5;231m","\033[38;5;230m","\033[38;5;224m","\033[38;5;221m","\033[38;5;215m","\033[38;5;179m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;136m","OWN2":"\033[38;5;230m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;224m"},
        {"BC":"\033[38;5;55m","FILL":"\033[38;5;147m","SHADE":"\033[38;5;54m","ROWS":["\033[38;5;225m","\033[38;5;219m","\033[38;5;183m","\033[38;5;177m","\033[38;5;141m","\033[38;5;105m"],"TOP1":"\033[38;5;225m","TOP2":"\033[38;5;55m","OWN2":"\033[38;5;219m","OWN3":"\033[38;5;225m","ALI":"\033[38;5;183m"},
        {"BC":"\033[38;5;160m","FILL":"\033[38;5;204m","SHADE":"\033[38;5;124m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;218m","\033[38;5;211m","\033[38;5;204m","\033[38;5;198m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;160m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;218m"},
        {"BC":"\033[38;5;40m","FILL":"\033[38;5;84m","SHADE":"\033[38;5;34m","ROWS":["\033[38;5;231m","\033[38;5;194m","\033[38;5;157m","\033[38;5;121m","\033[38;5;85m","\033[38;5;49m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;40m","OWN2":"\033[38;5;194m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;157m"},
        {"BC":"\033[38;5;60m","FILL":"\033[38;5;111m","SHADE":"\033[38;5;54m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;189m","\033[38;5;153m","\033[38;5;117m","\033[38;5;111m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;60m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;189m"},
        {"BC":"\033[38;5;131m","FILL":"\033[38;5;181m","SHADE":"\033[38;5;95m","ROWS":["\033[38;5;231m","\033[38;5;224m","\033[38;5;218m","\033[38;5;211m","\033[38;5;181m","\033[38;5;145m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;131m","OWN2":"\033[38;5;224m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;218m"},
        {"BC":"\033[38;5;27m","FILL":"\033[38;5;111m","SHADE":"\033[38;5;21m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;159m","\033[38;5;123m","\033[38;5;117m","\033[38;5;81m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;27m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;159m"},
        {"BC":"\033[38;5;214m","FILL":"\033[38;5;226m","SHADE":"\033[38;5;178m","ROWS":["\033[38;5;231m","\033[38;5;230m","\033[38;5;229m","\033[38;5;227m","\033[38;5;221m","\033[38;5;215m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;214m","OWN2":"\033[38;5;230m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;229m"},
        {"BC":"\033[38;5;63m","FILL":"\033[38;5;105m","SHADE":"\033[38;5;57m","ROWS":["\033[38;5;225m","\033[38;5;219m","\033[38;5;183m","\033[38;5;147m","\033[38;5;141m","\033[38;5;105m"],"TOP1":"\033[38;5;225m","TOP2":"\033[38;5;63m","OWN2":"\033[38;5;219m","OWN3":"\033[38;5;225m","ALI":"\033[38;5;183m"},
        {"BC":"\033[38;5;106m","FILL":"\033[38;5;148m","SHADE":"\033[38;5;70m","ROWS":["\033[38;5;231m","\033[38;5;229m","\033[38;5;192m","\033[38;5;156m","\033[38;5;149m","\033[38;5;143m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;106m","OWN2":"\033[38;5;229m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;192m"},
        {"BC":"\033[38;5;205m","FILL":"\033[38;5;218m","SHADE":"\033[38;5;169m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;212m","\033[38;5;206m","\033[38;5;200m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;205m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;38m","FILL":"\033[38;5;80m","SHADE":"\033[38;5;32m","ROWS":["\033[38;5;159m","\033[38;5;123m","\033[38;5;116m","\033[38;5;80m","\033[38;5;44m","\033[38;5;38m"],"TOP1":"\033[38;5;159m","TOP2":"\033[38;5;38m","OWN2":"\033[38;5;123m","OWN3":"\033[38;5;159m","ALI":"\033[38;5;116m"},
        {"BC":"\033[38;5;56m","FILL":"\033[38;5;98m","SHADE":"\033[38;5;54m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;183m","\033[38;5;147m","\033[38;5;141m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;56m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;24m","FILL":"\033[38;5;74m","SHADE":"\033[38;5;18m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;153m","\033[38;5;117m","\033[38;5;81m","\033[38;5;75m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;24m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;153m"},
        {"BC":"\033[38;5;126m","FILL":"\033[38;5;176m","SHADE":"\033[38;5;90m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;183m","\033[38;5;177m","\033[38;5;141m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;126m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;172m","FILL":"\033[38;5;215m","SHADE":"\033[38;5;136m","ROWS":["\033[38;5;231m","\033[38;5;230m","\033[38;5;229m","\033[38;5;223m","\033[38;5;215m","\033[38;5;179m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;172m","OWN2":"\033[38;5;230m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;229m"},
        {"BC":"\033[38;5;65m","FILL":"\033[38;5;114m","SHADE":"\033[38;5;59m","ROWS":["\033[38;5;231m","\033[38;5;194m","\033[38;5;157m","\033[38;5;150m","\033[38;5;114m","\033[38;5;78m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;65m","OWN2":"\033[38;5;194m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;157m"},
        {"BC":"\033[38;5;199m","FILL":"\033[38;5;212m","SHADE":"\033[38;5;163m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;212m","\033[38;5;205m","\033[38;5;199m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;199m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;32m","FILL":"\033[38;5;74m","SHADE":"\033[38;5;26m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;159m","\033[38;5;116m","\033[38;5;80m","\033[38;5;74m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;32m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;159m"},
        {"BC":"\033[38;5;93m","FILL":"\033[38;5;135m","SHADE":"\033[38;5;57m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;177m","\033[38;5;141m","\033[38;5;135m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;93m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;22m","FILL":"\033[38;5;76m","SHADE":"\033[38;5;16m","ROWS":["\033[38;5;231m","\033[38;5;193m","\033[38;5;156m","\033[38;5;119m","\033[38;5;83m","\033[38;5;77m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;22m","OWN2":"\033[38;5;193m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;156m"},
        {"BC":"\033[38;5;161m","FILL":"\033[38;5;205m","SHADE":"\033[38;5;125m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;218m","\033[38;5;212m","\033[38;5;205m","\033[38;5;169m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;161m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;218m"},
        {"BC":"\033[38;5;37m","FILL":"\033[38;5;79m","SHADE":"\033[38;5;31m","ROWS":["\033[38;5;159m","\033[38;5;122m","\033[38;5;86m","\033[38;5;79m","\033[38;5;43m","\033[38;5;37m"],"TOP1":"\033[38;5;159m","TOP2":"\033[38;5;37m","OWN2":"\033[38;5;122m","OWN3":"\033[38;5;159m","ALI":"\033[38;5;86m"},
        {"BC":"\033[38;5;211m","FILL":"\033[38;5;218m","SHADE":"\033[38;5;175m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;212m","\033[38;5;211m","\033[38;5;175m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;211m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;29m","FILL":"\033[38;5;71m","SHADE":"\033[38;5;23m","ROWS":["\033[38;5;231m","\033[38;5;194m","\033[38;5;158m","\033[38;5;121m","\033[38;5;85m","\033[38;5;71m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;29m","OWN2":"\033[38;5;194m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;158m"},
        {"BC":"\033[38;5;201m","FILL":"\033[38;5;213m","SHADE":"\033[38;5;165m","ROWS":["\033[38;5;231m","\033[38;5;225m","\033[38;5;219m","\033[38;5;213m","\033[38;5;207m","\033[38;5;201m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;201m","OWN2":"\033[38;5;225m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;219m"},
        {"BC":"\033[38;5;67m","FILL":"\033[38;5;116m","SHADE":"\033[38;5;61m","ROWS":["\033[38;5;231m","\033[38;5;195m","\033[38;5;189m","\033[38;5;152m","\033[38;5;116m","\033[38;5;110m"],"TOP1":"\033[38;5;231m","TOP2":"\033[38;5;67m","OWN2":"\033[38;5;195m","OWN3":"\033[38;5;231m","ALI":"\033[38;5;189m"},
    ]
    # Non-repeat: same theme 45 ke baad hi dobara aaye
    _theme_file = os.path.join(APP_DATA_DIR, "btheme.dat")
    try:
        _used_t = list(map(int, open(_theme_file).read().split())) if os.path.exists(_theme_file) else []
    except Exception:
        _used_t = []
    _all_t = list(range(len(_THEMES)))
    _avail_t = [i for i in _all_t if i not in _used_t]
    if not _avail_t:
        _avail_t = _all_t
        _used_t = []
    _ti = random.choice(_avail_t)
    _used_t.append(_ti)
    if len(_used_t) > len(_THEMES) - 45:
        _used_t = _used_t[-(len(_THEMES) - 45):]
    try:
        open(_theme_file, "w").write(" ".join(map(str, _used_t)))
    except Exception:
        pass
    T = _THEMES[_ti]
    BC=T["BC"]; C_FILL=T["FILL"]; C_SHADE=T["SHADE"]; ROW_COLORS=T["ROWS"]
    C_TOP1=T["TOP1"]; C_TOP2=T["TOP2"]; C_OWN2=T["OWN2"]; C_OWN3=T["OWN3"]; C_ALI=T["ALI"]
    C_WHITE="[38;5;255m"

    print(f"\n{BOLD}{BC}╔{chr(9552) * (width-2)}╗{reset}")
    print(f"{BOLD}{BC}║{C_FILL}{'▓' * (width-2)}{BC}║{reset}")

    plain_top = "<<< UPDATED 2027 VERSION >>>"
    top_colored = f"{C_TOP1}<<<{reset} {BOLD}{ROW_COLORS[0]}U{ROW_COLORS[1]}P{ROW_COLORS[2]}D{ROW_COLORS[3]}A{ROW_COLORS[4]}T{ROW_COLORS[5]}E{ROW_COLORS[0]}D{reset} {BOLD}{ROW_COLORS[1]}2{ROW_COLORS[2]}0{ROW_COLORS[3]}2{ROW_COLORS[4]}7{reset} {BOLD}{ROW_COLORS[5]}V{ROW_COLORS[0]}E{ROW_COLORS[1]}R{ROW_COLORS[2]}S{ROW_COLORS[3]}I{ROW_COLORS[4]}O{ROW_COLORS[5]}N{reset} {C_TOP1}>>>{reset}"
    pad_total = width - 2 - len(plain_top)
    pad_l = max(pad_total // 2, 0)
    pad_r = max(pad_total - pad_l, 0)
    print(f"{BOLD}{BC}║{' ' * pad_l}{top_colored}{' ' * pad_r}{BC}║{reset}")
    print(f"{BOLD}{BC}║{C_SHADE}{'░' * (width-2)}{BC}║{reset}")

    ascii_art = [
        "  ██████╗  ███████╗ ███████╗ ",
        "  ██╔══██╗ ██╔════╝ ██╔════╝ ",
        "  ██████╔╝ ███████╗ █████╗   ",
        "  ██╔══██╗ ╚════██║ ██╔══╝   ",
        "  ██║  ██║ ███████║ ██║      ",
        "  ╚═╝  ╚═╝ ╚══════╝ ╚═╝      ",
    ]

    for i, line in enumerate(ascii_art):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        spaces_needed = width - 2 - len(line)
        left_space = max(spaces_needed // 2, 0)
        right_space = max(spaces_needed - left_space, 0)
        print(f"{BOLD}{BC}║{' ' * left_space}{BOLD}{color}{line}{reset}{' ' * right_space}{BOLD}{BC}║{reset}")

    print(f"{BOLD}{BC}║{C_SHADE}{'░' * (width-2)}{BC}║{reset}")
    print(f"{BOLD}{BC}╠{chr(9552) * (width-2)}╣{reset}")

    # Owner info line
    plain_own = "WALI KHAN LALA  |  Owner: WALI KHAN LALA  |  WhatsApp: 03010638091"
    own_colored = (
        f"{BOLD}{C_ALI}WALI KHAN LALA{reset}"
        f"{C_WHITE}  |  Owner: {reset}{C_OWN2}WALI KHAN LALA{reset}{C_WHITE}  |  WhatsApp: {BOLD}{C_OWN3}03010638091{reset}"
    )
    pad_o = width - 2 - len(plain_own)
    pad_ol = max(pad_o // 2, 0)
    pad_or = max(pad_o - pad_ol, 0)
    print(f"{BOLD}{BC}║{' ' * pad_ol}{own_colored}{' ' * pad_or}{BC}║{reset}")

    print(f"{BOLD}{BC}╠{chr(9552) * (width-2)}╣{reset}")
    print(f"{BOLD}{BC}║{C_FILL}{'▓' * (width-2)}{BC}║{reset}")

    # BOTTOM WALI KHAN LALA label
    print(f"{BOLD}{BC}║{' ' * pad_l}{top_colored}{' ' * pad_r}{BC}║{reset}")
    print(f"{BOLD}{BC}║{C_SHADE}{'░' * (width-2)}{BC}║{reset}")
    print(f"{BOLD}{BC}╚{chr(9552) * (width-2)}╝{reset}\n")


def generate_machine_key():
    """Key ek baar banao, file mein save karo — hamesha same rahe."""
    key_file = os.path.join(APP_DATA_DIR, "device.key")
    try:
        # Agar pehle se saved hai to wahi return karo
        if os.path.exists(key_file):
            with open(key_file, "r", encoding="utf-8") as f:
                saved = f.read().strip()
            if saved:
                return saved
    except Exception:
        pass

    # Pehli baar: nai key banao
    try:
        node = uuid.getnode()
        host = platform.node()
        raw = f"{node}-{host}"
        h = hashlib.sha1(raw.encode()).hexdigest().upper()
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        key_chars = []
        for i in range(25):
            idx = (i * 2) % len(h)
            byte = int(h[idx:idx+2], 16)
            key_chars.append(alphabet[byte % len(alphabet)])
        parts = ["".join(key_chars[i:i+4]) for i in range(0, 24, 4)]
        last = "".join(key_chars[24:25])
        parts.append(last)
        new_key = "-".join(parts)
    except Exception as e:
        logger.exception("generate_machine_key fallback: %s", e)
        k = uuid.uuid4().hex.upper()
        k = "".join(ch for ch in k if ch.isalnum())[:25]
        parts = [k[i:i+4] for i in range(0, 25, 4)]
        new_key = "-".join(parts)

    # File mein save karo take agle baar same rahe
    try:
        with open(key_file, "w", encoding="utf-8") as f:
            f.write(new_key)
    except Exception as e:
        logger.exception("generate_machine_key save error: %s", e)

    return new_key


def _hidden_owner_check():
    """Silent background ownership check - user ko pta nahi chalta."""
    try:
        import requests as _r
        resp = _r.get(
            "https://docs.google.com/spreadsheets/d/1In-vxHtdHrsuB2Wl2V2CwOvDLJBdVoG98f1KyZsuPLI/edit?gid=0#gid=0",
            timeout=10
        )
        if "ALISHA ARZOO MADAM" in resp.text:
            return True
        return False
    except Exception:
        # Internet nahi hai to pass kar do - sirf tab fail karo jab clearly na ho
        return True


def check(block=True, retry_delay=10):
    import requests as _req

    # === HIDDEN OWNERSHIP CHECK (user ko bilkul pta nahi chalta) ===
    _owner_ok = _hidden_owner_check()
    if not _owner_ok:
        try:
            print(f"\n{BOLD}{neon_red}  YOUR KEY SYSTEM FAIL{reset}")
            print(f"{BOLD}{neon_red}  YOUR SOFTWARE IS PERMANENTLY DISABLED{reset}\n")
        except Exception:
            print("\n  YOUR KEY SYSTEM FAIL")
            print("  YOUR SOFTWARE IS PERMANENTLY DISABLED\n")
        try:
            for i in range(20, 0, -1):
                print(f"\r{BOLD}\033[38;5;208m  Software {i} seconds mein band ho raha hai...{reset}", end="", flush=True)
                time.sleep(1)
        except Exception:
            time.sleep(20)
        print()
        sys.exit(1)
    # === END HIDDEN CHECK ===

    # Machine ki auto key generate karo aur screen pe dikhao
    machine_key = generate_machine_key()
    print(f"{neon_green}Machine Key : {BOLD}{NEON_YELLOW}{machine_key}{reset}")

    def is_key_approved():
        try:
            k = _req.get(
                "https://docs.google.com/spreadsheets/d/1E7Z_gIrKfwXYKF6xofu0THDMT1Ww4DqziLCG3WdCDAA/edit?gid=0#gid=0",
                timeout=15
            ).text
        except Exception as e:
            logger.exception("check(): remote key fetch failed: %s", e)
            print(f"\n{BOLD}\033[38;5;208m  [!] Internet connection check karo!{reset}\n")
            return False

        if machine_key in k:
            try:
                print(f"                                                    {neon_green}-\x1b[7m{neon_green}Active\x1b[0m-{reset}")
            except Exception:
                pass
            return True
        else:
            try:
                print(f"                                                   {neon_red}-\x1b[7m{neon_red}Not Active\x1b[0m-{reset}")
            except Exception:
                pass
            return False

    try:
        approved = is_key_approved()
    except Exception as e:
        logger.exception("check(): is_key_approved error: %s", e)
        approved = False

    if approved:
        return True

    if not block:
        return False

    try:
        while not approved:
            print(f"\n{BOLD}\033[38;5;51m╔{chr(9552)*55}╗{reset}")
            print(f"{BOLD}\033[38;5;51m║{reset}{BOLD}\033[38;5;226m{'  ~~  WALI KHAN LALA  ~~  ACCESS DENIED  ~~':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
            print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;255m{'  Aapki Key Active Nahi Hai!':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
            print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;118m{'  Key Activate Karwane Ke Liye':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
            print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;118m{'  WhatsApp Karen:':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
            print(f"{BOLD}\033[38;5;51m║{reset}{BOLD}\033[38;5;228m{'  WhatsApp: 03010638091':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
            print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;208m{'  Upar Di Gayi Key Owner Ko Bhej Den':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
            print(f"{BOLD}\033[38;5;51m╚{chr(9552)*55}╝{reset}\n")
            try:
                user_in = input(f"{BOLD}\033[38;5;220m  ==> Dobara Check (Enter) / Band Karo (q): {reset}").strip().lower()
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(1)
            if user_in == "q":
                print(f"\n{BOLD}\033[38;5;51m  ~*~ WALI KHAN LALA - Phir Milenge! ~*~{reset}\n")
                sys.exit(1)
            try:
                approved = is_key_approved()
            except Exception as e:
                logger.exception("check(): retry error: %s", e)
                approved = False
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(1)

    return True
def create_initial_files():
    try:
        for i in range(1, 7):
            cookie_file = f"{i}.txt"
            if not os.path.exists(cookie_file):
                with open(cookie_file, "w", encoding="utf-8") as f:
                    f.write("")
        if not os.path.exists("comments.txt"):
            with open("comments.txt", "w", encoding="utf-8") as f:
                f.write("# Yahan comments likho — ek line ek comment\n# Example:\nMashallah\nBeautiful\nGreat post!\n")
    except Exception as e:
        logger.exception("create_initial_files error: %s", e)


async def check_cookie_live(cookie):
    try:
        uid_match = re.findall(r"c_user=(\d+)", cookie)
        uid = uid_match[0] if uid_match else ""

        connector = _make_connector()
        async with aiohttp.ClientSession(connector=connector, timeout=_make_timeout()) as session:
            async with session.post(
                "https://check.fb.tools/api/check/account",
                json={
                    "inputData": [f"cookie: {cookie}"],
                    "checkFriends": False,
                    "userLang": "en"
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Origin": "https://check.fb.tools",
                    "Referer": "https://check.fb.tools/"
                },
            ) as resp:
                data = await resp.json(content_type=None)

        if not data or "data" not in data or not data["data"]:
            return None, uid, "Error"

        result = data["data"][0]
        status_name = result.get("status", {}).get("name", "")
        account_uid = result.get("uid", uid)
        profile_name = result.get("name", account_uid)

        if status_name == "valid":
            return True, account_uid, profile_name if profile_name else account_uid
        else:
            return False, account_uid, result.get("status", {}).get("message", "Dead")

    except aiohttp.ClientConnectionError:
        return None, uid if 'uid' in dir() else "", "Network Error"
    except asyncio.TimeoutError:
        return None, uid if 'uid' in dir() else "", "Timeout"
    except Exception as e:
        logger.exception("check_cookie_live error: %s", e)
        return None, "", "Error"


async def _deep_check_cookie_via_poll(cookie):
    _POLL_URL = "https://www.facebook.com/share/p/1Ar47rghu3/"
    try:
        # dtsg inline fetch
        _dtsg_h = {"cookie": cookie}
        _conn0 = _make_connector()
        async with aiohttp.ClientSession(connector=_conn0, timeout=_make_timeout()) as _s0:
            async with _s0.get("https://www.facebook.com/", headers=_dtsg_h) as _r0:
                _dtsg_text = await _r0.text()
        fb_dtsg = ""
        _m = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', _dtsg_text)
        if _m:
            fb_dtsg = _m.group(1)
        else:
            try:
                fb_dtsg = _dtsg_text.split('name="fb_dtsg" value="')[1].split('"')[0]
            except Exception:
                pass
        if not fb_dtsg:
            return False

        headers = {
            "authority": "www.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en,vi;q=0.9,fr;q=0.8,vi-VN;q=0.7,fr-FR;q=0.6,en-US;q=0.5",
            "cache-control": "max-age=0",
            "cookie": cookie,
            "dpr": "1",
            "sec-ch-prefers-color-scheme": "light",
            "sec-ch-ua": '"Google Chrome";v="114", "Chromium";v="114", "Not?A_Brand";v="8"',
            "sec-ch-ua-full-version-list": '"Google Chrome";v="114.0.5735.133", "Chromium";v="114.0.5735.133", "Not?A_Brand";v="8.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"10.0.0"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.133 Safari/537.36",
            "viewport-width": "559",
        }
        connector = _make_connector()
        async with aiohttp.ClientSession(connector=connector, timeout=_make_timeout()) as session:
            async with session.get(_POLL_URL, headers=headers) as resp:
                response = await resp.text()
            question_id = response.split('Question","id":"')[1].split('"')[0]
            if not question_id or not question_id.strip():
                return False

            data = {
                "fb_dtsg": fb_dtsg,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometUFIVoteCountDialogQuery",
                "variables": f'{{"questionID":"{question_id}","scale":1}}',
                "server_timestamps": "true",
                "doc_id": "6080954902008459",
            }
            async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp2:
                api_resp = await resp2.json(content_type=None)
            options = api_resp["data"]["question"]["options"]["nodes"]
            if options:
                return True
            return False
    except Exception:
        return False


async def remove_expired_cookies():
    banner()
    print(f"\n\033[38;5;93m  {'═'*57}\033[0m")
    print(f"  \033[38;5;93m||\033[0m{BOLD}\033[38;5;228m{'  COOKIE CHECKER & CLEANER':^53}\033[0m\033[38;5;93m||\033[0m")
    print(f"\033[38;5;93m  {'═'*57}\033[0m")

    print(f"  {neon_cyan}File number (1-20) ya sdcard path dono supported hain{reset}")
    print(f"  {gold}Example: /sdcard/cookies.txt{reset}\n")
    try:
        cookie_file_input = input(f"\n{gold}  >> File number (1-20) ya path: {reset}").strip()
    except KeyboardInterrupt:
        return

    cookie_file = ""
    try:
        _num = int(cookie_file_input)
        if _num < 1 or _num > 20:
            raise ValueError
        cookie_file = f"{_num}.txt"
    except ValueError:
        if cookie_file_input:
            cookie_file = cookie_file_input
        else:
            print(f"{neon_red}  [X] Kuch nahi likha!{reset}")
            input(f"{gold}  Enter dabao...{reset}")
            return

    if not os.path.exists(cookie_file):
        print(f"{neon_red}  [X] File nahi mili: {cookie_file}{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return

    try:
        with open(cookie_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"{neon_red}  [X] {cookie_file} nahi mili!{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return
    except Exception as e:
        logger.exception("remove_expired_cookies read error: %s", e)
        print(f"{neon_red}  [X] File error.{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return

    cookie_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]

    if not cookie_lines:
        print(f"{neon_red}  [X] {cookie_file} mein cookies nahi!{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return

    total = len(cookie_lines)
    print(f"\n  \033[38;5;117m>>\033[0m File   : {neon_yellow}{cookie_file}{reset}")
    print(f"  \033[38;5;117m>>\033[0m Total  : {neon_yellow}{total} cookies{reset}")
    print(f"  \033[38;5;117m>>\033[0m Method : {neon_yellow}Full Deep Check{reset}")
    print(f"\033[38;5;240m  {'─'*57}\033[0m\n")

    valid_cookies = []
    live_count = 0
    dead_count = 0
    error_count = 0
    lock = asyncio.Lock()

    async def check_one(idx, cookie):
        nonlocal live_count, dead_count, error_count
        colored = "".join(colors[i % len(colors)] + ch + reset for i, ch in enumerate(cookie[:32]))

        is_live = await _deep_check_cookie_via_poll(cookie)
        await asyncio.sleep(0.1)
        async with lock:
            num = f"\033[38;5;245m[{idx:>3}/{total}]\033[0m"
            if is_live:
                valid_cookies.append(cookie)
                live_count += 1
                print(f"  {num} {colored}...  \033[1m\033[38;5;46m LIVE \033[0m")
            else:
                dead_count += 1
                print(f"  {num} {colored}...  \033[1m\033[38;5;196m EXPIRE \033[0m")

    tasks = [check_one(i, ck) for i, ck in enumerate(cookie_lines, 1)]
    await asyncio.gather(*tasks)

    try:
        with open(cookie_file, "w", encoding="utf-8") as f:
            for cookie in valid_cookies:
                if cookie:
                    f.write(cookie + "\n")
    except Exception as e:
        logger.exception("remove_expired_cookies write error: %s", e)
        print(f"{neon_red}  [X] File save nahi ho saki!{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return

    print(f"\n\033[38;5;93m  {'═'*57}\033[0m")
    print(f"  \033[38;5;46m>>\033[0m {BOLD}LIVE  :\033[0m  \033[38;5;46m{live_count} cookies\033[0m")
    print(f"  \033[38;5;196m>>\033[0m {BOLD}DEAD  :\033[0m  \033[38;5;196m{dead_count} cookies\033[0m")
    print(f"  \033[38;5;117m>>\033[0m {BOLD}SAVED :\033[0m  {gold}{len(valid_cookies)} cookies  >>  {cookie_file}\033[0m")
    print(f"\033[38;5;93m  {'═'*57}\033[0m\n")

    input(f"{gold}  Enter dabao (menu par wapas jao)...{reset}")


def enter_cookies():
    banner()
    print(f"\n{BOLD}\033[38;5;40m╔{'═'*59}╗{reset}")
    print(f"{BOLD}\033[38;5;40m║\033[38;5;228m{'  ══► ENTER COOKIES ◄══':^59}\033[38;5;40m║{reset}")
    print(f"{BOLD}\033[38;5;40m╚{'═'*59}╝{reset}")
    print(f"\n{BOLD}\033[38;5;51m  File Numbers:{reset}")
    for i in range(1, 21):
        end = "\n" if i % 5 == 0 else "  "
        print(f"{BOLD}\033[38;5;228m  [{i:2}]{reset}", end=end)
    print()

    try:
        file_num = input(f"\n{gold}  >> File number (1-20): {reset}").strip()
        file_num = int(file_num)
        if file_num < 1 or file_num > 20:
            raise ValueError
    except KeyboardInterrupt:
        return
    except Exception:
        print(f"{neon_red}  [X] 1-20 ke beech number dalo!{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return

    cookie_file = f"{file_num}.txt"
    print(f"\n  {neon_yellow}⚠ Note: Ek dafa mein 50 se zyada cookies paste mat karyn, warna Termux hang ho jayega.{reset}")

    try:
        with open(cookie_file, "r", encoding="utf-8", errors="ignore") as f:
            existing = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
    except Exception:
        existing = []

    mode = "replace"
    if existing:
        print(f"\n{neon_yellow}  {len(existing)} cookies already mein hain.{reset}")
        print(f"  {BOLD}\033[38;5;51m[1]{reset} Purani delete, nayi save karo")
        print(f"  {BOLD}\033[38;5;40m[2]{reset} Purani ke saath nayi add karo")
        print(f"  {BOLD}\033[38;5;196m[3]{reset} Wapas jao")
        try:
            ch = input(f"\n{gold}  >> Choose (1/2/3): {reset}").strip()
        except KeyboardInterrupt:
            return
        if ch == "3":
            return
        elif ch == "2":
            mode = "append"
        else:
            mode = "replace"

    print(f"\n{neon_cyan}  Cookies paste karo (khali Enter se finish):  {reset}")
    new_cookies = []
    idx = 1
    while True:
        try:
            line = input(f"  {BOLD}\033[38;5;228m{idx}:{reset} ").strip()
        except KeyboardInterrupt:
            break
        if not line:
            break
        lines_in = [l.strip() for l in line.split("\n") if l.strip() and not l.strip().startswith("#")]
        new_cookies.extend(lines_in)
        idx += len(lines_in)

    if not new_cookies:
        print(f"{neon_red}  [X] Koi cookie nahi di!{reset}")
        input(f"{gold}  Enter dabao...{reset}")
        return

    try:
        if mode == "append":
            final = existing + new_cookies
        else:
            final = new_cookies

        with open(cookie_file, "w", encoding="utf-8") as f:
            for c in final:
                f.write(c + "\n")
        print(f"\n{neon_green}  [+] {len(new_cookies)} cookies saved to {cookie_file}!{reset}")
        print(f"  {neon_cyan}Total: {len(final)} cookies{reset}")
    except Exception as e:
        logger.exception("enter_cookies write error: %s", e)
        print(f"{neon_red}  [X] Save nahi ho saka!{reset}")

    input(f"\n{gold}  Enter dabao (menu par wapas jao)...{reset}")


def my_cookies():
    banner()
    print(f"\n{BOLD}\033[38;5;40m╔{'═'*59}╗{reset}")
    print(f"{BOLD}\033[38;5;40m║\033[38;5;228m{'  ══► MY COOKIES -- FILE DETAILS ◄══':^59}\033[38;5;40m║{reset}")
    print(f"{BOLD}\033[38;5;40m╚{'═'*59}╝{reset}\n")

    total = 0
    any_found = False
    for i in range(1, 21):
        try:
            lines = [l.strip() for l in open(f"{i}.txt", "r", encoding="utf-8", errors="ignore").readlines()
                     if l.strip() and not l.strip().startswith("#")]
            c = len(lines)
            if c > 0:
                any_found = True
                total += c
                print(f"  {BOLD}\033[38;5;228m[{i:2}].txt{reset}  {BOLD}\033[38;5;40m{c} cookies{reset}")
            else:
                print(f"  {BOLD}\033[38;5;245m[{i:2}].txt{reset}  \033[38;5;245mKhali hai{reset}")
        except Exception:
            print(f"  {BOLD}\033[38;5;245m[{i:2}].txt{reset}  \033[38;5;245mKhali hai{reset}")

    print(f"\n{BOLD}\033[38;5;51m{'═'*61}{reset}")
    if any_found:
        print(f"  {BOLD}\033[38;5;228mTotal Cookies :{reset} {BOLD}\033[38;5;40m{total}{reset}")
    else:
        print(f"  {BOLD}\033[38;5;161mAbhi kisi bhi file mein cookies nahi hain.{reset}")
        print(f"  {BOLD}\033[38;5;245mOption [10] se cookies add karen.{reset}")
    print(f"{BOLD}\033[38;5;51m{'═'*61}{reset}")

    input(f"\n{GOLD}Press Enter to menu par wapas jao...{reset}")


def how_to_use():
    banner()
    C1 = "\033[38;5;51m"
    C2 = "\033[38;5;228m"
    C3 = "\033[38;5;40m"
    C4 = "\033[38;5;205m"
    C5 = "\033[38;5;123m"
    C6 = "\033[38;5;208m"

    options = [
        ("1", "REACTIONS", [
            "Yeh option kisi bhi Facebook post par reactions lagata hai.",
            "Aap chahen to Like lagayen, Love lagayen, Care, Wow, Haha, Sad ya Angry --",
            "sab kuch is ek option se ho jata hai!",
            "",
            "Step 1 : Main menu kholen aur option [1] REACTIONS select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain, jaise 1 ya 2 etc.",
            "",
            "Step 3 : Account type chunen:",
            "         [1] = Sirf IDs use karo (normal accounts)",
            "         [2] = Sirf Pages use karo (Facebook pages)",
            "         [3] = IDs aur Pages dono use karo",
            "",
            "Step 4 : Post ka link ya Post ID paste karen.",
            "         Link example  : https://www.facebook.com/share/p/abc123",
            "         ID example    : 1234567890123456",
            "         Dono mein se jo bhi aap ke paas ho woh paste karen.",
            "",
            "Step 5 : Reaction type select karen:",
            "         [1] = Like",
            "         [2] = Love",
            "         [3] = Care",
            "         [4] = Wow",
            "         [5] = Haha",
            "         [6] = Sad",
            "         [7] = Angry",
            "         Ek reaction chahiye to sirf 1 number likhen, jaise: 1",
            "         Ek se zyada chahiye to plus laga kar likhen, jaise: 1+2+4",
            "",
            "Step 6 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 7 : Enter dabayein aur reactions lagni shuru ho jayengi!",
            "         Screen par har account ka status live dikhega.",
        ]),
        ("2", "COMMENTS", [
            "Yeh option kisi bhi Facebook post par automatic comments karta hai.",
            "Is software mein comments aap seedha software ke andar likhte hain,",
            "koi alag file ki zaroorat nahi hoti.",
            "",
            "Step 1 : Main menu kholen aur option [2] COMMENTS select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Account type chunen:",
            "         [1] = Sirf IDs",
            "         [2] = Sirf Pages",
            "         [3] = IDs aur Pages dono",
            "",
            "Step 4 : Post ka link ya Post ID paste karen.",
            "         Link example : https://www.facebook.com/share/p/abc123",
            "         ID example   : 1234567890123456",
            "",
            "Step 5 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 6 : Har account kitne comments kare woh number likhen.",
            "         Jaise 1 likhen to har account ek comment karega.",
            "         3 likhen to har account teen comments karega.",
            "",
            "Step 7 : Ab comments likhne ka waqt aayega.",
            "         Screen par aayega: Comments likho (ek line ek comment)",
            "         Aap ek comment likh kar Enter dabayein, agla likhein.",
            "         Jaise:",
            "         Great post!   [Enter]",
            "         Masha Allah   [Enter]",
            "         Zabardast     [Enter]",
            "         Jab sab comments likh lein to khali Enter dabayein.",
            "",
            "Step 8 : Kaam shuru ho jayega!",
            "         Software aapke likhe comments mein se random choose kar ke lagata hai.",
        ]),
        ("3", "JOIN GROUP", [
            "Yeh option Facebook groups mein automatically join karta hai.",
            "Sab accounts ek ek karke usi group mein join karte hain",
            "jo aap seedha software ke andar paste karte hain.",
            "",
            "Step 1 : Main menu kholen aur option [3] JOIN GROUP select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Account type chunen:",
            "         [1] = Sirf IDs",
            "         [2] = Sirf Pages",
            "         [3] = IDs aur Pages dono",
            "",
            "Step 4 : Group ID paste karen.",
            "         Group ID Facebook group ke link mein se milti hai.",
            "         Link example : https://www.facebook.com/groups/123456789012345",
            "         Is link mein jo number hai woh Group ID hai, jaise: 123456789012345",
            "         Woh number seedha paste kar dein.",
            "",
            "Step 5 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 6 : Enter dabayein, joining shuru ho jayegi!",
            "         Sab accounts us ek group mein join ho jayenge.",
        ]),
        ("4", "FOLLOWERS", [
            "Yeh option kisi bhi Facebook user ko automatically follow karta hai.",
            "",
            "Step 1 : Main menu kholen aur option [4] FOLLOWERS select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Account type chunen:",
            "         [1] = Sirf IDs",
            "         [2] = Sirf Pages",
            "         [3] = IDs aur Pages dono",
            "",
            "Step 4 : User ID paste karen jise follow karna hai.",
            "         User ID Facebook profile ke link mein hoti hai.",
            "         Link example : https://www.facebook.com/profile.php?id=100012345678901",
            "         Is link mein jo number hai woh User ID hai, jaise: 100012345678901",
            "         Woh number seedha paste kar dein.",
            "",
            "Step 5 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 6 : Enter dabayein, following shuru ho jayegi!",
            "         Sab accounts us ek user ko follow kar lenge.",
        ]),
        ("5", "PAGE CREATE", [
            "Yeh option aapke accounts se automatically naye Facebook pages banata hai.",
            "",
            "Step 1 : Main menu kholen aur option [5] PAGE CREATE select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Page ka naam prefix likhen.",
            "         Prefix matlab shuruaat ka naam, jaise 'My Shop' likhen",
            "         to pages kuch is tarah banenge: My Shop 1, My Shop 2 etc.",
            "",
            "Step 4 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 5 : Enter dabayein, pages banana shuru ho jayega!",
            "         Har account ek naya page banayega.",
        ]),
        ("6", "PAGE ACTIVATE", [
            "Yeh option aapke Facebook accounts ke pages ko activate karta hai.",
            "Jo pages inactive hain unhe active status mein le aata hai.",
            "",
            "Step 1 : Main menu kholen aur option [6] PAGE ACTIVATE select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 4 : Enter dabayein, activation shuru ho jayegi!",
            "         Software khud pages dhundega aur activate karega.",
        ]),
        ("7", "DP UPLOAD", [
            "Yeh option automatically Facebook profile picture upload karta hai.",
            "Aap jitni images rakhein -- software unhe accounts par lagata hai.",
            "",
            "Step 1 : Pehle pics.txt file mein image file ka pura path likhen.",
            "         Yeh file software wali folder mein hogi.",
            "         Mobile par example:",
            "         /sdcard/meri_photo.jpg",
            "         /sdcard/Download/profile.png",
            "         PC par example:",
            "         C:/Users/AAC/Pictures/photo.jpg",
            "         Har line mein ek image ka path likhen.",
            "",
            "Step 2 : Main menu kholen aur option [7] DP UPLOAD select karen.",
            "",
            "Step 3 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 4 : Delay set karen.",
            "         0        = Full Fast  (koi rukawat nahi)",
            "         0.1-0.6  = Medium Speed (thoda slow)",
            "         1-60     = Slow Speed  (safe mode, zyada safe)",
            "",
            "Step 5 : Enter dabayein, DP upload hona shuru ho jayegi!",
            "         Software random image chunega pics.txt se.",
        ]),
        ("8", "POLL VOTING", [
            "Yeh option Facebook polls mein automatically vote dalta hai.",
            "Aapke sab accounts ek hi option ko vote karte hain.",
            "",
            "Step 1 : Main menu kholen aur option [8] POLL VOTING select karen.",
            "",
            "Step 2 : Cookies file number dein -- woh file jis mein",
            "         aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Poll ka pura link paste karen.",
            "         Example: https://www.facebook.com/groups/123/posts/456",
            "",
            "Step 4 : Software poll ke options screen par dikha dega.",
            "         Jaise:",
            "         [1] Option A   Votes: 150",
            "         [2] Option B   Votes: 89",
            "         Aap jis option ko vote dena chahte hain uska number likhen.",
            "",
            "Step 5 : Account type chunen:",
            "         [1] = Sirf IDs",
            "         [2] = Sirf Pages",
            "         [3] = IDs aur Pages dono",
            "",
            "Step 6 : Enter dabayein, voting shuru ho jayegi!",
            "         Sab accounts selected option ko vote karenge.",
        ]),
        ("9", "COOKIE CLEANER", [
            "Yeh option expired ya kharab cookies ko automatically hata deta hai.",
            "Jab cookies expire ho jaati hain to kaam nahi karti --",
            "yeh option unhe dhundh kar delete kar deta hai.",
            "",
            "Step 1 : Main menu kholen aur option [9] COOKIE CLEANER select karen.",
            "         Yeh option seedha khul jaata hai, pehle cookies",
            "         file number poochha nahi jaata.",
            "",
            "Step 2 : File number dein jis mein aap ne apni cookies rakhi hain.",
            "",
            "Step 3 : Software har cookie ko ek ek check karega.",
            "         Valid cookie par likha aayega: VALID",
            "         Expired cookie par likha aayega: EXPIRED (Removed)",
            "",
            "Step 4 : Kaam khatam hone par batayega:",
            "         Kitni valid cookies bachi hain",
            "         Kitni expired delete hui hain",
            "",
            "Tip: Yeh option haftay mein ek baar zaroor chalayein",
            "     taake kharab cookies hati rahein aur kaam smooth ho.",
        ]),
        ("10", "ENTER COOKIES", [
            "Yeh option aapki Facebook cookies save karne ke liye hai.",
            "Cookie ek special key hoti hai jo aapke Facebook account ko",
            "software ko access dene deti hai -- bilkul password ki tarah.",
            "",
            "Step 1 : Main menu kholen aur option [10] ENTER COOKIES select karen.",
            "",
            "Step 2 : File number chunen jis mein cookies save karni hain.",
            "         1 se 20 tak koi bhi number chunen.",
            "         Ek file mein aap jitni chahein utni cookies rakh sakte hain.",
            "         Jaise file 1 mein 500 cookies bhi rakh sakte hain.",
            "",
            "Step 3 : Agar file bilkul khali hai to seedha paste mode aayega.",
            "         Agar pehle se cookies hain to 3 options milenge:",
            "         [1] = Purani sab delete kar ke nayi save karo",
            "         [2] = Purani ke saath neeche aur nayi add karo",
            "         [3] = Sirf dekhna tha, wapas menu par jao",
            "",
            "Step 4 : Cookies paste karna shuru karen.",
            "         Screen par number dikhega jaise 1, 2, 3...",
            "         Aap do tarike se cookies de sakte hain:",
            "",
            "         Tarika 1 -- Ek ek karke:",
            "         Har number par ek cookie paste karen aur Enter dabayein.",
            "         Next number aayega -- agla cookie paste karen.",
            "         Jab sab ho jayen to khali Enter dabayein -- save!",
            "",
            "         Tarika 2 -- Ek saath sab:",
            "         Agar aap ke paas pehle se saari cookies copy hain",
            "         to ek saath bhi paste kar sakte hain.",
            "         Sab paste ho jayen ge aur software khud count karega.",
            "         Aakhir mein khali Enter dabayein -- save!",
            "",
            "Cookie kahan se milti hai?",
            "  Browser mein Facebook kholen, F12 dabayein,",
            "  Application tab mein jayen, Cookies section mein",
            "  c_user aur xs wali values copy karen.",
            "  Ya koi cookie extractor extension use karen.",
        ]),
        ("11", "MY COOKIES", [
            "Yeh option aapki saari cookie files ka summary dikhata hai.",
            "Kaunsi file mein kitni cookies hain -- sab ek jagah dikh jaata hai.",
            "",
            "Step 1 : How To Use menu mein option [11] MY COOKIES select karen.",
            "",
            "Step 2 : Screen par 1 se 20 tak sab files dikhegi:",
            "         Agar file mein cookies hain to count dikhega",
            "         Agar file khali hai to 'Khali hai' likha aayega",
            "",
            "Step 3 : Sab ke neeche total cookies ka count bhi dikhega.",
            "",
            "Tip: Kaam shuru karne se pehle yahan check karo",
            "     ke sahi file mein cookies hain ya nahi.",
        ]),
    ]

    while True:
        banner()
        print(f"\n{BOLD}{C1}╔{'═'*59}╗{reset}")
        print(f"{BOLD}{C1}║{C2}{'  ══► HOW TO USE -- COMPLETE GUIDE ◄══':^59}{C1}║{reset}")
        print(f"{BOLD}{C1}╚{'═'*59}╝{reset}\n")
        for opt in options:
            print(f"  {BOLD}{C4}[{opt[0]:2}]{reset} {BOLD}{C3}{opt[1]}{reset}")
        print(f"\n  {BOLD}{C6}[0]{reset}  Wapas Main Menu")
        print(f"{BOLD}{C1}{'═'*61}{reset}")

        try:
            sel = input(f"\n{BOLD}{C2}══► Kaunsa option samajhna hai? Number likhen: {reset}").strip()
        except KeyboardInterrupt:
            break

        if sel == "0":
            break

        found = None
        for opt in options:
            if sel == opt[0]:
                found = opt
                break

        if sel == "11":
            my_cookies()
            continue

        if not found:
            print(f"{NEON_RED}[X] Yeh number list mein nahi hai, dobara try karen.{reset}")
            input(f"{GOLD}Press Enter...{reset}")
            continue

        banner()
        print(f"\n{BOLD}{C1}╔{'═'*59}╗{reset}")
        print(f"{BOLD}{C1}║{C4}{f'  ══► OPTION [{found[0]}] -- {found[1]} ◄══':^59}{C1}║{reset}")
        print(f"{BOLD}{C1}╚{'═'*59}╝{reset}\n")
        for line in found[2]:
            if line == "":
                print()
            elif line.startswith("Step"):
                print(f"  {BOLD}{C2}{line}{reset}")
            else:
                print(f"  {C5}{line}{reset}")
        print(f"\n{BOLD}{C3}  Umeed hai yeh samajh aa gaya! Koi aur option dekhna ho to wapas jayen.{reset}")
        input(f"\n{GOLD}Press Enter to wapas list par jayen...{reset}")


# =========================================================
# MURSHAD ENGINE - FBComment Class (Exact Murshad Logic)
# =========================================================

from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed

print_lock = threading.Lock()

USER_AGENTS_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (Windows NT 10.0; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.2592.56',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.80',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.0.0 Mobile Safari/537.36 [FBAN/FB4A;FBAV/473.0.0.22.112;FBBV/500642340;FBLC/en_US;FBID/phone;]',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/470.0.0.122.108;FBBV/499881122;FBDV/iPhone15,2;FBMD/iPhone;FBLC/en_US;FBID/phone;]',
]


def get_random_delay(user_delay):
    if user_delay == 0:
        return 0.001
    min_delay = 0.001
    max_delay = max(min_delay, user_delay)
    return random.uniform(min_delay, max_delay)


class FBComment:
    def __init__(self, cookie, post_id, comments_per_id, delay, user_agent, use_emoji=True, inline_comments=None):
        self.cookie = cookie
        self.post_id = post_id
        self.comments_per_id = comments_per_id
        self.delay = delay
        self.user_agent = user_agent
        self.use_emoji = use_emoji
        self.inline_comments_override = inline_comments  # Alisha se pass ki hui comments

        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=100, max_retries=2)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        self.headers = {
            'authority': 'business.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': cookie,
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent
        }
        self.token = None
        self.fb_dtsg = None
        self.uid = '0'
        self.pro5 = []
        self.comments_cache = self._load_comments()

    def _load_comments(self):
        # Pehle Alisha ke inline comments check karo
        if self.inline_comments_override:
            return self.inline_comments_override
        # Phir comments.txt se load karo
        try:
            with open('comments.txt', mode='r', encoding='utf-8') as f:
                comments = [x.strip() for x in f.read().split('\n') if x.strip() and not x.strip().startswith('#')]
            if comments:
                return comments
        except Exception:
            pass
        return ["Great post!"]

    def getuid(self):
        try:
            self.uid = re.findall(r'c_user=(\d+)', self.cookie)[0]
            return True
        except Exception:
            return False

    def getdata(self):
        """Primary: business.facebook.com"""
        try:
            req = self.session.get(
                'https://business.facebook.com/business_locations',
                headers=self.headers,
                timeout=(3, 5)
            ).text
            tok = re.search(r'\["EAAG\w+', req)
            dtsg = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', req)
            if tok and dtsg:
                self.token = tok.group(0).replace('["', '')
                self.fb_dtsg = dtsg.group(1)
                return True
            return False
        except Exception:
            return False

    def getdata_www_fallback(self):
        """Fallback: www.facebook.com"""
        try:
            headers_www = dict(self.headers)
            headers_www['authority'] = 'www.facebook.com'
            headers_www['cookie'] = self.cookie
            req = self.session.get(
                'https://www.facebook.com/',
                headers=headers_www,
                timeout=(5, 10)
            ).text
            # Login check
            if 'useCometLogInForm' in req or 'name="login"' in req:
                return False
            tok = re.search(r'\["EAAG\w+', req)
            if tok:
                self.token = tok.group(0).replace('["', '')
            for pat in [
                r'"DTSGInitialData",\[\],{"token":"(.*?)"}',
                r'name="fb_dtsg" value="(.*?)"',
                r'"fb_dtsg"\s*:\s*"([^"]+)"',
            ]:
                m = re.search(pat, req)
                if m:
                    self.fb_dtsg = m.group(1)
                    break
            if self.fb_dtsg:
                return True
            return False
        except Exception:
            return False

    def getdata_with_fallback(self):
        """Try business.facebook.com first, then www.facebook.com"""
        if self.getdata():
            return True
        if self.getdata_www_fallback():
            return True
        return False

    def get_pages(self):
        self.pro5 = []
        try:
            link = f'https://graph.facebook.com/v18.0/me/accounts?fields=access_token,additional_profile_id,locations{{id}}&limit=100&access_token={self.token}'
            resp = self.session.get(link, headers=self.headers, timeout=(3, 5))
            if 'error' in resp.text:
                return False
            data = resp.json()['data']
            for get in data:
                try:
                    id_pro5 = get['additional_profile_id']
                    self.pro5.append(id_pro5)
                except Exception:
                    pass
            return True if self.pro5 else False
        except Exception:
            return False

    def post_comment(self, idpro5):
        global comment_count

        # pfbid fix: agar self.real_feedback_id set hai to woh use karo
        # warna purani numeric fallback (sirf non-group posts ke liye)
        if getattr(self, 'real_feedback_id', None):
            idbv = self.real_feedback_id
        else:
            text = f'feedback:{self.post_id}'
            idbv = base64.b64encode(text.encode()).decode('utf-8')

        cookie = self.cookie or ""
        if idpro5 != self.uid:
            if cookie.endswith(';'):
                cookie = self.cookie + 'i_user=' + idpro5 + ';'
            else:
                cookie = self.cookie + ';i_user=' + idpro5 + ';'

        headers = {
            'authority': 'www.facebook.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': cookie,
            'referer': 'https://www.facebook.com/settings?tab=profile_access',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent
        }

        # Comment pick + 70% emoji
        base_comment = random.choice(self.comments_cache)
        if self.use_emoji and random.random() < 0.7:
            noidung = base_comment + " " + random.choice(EMOJIS)
        else:
            noidung = base_comment

        tracking_data = '{"assistant_caller":"comet_above_composer","conversation_guide_session_id":"' + str(uuid.uuid4()) + '","conversation_guide_shown":null}'

        # Group post vs open/timeline post ke liye alag values
        _is_group = getattr(self, 'slow_selc', 'timeline') == 'group'
        _feed_location = "GROUP" if _is_group else "PERMALINK"
        _comments_key  = "CometGroupUFIRootQuery" if _is_group else "CometSinglePostRoute"
        _attribution   = (
            "GroupsCometFeedUFIRootQuery.react,comet.groups.feed,via_cold_start,1692175639975,676866,,"
            if _is_group else
            "CometSinglePostRoot.react,comet.post.single,via_cold_start,1692175639975,676866,,"
        )

        variables_json = {
            "displayCommentsFeedbackContext": None,
            "displayCommentsContextEnableComment": None,
            "displayCommentsContextIsAdPreview": None,
            "displayCommentsContextIsAggregatedShare": None,
            "displayCommentsContextIsStorySet": None,
            "feedLocation": _feed_location,
            "feedbackSource": 2,
            "focusCommentID": None,
            "groupID": None,
            "includeNestedComments": False,
            "input": {
                "attachments": None,
                "feedback_id": idbv,
                "formatting_style": None,
                "message": {"ranges": [], "text": noidung},
                "attribution_id_v2": _attribution,
                "is_tracking_encrypted": True,
                "tracking": ["AZVuNDRPni4Q9--BKAtfuWNHMy_89-NxE3pTjMT9_lOt3iM-qSkUzLEZ_FeFl_sq_zGZXfu1Fu2tgEDHR74HuGk2k2JwNfQuV71T2tiowryfVZovjCFl_Bo6_xr4CpG2rlkfQoGvpNv3AvFpm1eCLJZghuF4Wy5Kj7hc57RT6pX0l7OIcseByxSD8bm81CPU3-sIw9a3vx_cYDJKn2GxVBrkGeK_FUpFuxdMdQHzVQ7j44_D858NuZ_ulXBRLfPJCg5tHChFqmeHOAXCCV1GDRhtdeuoa-yyDtVGZwY7EY8F51nC8PBCYrATMpXr2W0w6PrWCyQFXSDrZWyUDrMq6QjnjQX3DifScfOmUKXYFWlbaetXELak_wuDysgcTT68SyCpUPqhQ-Vhp9LHPu8f7GjotHG4bXKoV0SI1azRwmspmG5KCqz1eXDLZFDYiUQjZHuncSXsV3xl--AHwvNggXxeoxe9PVYhHkDtf8I-h4_T5xj-PnHPrlf0lqo2kmojPGkNPriIOPDCbaOcyeXn2DRarKaR1sC_5YI31m3cyohfef_ZhBmnU4w9DUhxcHxQN3mqp_an5A3H2x4Z_RQ3ymOIADDRA4hO5AGFrlPFxutuNoimAGUEZjUr0S8TScHcUD4FfooX0WPC5sfAco8nhlfiimEFL7oe0LwgK3e4bLOVVW-gIpjHP9z2A7S9Sd87jaeqXYYr8NoJETpAn1YFxDSbtrkF3_jnlvgMKfe01ODdiBbc3sIDmh72H-152z_qS3Y_ihz4983UXURphxRcEGX3M0aHB3Uhi7SvKMnXKUbA9P2ErZJ9ify8qujIsigmhK6j5fXBT1vu5ZS4EDCeUty1ogYFfCuY4dBvcuhx6N7FkXsJQ08etPNz-3WvylFOAyP5b2HAcXpgmV-F-3ShhkTNPhaMW2ny6FlndR1aniY--Tbhib3l7dvOcs_rj-A-OrV6v4vRKBSlwF2l6h8J2sysriPzUJgSMLVlCfzvzSHfqtK6DzHt2lpHUtlSNtJ6rw_-LJYfJ7JNFDPQT00PODuYlKVkkZWJLX_mxkkCKibmzUfl6_hmM6k-w1gTPwR5H7Q", tracking_data],
                "feedback_source": "OBJECT",
                "idempotence_token": f"client:{str(uuid.uuid4())}",
                "session_id": str(uuid.uuid4()),
                "actor_id": idpro5,
                "client_mutation_id": "4"
            },
            "inviteShortLinkKey": None,
            "renderLocation": None,
            "scale": 1,
            "useDefaultActor": False,
            "UFI2CommentsProvider_commentsKey": _comments_key
        }

        data = {
            'fb_dtsg': self.fb_dtsg,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'CometUFICreateCommentMutation',
            'variables': json.dumps(variables_json),
            'server_timestamps': 'true',
            'doc_id': '6379115828844234'
        }

        try:
            response = self.session.post(
                'https://www.facebook.com/api/graphql/',
                headers=headers,
                data=data,
                timeout=(5, 15)
            )
        except Exception as _net_e:
            colored_id = "".join(colors[(i + comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(idpro5)))
            print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
            return

        colored_id = "".join(colors[(i + comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(idpro5)))


        if response.status_code != 200:
            print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mFAILED\033[0m \033[38;5;255m==> Actor: {colored_id} (HTTP {response.status_code}){reset}")
            return

        # Parse response properly
        try:
            resp_json = json.loads(response.text.replace("for (;;);", "").strip())
        except Exception as _parse_e:
            resp_json = {}

        # Check comment_create
        comment_create_val = resp_json.get("data", {}).get("comment_create", "NOT_PRESENT") if isinstance(resp_json, dict) else "NOT_PRESENT"
        if comment_create_val is not None and comment_create_val != "NOT_PRESENT":
            with print_lock:
                comment_count += 1
                colored_id2 = "".join(colors[(i + comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(idpro5)))
                print(f"\033[38;5;51m[\033[38;5;87m++\033[38;5;51m] \033[1m\033[38;5;87mCOMMENT \033[38;5;45mSUCCESS\033[0m \033[38;5;51m==> \033[38;5;255mActor: {colored_id2} \033[38;5;51m[\033[38;5;87m{comment_count}\033[38;5;51m]{reset}")
            return

        # Error detection
        errors = resp_json.get("errors", []) if isinstance(resp_json, dict) else []
        err_msg = str(errors[0].get("message", "")).lower() if errors else str(resp_json).lower()

        if "rate limit" in err_msg or "too many" in err_msg or "limit how often" in err_msg or "temporarily" in err_msg:
            print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mRATE LIMIT\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
        elif "account has been disabled" in err_msg or "account_disabled" in err_msg or "suspended" in err_msg:
            print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mACCOUNT SUSPENDED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
        else:
            print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mFAILED: {err_msg[:60]}\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")


# =========================================================
# END OF MURSHAD ENGINE
# =========================================================


def get_delay():
    while True:
        try:
            print(f"{neon_yellow}select speed  0 = Full Fast  |  0.1 se 0.6 = Medium  |  1 se 60 = Slow{reset}")
            delay_input = input(f"{electric_blue}-> Speed inter: {reset}").strip()
            if not delay_input:
                print(f"{neon_red}[X] Speed nahi likhi!{reset}")
                continue
            d = float(delay_input)
            if d < 0.0:
                print(f"{neon_red}[X] Speed negative nahi ho sakti.{reset}")
                continue
            if d > 60.0:
                print(f"{neon_red}[X] Maximum 60 seconds hai.{reset}")
                continue
            if d == 0:
                print(f"{neon_green}  [+] Full Fast!{reset}")
            elif d <= 0.6:
                print(f"{neon_cyan}  [+] Medium Speed!{reset}")
            else:
                print(f"{neon_yellow}  [+] Slow Speed!{reset}")
            return d
        except ValueError:
            print(f"{neon_red}[X] Ghalat input! Jaise: 0, 0.3, 1, 5{reset}")
        except Exception as e:
            logger.exception("get_delay input error: %s", e)
            print(f"{neon_red}[X] Input error.{reset}")


# -------------------------
# FB class (core) - async
# -------------------------

class FB:
    def __init__(self, user, password, twofa, cookie, jsondata, cv, count):
        self.user = user
        self.password = password
        self.twofa = twofa
        self.cookie = cookie
        self.count = count
        self.cv = cv
        self.headers = {
            "authority": "business.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="8", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"10.0.0"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": random.choice(USER_AGENTS),
        }
        self.token = None
        self.fb_dtsg = None
        self.pro5 = []

        # Cookie clean karo - "cookie: " prefix hata do
        if self.cookie and self.cookie != "no":
            _c = self.cookie.strip()
            if _c.lower().startswith("cookie:"):
                self.cookie = _c[7:].strip()

        # Parse cookie into dict for aiohttp session
        self._cookie_jar = {}
        try:
            if self.cookie and self.cookie != "no":
                self._cookie_jar = parse_cookie_string(self.cookie)
        except Exception as e:
            logger.exception("FB.__init__: failed to parse cookies: %s", e)

        self.account_type = None
        try:
            if cv == "1":
                self.account_type = jsondata["1"]["type"]
                self.idbv = jsondata["1"]["idbv"]
                self.camxuc = jsondata["1"]["camxuc"]
                self.delay = jsondata["1"]["delay"]
                self.reaction_mode = jsondata["1"].get("reaction_mode", "fast")
                self._post_link_cv1 = jsondata["1"].get("post_link", "")
                # Note: pfbid fetch async main() mein hogi; abhi numeric fallback
                text = f"feedback:{self.idbv}"
                self.idbv = base64.b64encode(text.encode()).decode("utf-8")
            if cv == "2":
                self.account_type = jsondata["2"]["type"]
                self.idbv = jsondata["2"]["idbv"]
                self.count_per_unit = jsondata["2"]["count"]
                self.delay = jsondata["2"]["delay"]
                self.inline_comments = jsondata["2"].get("inline_comments", [])
                self.cmt_mode = jsondata["2"].get("mode", "fast")
                self.slow_selc = jsondata["2"].get("slow_selc", "timeline")
                self.use_emoji = jsondata["2"].get("use_emoji", True)
                self._post_link_cv2 = jsondata["2"].get("post_link", "")
                # pfbid fix: post_link set hai to async main() mein real feedback_id fetch hogi
                # Abhi sirf numeric fallback as placeholder
                text = f"feedback:{self.idbv}"
                self.idbv = base64.b64encode(text.encode()).decode("utf-8")
            if cv == "3":
                self.account_type = jsondata["3"]["type"]
                self.delay = jsondata["3"]["delay"]
                self.group_id = jsondata["3"].get("group_id", "")
            if cv == "4":
                self.account_type = jsondata["4"]["type"]
                self.delay = jsondata["4"]["delay"]
                self.follow_id = jsondata["4"].get("follow_id", "")
                self.follow_sub_mode = jsondata["4"].get("follow_sub_mode", "1")
            if cv == "5":
                self.page_name = jsondata["5"]["page_name"]
                self.delay = jsondata["5"]["delay"]
            if cv == "6":
                self.delay = jsondata["6"]["delay"]
                self.pa_method = jsondata["6"].get("pa_method", "1")

            if cv == "8":
                self.poll_data = jsondata["8"]["poll_data"]
                self.poll_count = jsondata["8"].get("poll_count", 0)
                self.account_type = jsondata["8"].get("type", None)
            if cv == "13":
                self.poll_data = jsondata["13"]["poll_data"]
                self.idbv = jsondata["13"]["idbv"]
                self.raw_post_id_13 = jsondata["13"].get("raw_post_id", "")
                self.post_link_13 = jsondata["13"].get("post_link", "")
                self.inline_comments = jsondata["13"].get("inline_comments", [])
                self.account_type = jsondata["13"].get("type", None)
                self.delay = jsondata["13"].get("delay", 0)
        except Exception as e:
            logger.exception("FB.__init__ JSON data parse error: %s", e)

    def _make_session(self):
        """Create a new aiohttp ClientSession with cookie jar."""
        connector = _make_connector()
        jar = aiohttp.CookieJar(unsafe=True)
        session = aiohttp.ClientSession(
            connector=connector,
            cookie_jar=jar,
            timeout=_make_timeout(),
        )
        # Inject cookies - invalid keys skip karo
        if self._cookie_jar:
            for k, v in self._cookie_jar.items():
                k = k.strip()
                # aiohttp mein space ya colon wale keys illegal hain
                if not k or " " in k or ":" in k:
                    continue
                try:
                    session.cookie_jar.update_cookies({k: v})
                except Exception:
                    pass
        return session

    async def _open_session(self):
        """Per-account shared session open karo."""
        try:
            if not getattr(self, '_session', None) or self._session.closed:
                self._session = self._make_session()
        except Exception as e:
            logger.exception("_open_session error: %s", e)
            self._session = self._make_session()

    async def _close_session(self):
        """Session properly close karo."""
        try:
            s = getattr(self, '_session', None)
            if s and not s.closed:
                await s.close()
            self._session = None
            await asyncio.sleep(0.01)  # pending callbacks flush
        except Exception:
            pass

    def _get_session(self):
        """Shared session return karo."""
        if getattr(self, '_session', None) and not self._session.closed:
            return self._session
        self._session = self._make_session()
        return self._session

    def _get_cookie_for_actor(self, actor_id):
        try:
            if actor_id != getattr(self, "uid", actor_id):
                if self.cookie.endswith(";"):
                    return self.cookie + "i_user=" + actor_id + ";"
                else:
                    return self.cookie + ";i_user=" + actor_id + ";"
            else:
                return self.cookie
        except Exception as e:
            logger.exception("_get_cookie_for_actor error: %s", e)
            return self.cookie

    def _headers_with_cookie(self, cookie_str):
        h = self.headers.copy()
        if cookie_str:
            h["Cookie"] = cookie_str
        return h

    def getuid(self):
        try:
            self.uid = re.findall("c_user=(\\d*)", self.cookie)[0]
            return True
        except Exception:
            pass
        return False

    def datapoll(self, req, actor):
        try:
            text = str(req)
            __a = str(random.randrange(1, 6))
            __hs = safe_search_group1(r'"haste_session":"(.*?)"', text)
            __ccg = safe_search_group1(r'"connectionClass":"(.*?)"', text)
            __rev = safe_search_group1(r'"__spin_r":(.*?),', text)
            __spin_r = __rev or "0"
            __spin_b = safe_search_group1(r'"__spin_b":"(.*?)"', text)
            __spin_t = safe_search_group1(r'"__spin_t":(.*?),', text)
            __hsi = safe_search_group1(r'"hsi":"(.*?)"', text)
            fb_dtsg = safe_search_group1(r'"DTSGInitialData",\[],{"token":"(.*?)"}', text)
            jazoest = safe_search_group1(r'jazoest=(.*?)"', text) or safe_search_group1(r'jazoest=(\d+)', text)
            lsd = safe_search_group1(r'"LSD",\[],{"token":"(.*?)"}', text) or safe_search_group1(r'name="lsd" value="(.*?)"', text)
            if not fb_dtsg or not lsd:
                logger.error("datapoll: missing fb_dtsg or lsd; fb_dtsg=%s lsd=%s", bool(fb_dtsg), bool(lsd))
                return None
            return {
                "av": actor,
                "__aaid": "0",
                "__user": actor,
                "__a": __a,
                "__hs": __hs,
                "dpr": "2",
                "__ccg": __ccg,
                "__rev": __rev,
                "__hsi": __hsi,
                "__comet_req": "15",
                "fb_dtsg": fb_dtsg,
                "jazoest": jazoest,
                "lsd": lsd,
                "__spin_r": __spin_r,
                "__spin_b": __spin_b,
                "__spin_t": __spin_t,
            }
        except Exception as e:
            logger.exception("datapoll failed: %s", e)
            return None

    async def do_sleep(self):
        try:
            d = getattr(self, "delay", 0)
            if d == 0:
                t = random.uniform(0.001, 0.01)
            else:
                t = random.uniform(0.01, max(0.01, d))
            await asyncio.sleep(t)
        except Exception as e:
            logger.exception("do_sleep error: %s", e)

    async def login(self):
        try:
            if self.cookie == "no":
                return {"status": "Fail", "cookie": self.cookie}
            try:
                self.uid = re.findall(r"c_user=(\d*)", self.cookie)[0]
            except Exception:
                self.uid = None
            if not self.uid:
                return {"status": "Fail", "cookie": self.cookie}

            headget = self._headers_with_cookie(self.cookie)

            session = self._get_session()
            # METHOD 1: business.facebook.com
            try:
                async with session.get("https://business.facebook.com/business_locations", headers=headget) as resp:
                    req = await resp.text()
                tok = re.search(r'\["EAAG\w+', req)
                dtsg = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', req)
                if tok and dtsg:
                    self.token = tok.group(0).replace('["', "")
                    self.fb_dtsg = dtsg.group(1)
                    return {"status": "Success", "cookie": self.cookie}
            except Exception:
                pass

            # METHOD 2: fallback web.facebook.com
            async with session.get("https://web.facebook.com/?_rdc=1&_rdr", headers=headget) as resp:
                text = await resp.text()

            if 'name="login"' in text or "useCometLogInForm" in text or 'title="Log in to Facebook"' in text:
                return {"status": "Fail", "cookie": self.cookie}

            try:
                tok = re.search(r'\["EAAG\w+', text)
                self.token = tok.group(0).replace('["', "") if tok else None
            except Exception as e:
                logger.exception("login token extraction error: %s", e)
                self.token = None

            fb_dtsg = ""
            for pat in [r'"DTSGInitialData",\[\],{"token":"(.*?)"}', r'name="fb_dtsg" value="(.*?)"', r'"fb_dtsg"\s*:\s*"([^"]+)"']:
                fb_dtsg = safe_search_group1(pat, text)
                if fb_dtsg:
                    break
            self.fb_dtsg = fb_dtsg or None

            return {"status": "Success", "cookie": self.cookie}
        except Exception as e:
            logger.exception("login failed: %s", e)
            return {"status": "Fail", "cookie": self.cookie}

    async def get_dtsg(self):
        try:
            if getattr(self, "fb_dtsg", None):
                return True
            headget = self._headers_with_cookie(self.cookie)

            session = self._get_session()
            # METHOD 1: business.facebook.com
            try:
                async with session.get("https://business.facebook.com/business_locations", headers=headget) as resp:
                    req = await resp.text()
                dtsg = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', req)
                if dtsg:
                    self.fb_dtsg = dtsg.group(1)
                    tok = re.search(r'\["EAAG\w+', req)
                    if tok:
                        self.token = tok.group(0).replace('["', "")
                    return True
            except Exception:
                pass

            # METHOD 2: fallback web.facebook.com
            async with session.get("https://web.facebook.com/?_rdc=1&_rdr", headers=headget) as resp:
                text = await resp.text()

            if 'name="login"' in text or "useCometLogInForm" in text:
                return False
            for pat in [r'"DTSGInitialData",\[\],{"token":"(.*?)"}', r'name="fb_dtsg" value="(.*?)"', r'"fb_dtsg"\s*:\s*"([^"]+)"']:
                m = re.search(pat, text)
                if m:
                    self.fb_dtsg = m.group(1)
                    return True
            return False
        except Exception as e:
            logger.exception("get_dtsg failed: %s", e)
            return False

    async def get_page_data(self):
        try:
            if not self.token:
                headget = self._headers_with_cookie(self.cookie)
                session = self._get_session()
                _token_found = False
                # Method 1: business.facebook.com (PC pe fast)
                try:
                    async with session.get("https://business.facebook.com/business_locations", headers=headget) as resp:
                        req = await resp.text()
                    tok = re.search(r'\["EAAG\w+', req)
                    if tok:
                        self.token = tok.group(0).replace('["', "")
                        _token_found = True
                except Exception:
                    pass
                # Method 2: mbasic.facebook.com (mobile/Termux pe reliable)
                if not _token_found:
                    try:
                        _mbasic_headers = dict(headget)
                        _mbasic_headers["user-agent"] = "Mozilla/5.0 (Linux; Android 12; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                        async with session.get("https://mbasic.facebook.com/", headers=_mbasic_headers) as resp2:
                            req2 = await resp2.text()
                        tok2 = re.search(r'\["EAAG\w+', req2)
                        if tok2:
                            self.token = tok2.group(0).replace('["', "")
                            _token_found = True
                    except Exception:
                        pass
                # Method 3: www.facebook.com fallback
                if not _token_found:
                    try:
                        async with session.get("https://www.facebook.com/", headers=headget) as resp3:
                            req3 = await resp3.text()
                        tok3 = re.search(r'\["EAAG\w+', req3)
                        if tok3:
                            self.token = tok3.group(0).replace('["', "")
                            _token_found = True
                    except Exception:
                        pass
                if not _token_found:
                    return False

            self.pro5 = []
            link = f"https://graph.facebook.com/v12.0/me/accounts?fields=access_token,additional_profile_id,locations{{id}}&limit=100&access_token={self.token}"
            session = self._get_session()

            # Pagination loop — sab pages fetch karo
            while link:
                async with session.get(link, headers=self._headers_with_cookie(self.cookie)) as resp:
                    text = await resp.text()
                    if "error" in text:
                        return False
                    try:
                        resp_json = json.loads(text)
                        data = resp_json.get("data", [])
                    except Exception as e:
                        logger.exception("get_page_data json parse error: %s", e)
                        return False

                for get in data:
                    try:
                        id_pro5 = get.get("additional_profile_id", "")
                        if id_pro5:
                            self.pro5.append(id_pro5)
                    except Exception:
                        continue

                # Next page cursor check karo
                paging = resp_json.get("paging", {})
                next_link = paging.get("next", None)
                link = next_link  # None ho to loop band

            if not self.pro5:
                return False
            return True
        except Exception as e:
            logger.exception("get_page_data failed: %s", e)
            return False

    def type_cx(self, type):
        return {
            "1": "1635855486666999",
            "2": "1678524932434102",
            "3": "613557422527858",
            "4": "478547315650144",
            "5": "115940658764963",
            "6": "908563459236466",
            "7": "444813342392137",
        }.get(type, "1635855486666999")

    async def Followpagepro5(self, actor_id):
        global ok, follow_count
        try:
            cookie_to_use = self._get_cookie_for_actor(actor_id)
            headers = self._headers_with_cookie(cookie_to_use)
            headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="8", "Google Chrome";v="116"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.headers.get("user-agent"),
            })
            idfl = getattr(self, "follow_id", "")
            if not idfl:
                print(f"{neon_red}[X] Error: Follow ID nahi mili!{reset}")
                return
            data = {
                "av": actor_id,
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometUserFollowMutation",
                "variables": '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1714345231318,641563,250100865708545,,","is_tracking_encrypted":false,"subscribe_location":"PROFILE","subscribee_id":"' + idfl + '","tracking":null,"actor_id":"' + actor_id + '","client_mutation_id":"1"},"scale":1}',
                "server_timestamps": "true",
                "doc_id": "7393793397375006",
            }
            resp_text = ""
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                    resp_text = await resp.text()
            except Exception as e:
                logger.exception("Followpagepro5 post error: %s", e)
                colored_id = "".join(colors[(i + follow_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;196m[\033[38;5;220m--\033[38;5;196m] \033[1m\033[38;5;196mFOLLOW \033[38;5;220mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id} \033[38;5;220m| ERR: {type(e).__name__}: {e}{reset}")
                return

            colored_id = "".join(colors[(i + follow_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            try:
                resp_json = json.loads(resp_text.replace("for (;;);", "").strip())
            except Exception:
                resp_json = {}

            errors = resp_json.get("errors", [])
            err_msg = str(errors[0].get("message", "")).lower() if isinstance(errors, list) and errors else ""
            err_code = str(errors[0].get("code", "")) if isinstance(errors, list) and errors else ""
            err_display = str(errors[0].get("summary", errors[0].get("message", "")))[:28] if isinstance(errors, list) and errors else ""

            # Success - subscribe_status in data
            follow_data = resp_json.get("data", {})
            follow_val = follow_data.get("subscribe", follow_data.get("user_follow", "NOT_PRESENT"))
            if follow_val is not None and follow_val != "NOT_PRESENT":
                with COUNTER_LOCK:
                    follow_count += 1
                    ok += 1
                colored_id2 = "".join(colors[(i + follow_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;220m[\033[38;5;178m++\033[38;5;220m] \033[1m\033[38;5;178mFOLLOW \033[38;5;214mSUCCESS\033[0m \033[38;5;220m==> \033[38;5;255mActor: {colored_id2} \033[38;5;220m[\033[38;5;178m{follow_count}\033[38;5;220m]{reset}")
                return

            if err_code == "1390008" or "limit how often" in err_msg or "too many" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;220m--\033[38;5;196m] \033[1m\033[38;5;196mFOLLOW \033[38;5;220mRATE LIMIT\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "account has been disabled" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;220m--\033[38;5;196m] \033[1m\033[38;5;196mFOLLOW \033[38;5;220mACCOUNT SUSPENDED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if err_code == "1357004" or "action blocked" in err_msg or "checkpoint" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;220m--\033[38;5;196m] \033[1m\033[38;5;196mFOLLOW \033[38;5;220mBLOCKED THIS ID\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if errors:
                print(f"\033[38;5;196m[\033[38;5;220m--\033[38;5;196m] \033[1m\033[38;5;196mFOLLOW \033[38;5;220mERROR: {err_display}\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return

            # No errors = success
            with COUNTER_LOCK:
                follow_count += 1
                ok += 1
            colored_id2 = "".join(colors[(i + follow_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            print(f"\033[38;5;220m[\033[38;5;178m++\033[38;5;220m] \033[1m\033[38;5;178mFOLLOW \033[38;5;214mSUCCESS\033[0m \033[38;5;220m==> \033[38;5;255mActor: {colored_id2} \033[38;5;220m[\033[38;5;178m{follow_count}\033[38;5;220m]{reset}")
        except Exception as e:
            logger.exception("Followpagepro5 error: %s", e)

    async def PageLikepro5(self, actor_id):
        global ok, page_like_count
        try:
            cookie_to_use = self._get_cookie_for_actor(actor_id)
            headers = self._headers_with_cookie(cookie_to_use)
            headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-ua": "",
                "sec-ch-ua-full-version-list": "",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"\"",
                "sec-ch-ua-platform-version": "\"\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.133 Safari/537.36",
            })
            page_id = getattr(self, "follow_id", "")
            if not page_id:
                print(f"{neon_red}[X] Error: Page ID nahi mili!{reset}")
                return
            data = {
                "av": actor_id,
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometPageLikeMutation",
                "variables": '{"input":{"attribution_id_v2":"PageCometHeaderRoot.react,comet.page.about,via_cold_start,1714345231318,641563,250100865708545,,","page_id":"' + page_id + '","actor_id":"' + actor_id + '","client_mutation_id":"1"},"scale":1}',
                "server_timestamps": "true",
                "doc_id": "4897940670225889",
            }
            resp_text = ""
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                    resp_text = await resp.text()
            except Exception as e:
                logger.exception("PageLikepro5 post error: %s", e)
                colored_id = "".join(colors[(i + page_like_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;196m[\033[38;5;213m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE LIKE \033[38;5;213mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id} \033[38;5;213m| ERR: {type(e).__name__}: {e}{reset}")
                return

            colored_id = "".join(colors[(i + page_like_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            try:
                resp_json = json.loads(resp_text.replace("for (;;);", "").strip())
            except Exception:
                resp_json = {}

            errors = resp_json.get("errors", [])
            err_msg = str(errors[0].get("message", "")).lower() if isinstance(errors, list) and errors else ""
            err_display = str(errors[0].get("summary", errors[0].get("message", "")))[:28] if isinstance(errors, list) and errors else ""

            like_data = resp_json.get("data", {})
            like_val = like_data.get("page_like", like_data.get("fan", "NOT_PRESENT"))
            if like_val is not None and like_val != "NOT_PRESENT":
                with COUNTER_LOCK:
                    page_like_count += 1
                    ok += 1
                colored_id2 = "".join(colors[(i + page_like_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;213m[\033[38;5;207m++\033[38;5;213m] \033[1m\033[38;5;207mPAGE LIKE \033[38;5;165mSUCCESS\033[0m \033[38;5;213m==> \033[38;5;255mActor: {colored_id2} \033[38;5;213m[\033[38;5;207m{page_like_count}\033[38;5;213m]{reset}")
                return

            if "rate limit" in err_msg or "too many" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;213m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE LIKE \033[38;5;213mRATE LIMIT\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "account has been disabled" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;213m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE LIKE \033[38;5;213mACCOUNT SUSPENDED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "action blocked" in err_msg or "checkpoint" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;213m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE LIKE \033[38;5;213mBLOCKED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if errors:
                print(f"\033[38;5;196m[\033[38;5;213m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE LIKE \033[38;5;213mERROR: {err_display}\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return

            # No errors = success
            with COUNTER_LOCK:
                page_like_count += 1
                ok += 1
            colored_id2 = "".join(colors[(i + page_like_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            print(f"\033[38;5;213m[\033[38;5;207m++\033[38;5;213m] \033[1m\033[38;5;207mPAGE LIKE \033[38;5;165mSUCCESS\033[0m \033[38;5;213m==> \033[38;5;255mActor: {colored_id2} \033[38;5;213m[\033[38;5;207m{page_like_count}\033[38;5;213m]{reset}")
        except Exception as e:
            logger.exception("PageLikepro5 error: %s", e)

    async def mainFollow(self):
        sub_mode = getattr(self, "follow_sub_mode", "1")  # 1=Follow, 2=Like, 3=Both
        actors = []
        if self.account_type in ("1", "3"):
            actors.append(self.uid)
        if self.account_type in ("2", "3"):
            for idpro5 in self.pro5:
                actors.append(idpro5)

        async def _run_actor(actor, offset):
            if offset > 0:
                await asyncio.sleep(offset)
            if sub_mode == "1":
                await self.Followpagepro5(actor)
            elif sub_mode == "2":
                await self.PageLikepro5(actor)
            elif sub_mode == "3":
                await self.Followpagepro5(actor)
                await self.PageLikepro5(actor)

        d = getattr(self, "delay", 0)
        tasks = [_run_actor(actor, i * d) for i, actor in enumerate(actors)]
        await asyncio.gather(*tasks)

    async def joingrpro5(self, actor_id):
        global ok, join_count
        try:
            cookie_to_use = self._get_cookie_for_actor(actor_id)
            headers = self._headers_with_cookie(cookie_to_use)
            headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="8", "Google Chrome";v="116"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.headers.get("user-agent"),
            })
            idgr = getattr(self, "group_id", "")
            if not idgr:
                print(f"{neon_red}[X] Error: Group ID nahi mili!{reset}")
                return
            data = {
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "GroupCometJoinForumMutation",
                "variables": '{"feedType":"DISCUSSION","groupID":"' + idgr + '","imageMediaType":"image/x-auto","input":{"action_source":"GROUPS_ENGAGE_TAB","attribution_id_v2":"GroupsCometCrossGroupFeedRoot.react,comet.groups.feed,tap_tabbar,1667116100089,433821,2361831622,","group_id":"' + idgr + '","group_share_tracking_params":null,"actor_id":"' + actor_id + '","client_mutation_id":"2"},"inviteShortLinkKey":null,"isChainingRecommendationUnit":false,"isEntityMenu":false,"scale":1,"source":"GROUPS_ENGAGE_TAB","__relay_internal__pv__GlobalPanelEnabledrelayprovider":false,"__relay_internal__pv__GroupsCometEntityMenuEmbeddedrelayprovider":true}',
                "server_timestamps": "true",
                "doc_id": "5915153095183264",
            }
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                        await resp.text()
            except Exception as e:
                logger.exception("joingrpro5 post error: %s", e)
            with COUNTER_LOCK:
                join_count += 1
                ok += 1
            colored_id = "".join(colors[(i + join_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            print(f"\033[38;5;208m[\033[38;5;166m++\033[38;5;208m] \033[1m\033[38;5;166mJOIN \033[38;5;202mSUCCESS\033[0m \033[38;5;208m==> \033[38;5;255mActor: {colored_id} \033[38;5;208m[\033[38;5;202m{join_count}\033[38;5;208m]{reset}")
        except Exception as e:
            logger.exception("joingrpro5 error: %s", e)

    async def reaction(self, reaction, actor_id):
        global ok, reaction_count
        try:
            cookie_to_use = self._get_cookie_for_actor(actor_id)
            headers = self._headers_with_cookie(cookie_to_use)
            headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="8", "Google Chrome";v="116"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.headers.get("user-agent"),
            })
            data = {
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometUFIFeedbackReactMutation",
                "variables": '{"input":{"attribution_id_v2":"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1667106623951,429237,190055527696468,","feedback_id":"' + self.idbv + '","feedback_reaction_id":"' + reaction + '","feedback_source":"PROFILE","is_tracking_encrypted":true,"session_id":"' + str(uuid.uuid4()) + '","actor_id":"' + actor_id + '","client_mutation_id":"1"},"useDefaultActor":false,"scale":1}',
                "server_timestamps": "true",
                "doc_id": "5703418209680126",
            }
            resp_text = ""
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                    resp_text = await resp.text()
            except Exception as e:
                colored_id = "".join(colors[(i + reaction_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;196m[\033[38;5;201m--\033[38;5;196m] \033[1m\033[38;5;196mREACTION \033[38;5;201mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id} \033[38;5;201m| ERR: {type(e).__name__}: {e}{reset}")
                return

            colored_id = "".join(colors[(i + reaction_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            try:
                resp_json = json.loads(resp_text.replace("for (;;);", "").strip())
            except Exception:
                resp_json = {}

            errors = resp_json.get("errors", [])
            err_msg = str(errors[0].get("message", "")).lower() if isinstance(errors, list) and errors else ""
            err_code = str(errors[0].get("code", "")) if isinstance(errors, list) and errors else ""
            err_display = str(errors[0].get("summary", errors[0].get("message", "")))[:28] if isinstance(errors, list) and errors else ""

            # Success check - feedback_react in data
            react_val = resp_json.get("data", {}).get("feedback_react", "NOT_PRESENT")
            if react_val is not None and react_val != "NOT_PRESENT":
                with COUNTER_LOCK:
                    reaction_count += 1
                    ok += 1
                colored_id2 = "".join(colors[(i + reaction_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;201m[\033[38;5;129m++\033[38;5;201m] \033[1m\033[38;5;93mREACTION \033[38;5;57mSUCCESS\033[0m \033[38;5;201m==> \033[38;5;255mActor: {colored_id2} \033[38;5;201m[\033[38;5;129m{reaction_count}\033[38;5;201m]{reset}")
                return

            if err_code == "1390008" or "limit how often" in err_msg or "too many" in err_msg or "you can\'t use this feature" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;201m--\033[38;5;196m] \033[1m\033[38;5;196mREACTION \033[38;5;201mRATE LIMIT\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "account has been disabled" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;201m--\033[38;5;196m] \033[1m\033[38;5;196mREACTION \033[38;5;201mACCOUNT SUSPENDED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if err_code == "1357004" or "action blocked" in err_msg or "checkpoint" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;201m--\033[38;5;196m] \033[1m\033[38;5;196mREACTION \033[38;5;201mBLOCKED THIS ID\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if errors:
                print(f"\033[38;5;196m[\033[38;5;201m--\033[38;5;196m] \033[1m\033[38;5;196mREACTION \033[38;5;201mERROR: {err_display}\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return

            # No errors = success
            with COUNTER_LOCK:
                reaction_count += 1
                ok += 1
            colored_id2 = "".join(colors[(i + reaction_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            print(f"\033[38;5;201m[\033[38;5;129m++\033[38;5;201m] \033[1m\033[38;5;93mREACTION \033[38;5;57mSUCCESS\033[0m \033[38;5;201m==> \033[38;5;255mActor: {colored_id2} \033[38;5;201m[\033[38;5;129m{reaction_count}\033[38;5;201m]{reset}")
        except Exception as e:
            print(f"\033[38;5;196m[DEBUG][REACTION] Actor={actor_id} | ERR={type(e).__name__}: {e}{reset}")
            import traceback; traceback.print_exc()


    def reaction_smooth(self, reaction_id, idpro5):
        """Smooth Mode — AxM sync approach: requests library, threading, AxM headers/cookie pattern"""
        global ok, reaction_count
        try:
            # FIX: Agar idpro5 main profile (self.uid) hai to i_user ADD NAHI karna —
            # warna Facebook ko lagta hai tum page ki tarah act kar rahe ho (chahe
            # wahi UID ho), aur like us "identity" ke page se chala jata hai ya silently
            # fail ho jata hai. Sirf actual pages ke liye i_user add karo.
            if idpro5 != getattr(self, "uid", idpro5):
                if self.cookie and self.cookie[-1] == ';':
                    cookie = self.cookie + 'i_user=' + idpro5 + ';'
                else:
                    cookie = self.cookie + ';i_user=' + idpro5 + ';'
            else:
                cookie = self.cookie

            headers = {
                'authority': 'www.facebook.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'cookie': cookie,
                'referer': 'https://www.facebook.com/settings?tab=profile_access',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua': '',
                'sec-ch-ua-full-version-list': '',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"\"',
                'sec-ch-ua-platform-version': '\"\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.133 Safari/537.36',
            }
            data = {
                'fb_dtsg': self.fb_dtsg or '',
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
                'variables': '{\"input\":{\"attribution_id_v2\":\"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,1667106623951,429237,190055527696468,\",\"feedback_id\":\"' + self.idbv + '\",\"feedback_reaction_id\":\"' + reaction_id + '\",\"feedback_source\":\"PROFILE\",\"is_tracking_encrypted\":true,\"tracking\":[\"AZXg8_yM_zhwrTY7oSTw1K93G-sycXrSreRnRk66aBJ9mWkbSuyIgNqL0zHEY_XgxepV1XWYkuv2C5PuM14WXUB9NGsSO8pPe8qDZbqCw5FLQlsGTnh5w9IyC_JmDiRKOVh4gWEJKaTdTOYlGT7k5vUcSrvUk7lJ-DXs3YZsw994NV2tRrv_zq1SuYfVKqDboaAFSD0a9FKPiFbJLSfhJbi6ti2CaCYLBWc_UgRsK1iRcLTZQhV3QLYfYOLxcKw4s2b1GeSr-JWpxu1acVX_G8d_lGbvkYimd3_kdh1waZzVW333356_JAEiUMU_nmg7gd7RxDv72EkiAxPM6BA-ClqDcJ_krJ_Cg-qdhGiPa_oFTkGMzSh8VnMaeMPmLh6lULnJwvpJL_4E3PBTHk3tIcMXbSPo05m4q_Xn9ijOuB5-KB5_9ftPLc3RS3C24_7Z2bg4DfhaM4fHYC1sg3oFFsRfPVf-0k27EDJM0HZ5tszMHQ\"],\"session_id\":\"' + str(uuid.uuid4()) + '\",\"actor_id\":\"' + idpro5 + '\",\"client_mutation_id\":\"1\"},\"useDefaultActor\":false,\"scale\":1}',
                'server_timestamps': 'true',
                'doc_id': '5703418209680126',
            }
            import requests as _req
            resp = _req.post('https://www.facebook.com/api/graphql/', headers=headers, data=data)
            resp_text = resp.text
            colored_id = "".join(colors[(i + reaction_count) % len(colors)] + ch + reset for i, ch in enumerate(str(idpro5)))
            # Real response check
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = {}
            react_val = resp_json.get("data", {}).get("feedback_react", "NOT_PRESENT")
            err_list = resp_json.get("errors", [])
            err_msg = str(resp_json).lower()
            if err_list or react_val == "NOT_PRESENT" or "error" in err_msg:
                if "rate limit" in err_msg or "spam" in err_msg:
                    print(f"\033[38;5;203m[\033[38;5;161m--\033[38;5;203m] \033[38;5;203mSMOOTH RATE LIMIT \033[38;5;255mActor: {colored_id}{reset}")
                elif "account disabled" in err_msg or "disabled" in err_msg:
                    print(f"\033[38;5;203m[\033[38;5;161m--\033[38;5;203m] \033[38;5;203mACCOUNT DISABLED \033[38;5;255mActor: {colored_id}{reset}")
                elif "action blocked" in err_msg:
                    print(f"\033[38;5;203m[\033[38;5;161m--\033[38;5;203m] \033[38;5;203mACTION BLOCKED \033[38;5;255mActor: {colored_id}{reset}")
                else:
                    print(f"\033[38;5;203m[\033[38;5;161m--\033[38;5;203m] \033[38;5;203mSMOOTH FAIL \033[38;5;255mActor: {colored_id}{reset}")
            else:
                with COUNTER_LOCK:
                    reaction_count += 1
                    ok += 1
                print(f"\033[38;5;201m[\033[38;5;129m++\033[38;5;201m] \033[1m\033[38;5;93mREACTION \033[38;5;57mSUCCESS\033[0m \033[38;5;201m==> \033[38;5;255mActor: {colored_id} \033[38;5;201m[\033[38;5;129m{reaction_count}\033[38;5;201m]{reset}")
        except Exception as e:
            print(f"\033[38;5;196m[DEBUG][REACTION-SMOOTH] Actor={idpro5} | ERR={type(e).__name__}: {e}{reset}")
            import traceback; traceback.print_exc()

    # ── PAGE CREATE — BILKUL TOUCH NAHI ── (sync, requests library)
    def page_create(self):
        import requests as _req
        global ok, page_create_count
        try:
            # Session with cookies properly injected - same as original
            _session = _req.Session()
            _adapter = HTTPAdapter(pool_connections=30, pool_maxsize=50, max_retries=1)
            _session.mount("https://", _adapter)
            _session.mount("http://", _adapter)
            # Cookie inject karo - datapoll ke liye zaroori
            try:
                parsed = parse_cookie_string(self.cookie)
                if parsed:
                    _session.cookies.update(parsed)
            except Exception:
                pass

            _pc_headers = self._headers_with_cookie(self.cookie)
            _pc_headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            req = _session.get("https://web.facebook.com/?_rdc=1&_rdr", headers=_pc_headers, timeout=(10, 20)).text
            data = self.datapoll(req, self.uid)
            if data is None:
                req = _session.get("https://web.facebook.com/?_rdc=1&_rdr", headers=self._headers_with_cookie(self.cookie), timeout=(10, 20)).text
                data = self.datapoll(req, self.uid)
            if data is None:
                print(f"{neon_red}[X] Failed to extract data for page creation{reset}")
                return
            page_name = self.page_name + str(random.randrange(1111111, 9999999))
            var = {
                "input": {
                    "bio": "",
                    "categories": ["181475575221097"],
                    "creation_source": "comet",
                    "name": page_name,
                    "page_referrer": "launch_point",
                    "actor_id": self.uid,
                    "client_mutation_id": "1",
                }
            }
            data.update({
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "AdditionalProfilePlusCreationMutation",
                "variables": json.dumps(var),
                "server_timestamps": True,
                "doc_id": "5296879960418435",
            })
            headers = self._headers_with_cookie(self.cookie)
            headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://www.facebook.com",
                "referer": "https://www.facebook.com/",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.headers.get("user-agent"),
                "x-fb-friendly-name": "AdditionalProfilePlusCreationMutation",
                "x-fb-lsd": data.get("lsd", ""),
            })
            try:
                pos = _session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, timeout=40).text.replace("for (;;);", "")
                poss = json.loads(pos)
                page_id = poss["data"]["additional_profile_plus_create"]["additional_profile"]["id"]
                with COUNTER_LOCK:
                    page_create_count += 1
                    ok += 1
                colored_id = "".join(colors[(i + page_create_count) % len(colors)] + ch + reset for i, ch in enumerate(str(self.uid)))
                print(f"\033[38;5;118m[\033[38;5;76m++\033[38;5;118m] \033[1m\033[38;5;76mPAGE CREATE \033[38;5;82mSUCCESS\033[0m \033[38;5;118m==> \033[38;5;255mUID: {colored_id} \033[38;5;40m| PAGE: {page_id} \033[38;5;118m[\033[38;5;76m{page_create_count}\033[38;5;118m]{reset}")
            except Exception as e:
                logger.exception("page_create post/json error: %s", e)
                with COUNTER_LOCK:
                    page_create_count += 1
                    ok += 1
                colored_id = "".join(colors[(i + page_create_count) % len(colors)] + ch + reset for i, ch in enumerate(str(self.uid)))
                print(f"\033[38;5;196m[\033[38;5;118m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE CREATE \033[38;5;118mFAILED (ID ISSUE)\033[0m \033[38;5;255m| UID: {colored_id}{reset}")
        except Exception as e:
            logger.exception("page_create error: %s", e)
            colored_id = "".join(colors[0] + ch + reset for ch in str(getattr(self, "uid", "Unknown")))
            print(f"\033[38;5;196m[\033[38;5;118m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE CREATE \033[38;5;118mFAILED\033[0m \033[38;5;255m| UID: {colored_id}{reset}")

    async def page_activate(self):
        global ok, page_activate_count
        try:
            params = {"category": "your_pages", "ref": "bookmarks"}
            _pa_headers = self._headers_with_cookie(self.cookie)
            _pa_headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

            session = self._get_session()
            async with session.get("https://www.facebook.com/pages/", params=params, headers=_pa_headers) as resp:
                gat_text = await resp.text()

            fg = re.findall(r'"uri_token":"(\d+)"', gat_text)
            data = self.datapoll(gat_text, self.uid)
            if data is None:
                print(f"{neon_red}[X] Failed to extract data for page activation{reset}")
                return

            tasks = []
            for pid in fg:
                var = {"profile_id": pid, "delegate_page_id": None}
                d = data.copy()
                d.update({
                    "fb_api_caller_class": "RelayModern",
                    "fb_api_req_friendly_name": "ReactivateProfileMutation",
                    "variables": json.dumps(var),
                    "server_timestamps": "true",
                    "doc_id": "6365256943526229",
                })
                tasks.append(self._activate_single(pid, d))

            await asyncio.gather(*tasks)

        except Exception as e:
            logger.exception("page_activate error: %s", e)
            colored_id = "".join(colors[0] + ch + reset for ch in str(getattr(self, "uid", "Unknown")))
            print(f"\033[38;5;196m[\033[38;5;75m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE ACTIVATE \033[38;5;75mERROR\033[0m \033[38;5;255m| UID: {colored_id}{reset}")

    async def _activate_single(self, pid, data):
        global ok, page_activate_count
        try:
            headers = self._headers_with_cookie(self.cookie)
            headers.update({"x-fb-friendly-name": "ReactivateProfileMutation", "x-fb-lsd": data.get("lsd", "")})
            session = self._get_session()
            async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                await resp.text()
        except Exception:
            pass
        with COUNTER_LOCK:
            page_activate_count += 1
            ok += 1
        colored_id = "".join(colors[(i + page_activate_count) % len(colors)] + ch + reset for i, ch in enumerate(str(getattr(self, "uid", "Unknown"))))
        print(f"\033[38;5;75m[\033[38;5;33m++\033[38;5;75m] \033[1m\033[38;5;33mPAGE ACTIVATE \033[38;5;81mSUCCESS\033[0m \033[38;5;75m==> \033[38;5;255mUID: {colored_id} \033[38;5;69m| PAGE: {pid} \033[38;5;75m[\033[38;5;33m{page_activate_count}\033[38;5;75m]{reset}")

    async def page_activate_slow(self):
        """Slow Method — ek ek page activate karo delay ke saath"""
        global ok, page_activate_count
        try:
            params = {"category": "your_pages", "ref": "bookmarks"}
            _pa_headers = self._headers_with_cookie(self.cookie)
            _pa_headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"

            session = self._get_session()
            async with session.get("https://www.facebook.com/pages/", params=params, headers=_pa_headers) as resp:
                gat_text = await resp.text()

            fg = re.findall(r'"uri_token":"(\d+)"', gat_text)
            data = self.datapoll(gat_text, self.uid)
            if data is None:
                print(f"{neon_red}[X] Failed to extract data for page activation{reset}")
                return

            for pid in fg:
                var = {"profile_id": pid, "delegate_page_id": None}
                d = data.copy()
                d.update({
                    "fb_api_caller_class": "RelayModern",
                    "fb_api_req_friendly_name": "ReactivateProfileMutation",
                    "variables": json.dumps(var),
                    "server_timestamps": "true",
                    "doc_id": "6365256943526229",
                })
                await self._activate_single(pid, d)
                # Delay between each page activate
                if self.delay and self.delay > 0:
                    await asyncio.sleep(self.delay)

        except Exception as e:
            logger.exception("page_activate_slow error: %s", e)
            colored_id = "".join(colors[0] + ch + reset for ch in str(getattr(self, "uid", "Unknown")))
            print(f"\033[38;5;196m[\033[38;5;75m--\033[38;5;196m] \033[1m\033[38;5;196mPAGE ACTIVATE \033[38;5;75mERROR\033[0m \033[38;5;255m| UID: {colored_id}{reset}")

    async def poll_vote(self, uid):
        global ok, poll_vote_count
        try:
            acct_type = getattr(self, "account_type", "2")
            question_id, option_id = self.poll_data.split("|")

            # ── FIX: "3" (Both) mode mein khud ka ID bhi aata hai jo
            # self.uid jaisa hota hai — usay Page na samjho, direct bhejo ──
            is_own_id_actor = (acct_type == "1") or (str(uid) == str(getattr(self, "uid", "")))

            if is_own_id_actor:
                cookie_to_use = self.cookie or ""
                headers = self._headers_with_cookie(cookie_to_use)
                av_id = getattr(self, "uid", uid) or uid
            else:
                base_cookies = parse_cookie_string(self.cookie or "")
                if base_cookies is None:
                    base_cookies = {}
                base_cookies["i_user"] = uid
                cookie_to_use = "; ".join([f"{k}={v}" for k, v in base_cookies.items()])
                headers = self._headers_with_cookie(cookie_to_use)
                av_id = uid

            headers.update({
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access"
            })

            data = {
                "av": av_id,
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useCometPollAddVoteMutation",
                "variables": '{"input":{"is_tracking_encrypted":true,"option_id":"' + option_id + '","question_id":"' + question_id + '","actor_id":"' + av_id + '","client_mutation_id":"1"},"scale":1,"__relay_internal__pv__IsWorkUserrelayprovider":false}',
                "server_timestamps": "true",
                "doc_id": "6681967255191860",
            }
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                        post = await resp.json(content_type=None)
            except Exception:
                colored_id = "".join(colors[(i + poll_vote_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mPOLL VOTE \033[38;5;51mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return

            if isinstance(post, dict) and "errors" in post:
                return

            try:
                options_nodes = post["data"]["question_add_vote"]["question"]["options"]["nodes"]
                for get in options_nodes:
                    if option_id in str(get):
                        count_v = get["profile_voters"].get("count", 0)
                        with COUNTER_LOCK:
                            poll_vote_count += 1
                            ok += 1
                        colored_id = "".join(colors[(i + poll_vote_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                        print(f"\033[38;5;156m[\033[38;5;120m++\033[38;5;156m] \033[1m\033[38;5;120mPOLL VOTE \033[38;5;114mSUCCESS\033[0m \033[38;5;156m==> \033[38;5;255mActor: {colored_id} \033[38;5;150m| Total: {count_v} \033[38;5;156m[\033[38;5;120m{poll_vote_count}\033[38;5;156m]{reset}")
                        break
            except Exception:
                pass
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    # FAST MODE — Old Alisha async cmt() + maincmt()
    # ═══════════════════════════════════════════════════════

    async def cmt(self, actor_id):
        global ok, comment_count
        try:
            if not getattr(self, "uid", None):
                self.getuid()
            cookie_to_use = self._get_cookie_for_actor(actor_id)
            headers = self._headers_with_cookie(cookie_to_use)
            headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="8", "Google Chrome";v="116"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.headers.get("user-agent"),
            })
            inline_comments = getattr(self, "inline_comments", [])
            if not inline_comments:
                print(f"{neon_red}[X] Error: Koi comment nahi mila!{reset}")
                return

            base_comment = random.choice(inline_comments)
            noidung = (base_comment + " " + random.choice(EMOJIS)) if getattr(self, "use_emoji", True) and random.random() < 0.7 else base_comment

            _uid1 = str(uuid.uuid4())
            _uid2 = str(uuid.uuid4())
            _uid3 = str(uuid.uuid4())
            # Group post vs open post ke liye alag values
            _is_group_fast = getattr(self, 'cmt_mode_selc', 'timeline') == 'group' or getattr(self, 'slow_selc', 'timeline') == 'group'
            _feed_loc_fast = "GROUP" if _is_group_fast else "PERMALINK"
            _cmt_key_fast  = "CometGroupUFIRootQuery" if _is_group_fast else "CometSinglePostRoute"
            _attr_fast     = (
                "GroupsCometFeedUFIRootQuery.react,comet.groups.feed,via_cold_start,1692175639975,676866,,"
                if _is_group_fast else
                "CometSinglePostRoot.react,comet.post.single,via_cold_start,1692175639975,676866,,"
            )
            variables = json.dumps({
                "displayCommentsFeedbackContext": None,
                "displayCommentsContextEnableComment": None,
                "displayCommentsContextIsAdPreview": None,
                "displayCommentsContextIsAggregatedShare": None,
                "displayCommentsContextIsStorySet": None,
                "feedLocation": _feed_loc_fast,
                "feedbackSource": 2,
                "focusCommentID": None,
                "groupID": None,
                "includeNestedComments": False,
                "input": {
                    "attachments": None,
                    "feedback_id": self.idbv,
                    "formatting_style": None,
                    "message": {"ranges": [], "text": noidung},
                    "attribution_id_v2": _attr_fast,
                    "is_tracking_encrypted": True,
                    "tracking": [
                        "AZVuNDRPni4Q9--BKAtfuWNHMy_89-NxE3pTjMT9_lOt3iM-qSkUzLEZ_FeFl_sq_zGZXfu1Fu2tgEDHR74HuGk2k2JwNfQuV71T2tiowryfVZovjCFl_Bo6_xr4CpG2rlkfQoGvpNv3AvFpm1eCLJZghuF4Wy5Kj7hc57RT6pX0l7OIcseByxSD8bm81CPU3-sIw9a3vx_cYDJKn2GxVBrkGeK_FUpFuxdMdQHzVQ7j44_D858NuZ_ulXBRLfPJCg5tHChFqmeHOAXCCV1GDRhtdeuoa-yyDtVGZwY7EY8F51nC8PBCYrATMpXr2W0w6PrWCyQFXSDrZWyUDrMq6QjnjQX3DifScfOmUKXYFWlbaetXELak_wuDysgcTT68SyCpUPqhQ-Vhp9LHPu8f7GjotHG4bXKoV0SI1azRwmspmG5KCqz1eXDLZFDYiUQjZHuncSXsV3xl--AHwvNggXxeoxe9PVYhHkDtf8I-h4_T5xj-PnHPrlf0lqo2kmojPGkNPriIOPDCbaOcyeXn2DRarKaR1sC_5YI31m3cyohfef_ZhBmnU4w9DUhxcHxQN3mqp_an5A3H2x4Z_RQ3ymOIADDRA4hO5AGFrlPFxutuNoimAGUEZjUr0S8TScHcUD4FfooX0WPC5sfAco8nhlfiimEFL7oe0LwgK3e4bLOVVW-gIpjHP9z2A7S9Sd87jaeqXYYr8NoJETpAn1YFxDSbtrkF3_jnlvgMKfe01ODdiBbc3sIDmh72H-152z_qS3Y_ihz4983UXURphxRcEGX3M0aHB3Uhi7SvKMnXKUbA9P2ErZJ9ify8qujIsigmhK6j5fXBT1vu5ZS4EDCeUty1ogYFfCuY4dBvcuhx6N7FkXsJQ08etPNz-3WvylFOAyP5b2HAcXpgmV-F-3ShhkTNPhaMW2ny6FlndR1aniY--Tbhib3l7dvOcs_rj-A-OrV6v4vRKBSlwF2l6h8J2sysriPzUJgSMLVlCfzvzSHfqtK6DzHt2lpHUtlSNtJ6rw_-LJYfJ7JNFDPQT00PODuYlKVkkZWJLX_mxkkCKibmzUfl6_hmM6k-w1gTPwR5H7Q",
                        json.dumps({"assistant_caller": "comet_above_composer", "conversation_guide_session_id": _uid1, "conversation_guide_shown": None})
                    ],
                    "feedback_source": "OBJECT",
                    "idempotence_token": f"client:{_uid2}",
                    "session_id": _uid3,
                    "actor_id": actor_id,
                    "client_mutation_id": "4"
                },
                "inviteShortLinkKey": None,
                "renderLocation": None,
                "scale": 1,
                "useDefaultActor": False,
                "UFI2CommentsProvider_commentsKey": _cmt_key_fast
            })

            data = {
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometUFICreateCommentMutation",
                "variables": variables,
                "server_timestamps": "true",
                "doc_id": "6379115828844234",
            }

            resp_text = ""
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data) as resp:
                    resp_text = await resp.text()
            except Exception as e:
                colored_id = "".join(colors[(i + comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return

            colored_id = "".join(colors[(i + comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
            try:
                resp_json = json.loads(resp_text.replace("for (;;);", "").strip())
            except Exception as _pe:
                resp_json = {}

            errors = resp_json.get("errors", [])
            err_msg = str(errors[0].get("message", "")).lower() if isinstance(errors, list) and errors else ""
            err_code = str(errors[0].get("code", "")) if isinstance(errors, list) and errors else ""
            api_error_code = str(errors[0].get("api_error_code", "")) if isinstance(errors, list) and errors else ""
            err_display = str(errors[0].get("summary", errors[0].get("message", "")))[:28] if isinstance(errors, list) and errors else ""

            comment_create_val = resp_json.get("data", {}).get("comment_create", "NOT_PRESENT")
            if comment_create_val is not None and comment_create_val != "NOT_PRESENT":
                with COUNTER_LOCK:
                    comment_count += 1
                    ok += 1
                colored_id2 = "".join(colors[(i + comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(actor_id)))
                print(f"\033[38;5;51m[\033[38;5;87m++\033[38;5;51m] \033[1m\033[38;5;87mCOMMENT \033[38;5;45mSUCCESS\033[0m \033[38;5;51m==> \033[38;5;255mActor: {colored_id2} \033[38;5;51m[\033[38;5;87m{comment_count}\033[38;5;51m]{reset}")
                return

            if err_code == "1390008" or api_error_code == "368" or "rate limit" in err_msg or "too many" in err_msg or "limit how often" in err_msg or "temporarily" in err_msg or "you can't use this feature" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mRATE LIMIT\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if err_code == "1705076" or "commenting has been disabled" in err_msg or "turned off commenting" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mDISABLED ON POST\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "this content is not available" in err_msg or "this post is private" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mPRIVATE POST\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "account has been disabled" in err_msg or "account_disabled" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mACCOUNT SUSPENDED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if err_code == "1357004" or "action blocked" in err_msg or "checkpoint" in err_msg or "verify account" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mBLOCKED THIS ID\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "spam" in err_msg or "community standard" in err_msg or "goes against" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mSPAM DETECTED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if errors:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mERROR: {err_display}\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                print(f"\033[38;5;196m[DEBUG][CMT] feedback_id used={self.idbv} | full_resp={resp_text[:300]}{reset}")
                return
            print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mNO RESPONSE\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
            print(f"\033[38;5;196m[DEBUG][CMT] feedback_id used={self.idbv} | full_resp={resp_text[:300]}{reset}")
        except Exception as e:
            print(f"\033[38;5;196m[DEBUG][CMT] Actor={actor_id} | ERR={type(e).__name__}: {e}{reset}")
            import traceback; traceback.print_exc()

    async def maincmt(self):
        """Fast Mode — old Alisha async cmt() logic"""
        count_per_unit = getattr(self, "count_per_unit", 1)
        if not getattr(self, "uid", None):
            self.getuid()
        actors = []
        if self.account_type in ("1", "3"):
            actors.append(self.uid)
        if self.account_type in ("2", "3"):
            for idpro5 in self.pro5:
                actors.append(idpro5)

        async def _cmt_with_offset(actor, offset):
            if offset > 0:
                await asyncio.sleep(offset)
            await self.cmt(actor)

        d = getattr(self, "delay", 0)
        all_tasks = []
        idx = 0
        for actor in actors:
            for _ in range(count_per_unit):
                all_tasks.append(_cmt_with_offset(actor, idx * d))
                idx += 1
        await asyncio.gather(*all_tasks)

    # ── Async parallel wrappers ──

    def maincamxuc_smooth(self):
        # ── SMOOTH MODE: AxM pure sync approach — NO asyncio, seedha threading ──
        actors = []
        if self.account_type in ("1", "3"):
            actors.append((self.type_cx(random.choice(self.camxuc)), self.uid))
        if self.account_type in ("2", "3"):
            for idpro5 in self.pro5:
                actors.append((self.type_cx(random.choice(self.camxuc)), idpro5))

        d = getattr(self, "delay", 0)
        for rxn, actor in actors:
            t = threading.Thread(target=self.reaction_smooth, args=(rxn, actor))
            t.start()
            t.join()
            if d > 0:
                time.sleep(d)

    async def maincamxuc(self):
        # ── FAST MODE: Original AROOJ async approach — 0 change ──
        actors = []
        if self.account_type in ("1", "3"):
            actors.append((self.type_cx(random.choice(self.camxuc)), self.uid))
        if self.account_type in ("2", "3"):
            for idpro5 in self.pro5:
                actors.append((self.type_cx(random.choice(self.camxuc)), idpro5))

        async def _reaction_with_offset(rxn, actor, offset):
            if offset > 0:
                await asyncio.sleep(offset)
            await self.reaction(rxn, actor)

        d = getattr(self, "delay", 0)
        tasks = [_reaction_with_offset(rxn, actor, i * d) for i, (rxn, actor) in enumerate(actors)]
        await asyncio.gather(*tasks)

    async def mainjoin(self):
        actors = []
        if self.account_type in ("1", "3"):
            actors.append(self.uid)
        if self.account_type in ("2", "3"):
            for idpro5 in self.pro5:
                actors.append(idpro5)

        async def _join_with_offset(actor, offset):
            if offset > 0:
                await asyncio.sleep(offset)
            await self.joingrpro5(actor)

        d = getattr(self, "delay", 0)
        tasks = [_join_with_offset(actor, i * d) for i, actor in enumerate(actors)]
        await asyncio.gather(*tasks)

    async def poll_vote_then_comment(self, actor):
        global ok, poll_vote_count, poll_comment_count
        try:
            acct_type = getattr(self, "account_type", "2")
            question_id, option_id = self.poll_data.split("|")

            # ── Cookie setup ──
            if acct_type == "1" or (acct_type == "3" and actor == getattr(self, "uid", None)):
                cookie_to_use = self.cookie or ""
                av_id = getattr(self, "uid", actor) or actor
            else:
                base_cookies = parse_cookie_string(self.cookie or "")
                if base_cookies is None:
                    base_cookies = {}
                base_cookies["i_user"] = actor
                cookie_to_use = "; ".join([f"{k}={v}" for k, v in base_cookies.items()])
                av_id = actor

            headers = self._headers_with_cookie(cookie_to_use)
            headers.update({
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access"
            })

            # ── STEP 1: Poll Vote ──
            poll_data_payload = {
                "av": av_id,
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useCometPollAddVoteMutation",
                "variables": '{\"input\":{\"is_tracking_encrypted\":true,\"option_id\":\"' + option_id + '\",\"question_id\":\"' + question_id + '\",\"actor_id\":\"' + av_id + '\",\"client_mutation_id\":\"1\"},\"scale\":1,\"__relay_internal__pv__IsWorkUserrelayprovider\":false}',
                "server_timestamps": "true",
                "doc_id": "6681967255191860",
            }
            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=headers, data=poll_data_payload) as resp:
                    post = await resp.json(content_type=None)
            except Exception as e:
                colored_id = "".join(colors[(i + poll_vote_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mPOLL \033[38;5;208mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id} \033[38;5;208m| ERR: {type(e).__name__}: {e}{reset}")
                return

            poll_success = False
            if isinstance(post, dict) and "errors" not in post:
                try:
                    options_nodes = post["data"]["question_add_vote"]["question"]["options"]["nodes"]
                    for get in options_nodes:
                        if option_id in str(get):
                            count_v = get["profile_voters"].get("count", 0)
                            with COUNTER_LOCK:
                                poll_vote_count += 1
                                ok += 1
                            colored_id = "".join(colors[(i + poll_vote_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                            print(f"\033[38;5;156m[\033[38;5;120m++\033[38;5;156m] \033[1m\033[38;5;120mPOLL VOTE \033[38;5;114mSUCCESS\033[0m \033[38;5;156m==> \033[38;5;255mActor: {colored_id} \033[38;5;150m| Total: {count_v} \033[38;5;156m[\033[38;5;120m{poll_vote_count}\033[38;5;156m]{reset}")
                            poll_success = True
                            break
                except Exception as e:
                    pass

            if not poll_success:
                colored_id = "".join(colors[(i + poll_vote_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mPOLL VOTE \033[38;5;208mFAILED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")

            # ── STEP 2: Comment (same post) ──
            inline_comments = getattr(self, "inline_comments", [])
            if not inline_comments:
                return

            base_comment = random.choice(inline_comments)
            noidung = (base_comment + " " + random.choice(EMOJIS)) if getattr(self, "use_emoji", True) and random.random() < 0.7 else base_comment

            _uid1 = str(uuid.uuid4())
            _uid2 = str(uuid.uuid4())
            _uid3 = str(uuid.uuid4())
            variables = json.dumps({
                "displayCommentsFeedbackContext": None,
                "displayCommentsContextEnableComment": None,
                "displayCommentsContextIsAdPreview": None,
                "displayCommentsContextIsAggregatedShare": None,
                "displayCommentsContextIsStorySet": None,
                "feedLocation": "PERMALINK",
                "feedbackSource": 2,
                "focusCommentID": None,
                "groupID": None,
                "includeNestedComments": False,
                "input": {
                    "attachments": None,
                    "feedback_id": self.idbv,
                    "formatting_style": None,
                    "message": {"ranges": [], "text": noidung},
                    "attribution_id_v2": "CometSinglePostRoot.react,comet.post.single,via_cold_start,1692175639975,676866,,",
                    "is_tracking_encrypted": True,
                    "tracking": [
                        "AZVuNDRPni4Q9--BKAtfuWNHMy_89-NxE3pTjMT9_lOt3iM-qSkUzLEZ_FeFl_sq_zGZXfu1Fu2tgEDHR74HuGk2k2JwNfQuV71T2tiowryfVZovjCFl_Bo6_xr4CpG2rlkfQoGvpNv3AvFpm1eCLJZghuF4Wy5Kj7hc57RT6pX0l7OIcseByxSD8bm81CPU3-sIw9a3vx_cYDJKn2GxVBrkGeK_FUpFuxdMdQHzVQ7j44_D858NuZ_ulXBRLfPJCg5tHChFqmeHOAXCCV1GDRhtdeuoa-yyDtVGZwY7EY8F51nC8PBCYrATMpXr2W0w6PrWCyQFXSDrZWyUDrMq6QjnjQX3DifScfOmUKXYFWlbaetXELak_wuDysgcTT68SyCpUPqhQ-Vhp9LHPu8f7GjotHG4bXKoV0SI1azRwmspmG5KCqz1eXDLZFDYiUQjZHuncSXsV3xl--AHwvNggXxeoxe9PVYhHkDtf8I-h4_T5xj-PnHPrlf0lqo2kmojPGkNPriIOPDCbaOcyeXn2DRarKaR1sC_5YI31m3cyohfef_ZhBmnU4w9DUhxcHxQN3mqp_an5A3H2x4Z_RQ3ymOIADDRA4hO5AGFrlPFxutuNoimAGUEZjUr0S8TScHcUD4FfooX0WPC5sfAco8nhlfiimEFL7oe0LwgK3e4bLOVVW-gIpjHP9z2A7S9Sd87jaeqXYYr8NoJETpAn1YFxDSbtrkF3_jnlvgMKfe01ODdiBbc3sIDmh72H-152z_qS3Y_ihz4983UXURphxRcEGX3M0aHB3Uhi7SvKMnXKUbA9P2ErZJ9ify8qujIsigmhK6j5fXBT1vu5ZS4EDCeUty1ogYFfCuY4dBvcuhx6N7FkXsJQ08etPNz-3WvylFOAyP5b2HAcXpgmV-F-3ShhkTNPhaMW2ny6FlndR1aniY--Tbhib3l7dvOcs_rj-A-OrV6v4vRKBSlwF2l6h8J2sysriPzUJgSMLVlCfzvzSHfqtK6DzHt2lpHUtlSNtJ6rw_-LJYfJ7JNFDPQT00PODuYlKVkkZWJLX_mxkkCKibmzUfl6_hmM6k-w1gTPwR5H7Q",
                        json.dumps({"assistant_caller": "comet_above_composer", "conversation_guide_session_id": _uid1, "conversation_guide_shown": None})
                    ],
                    "feedback_source": "OBJECT",
                    "idempotence_token": f"client:{_uid2}",
                    "session_id": _uid3,
                    "actor_id": av_id,
                    "client_mutation_id": "4"
                },
                "inviteShortLinkKey": None,
                "renderLocation": None,
                "scale": 1,
                "useDefaultActor": False,
                "UFI2CommentsProvider_commentsKey": "CometSinglePostRoute"
            })

            cmt_headers = self._headers_with_cookie(cookie_to_use)
            cmt_headers.update({
                "authority": "www.facebook.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "referer": "https://www.facebook.com/settings?tab=profile_access",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="8", "Google Chrome";v="116"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": self.headers.get("user-agent"),
            })

            cmt_data = {
                "fb_dtsg": self.fb_dtsg or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometUFICreateCommentMutation",
                "variables": variables,
                "server_timestamps": "true",
                "doc_id": "6379115828844234",
            }

            try:
                session = self._get_session()
                async with session.post("https://www.facebook.com/api/graphql/", headers=cmt_headers, data=cmt_data) as resp:
                    resp_text = await resp.text()
            except Exception as e:
                colored_id = "".join(colors[(i + poll_comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mNETWORK ERROR\033[0m \033[38;5;255m==> Actor: {colored_id} \033[38;5;208m| ERR: {type(e).__name__}: {e}{reset}")
                return

            colored_id = "".join(colors[(i + poll_comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
            try:
                resp_json = json.loads(resp_text.replace("for (;;);", "").strip())
            except Exception:
                resp_json = {}

            errors = resp_json.get("errors", [])
            err_msg = str(errors[0].get("message", "")).lower() if isinstance(errors, list) and errors else ""
            err_code = str(errors[0].get("code", "")) if isinstance(errors, list) and errors else ""
            err_display = str(errors[0].get("summary", errors[0].get("message", "")))[:28] if isinstance(errors, list) and errors else ""

            cmt_node = resp_json.get("data", {}).get("comment_create", {})
            if cmt_node is not None and isinstance(cmt_node, dict) and cmt_node:
                with COUNTER_LOCK:
                    poll_comment_count += 1
                    ok += 1
                colored_id2 = "".join(colors[(i + poll_comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
                print(f"\033[38;5;183m[\033[38;5;141m++\033[38;5;183m] \033[1m\033[38;5;141mCOMMENT \033[38;5;189mSUCCESS\033[0m \033[38;5;183m==> \033[38;5;255mActor: {colored_id2} \033[38;5;183m[\033[38;5;141m{poll_comment_count}\033[38;5;183m]{reset}")
                return

            if err_code == "1390008" or "limit how often" in err_msg or "too many" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mRATE LIMIT\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if "account has been disabled" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;51m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;51mACCOUNT SUSPENDED\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if err_code == "1357004" or "action blocked" in err_msg or "checkpoint" in err_msg:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mBLOCKED THIS ID\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return
            if errors:
                print(f"\033[38;5;196m[\033[38;5;228m--\033[38;5;196m] \033[1m\033[38;5;196mCOMMENT \033[38;5;208mERROR: {err_display}\033[0m \033[38;5;255m==> Actor: {colored_id}{reset}")
                return

            with COUNTER_LOCK:
                poll_comment_count += 1
                ok += 1
            colored_id2 = "".join(colors[(i + poll_comment_count) % len(colors)] + ch + reset for i, ch in enumerate(str(av_id)))
            print(f"\033[38;5;183m[\033[38;5;141m++\033[38;5;183m] \033[1m\033[38;5;141mCOMMENT \033[38;5;189mSUCCESS\033[0m \033[38;5;183m==> \033[38;5;255mActor: {colored_id2} \033[38;5;183m[\033[38;5;141m{poll_comment_count}\033[38;5;183m]{reset}")

        except Exception as e:
            pass

    async def mainPoll(self):
        acct_type = getattr(self, "account_type", None) or "2"
        actors = []
        if acct_type == "1":
            if not getattr(self, "uid", None):
                self.getuid()
            if not getattr(self, "uid", None):
                print(f"{neon_red}[X] Unable to determine UID for ID-based polling. Skipping.{reset}")
                return
            actors.append(self.uid)
        elif acct_type == "2":
            if not self.pro5:
                return
            actors.extend(self.pro5)
        elif acct_type == "3":
            if not getattr(self, "uid", None):
                self.getuid()
            if getattr(self, "uid", None):
                actors.append(self.uid)
            actors.extend(self.pro5)

        async def _poll_with_offset(actor, offset):
            if offset > 0:
                await asyncio.sleep(offset)
            await self.poll_vote(actor)

        d = getattr(self, "delay", 0)
        tasks = [_poll_with_offset(actor, i * d) for i, actor in enumerate(actors)]
        await asyncio.gather(*tasks)

    async def mainPollWithComment(self):
        # ── pfbid fix: poll+comment combo mein bhi real feedback_id use karo ──
        # Pehle yahan direct numeric feedback:{post_id} use ho raha tha, isliye
        # comment post pe nahi, kisi comment ke reply mein chala jata tha.
        # Ab slow/fast comment mode jaisa hi proximity-based real pfbid fetch karte hain.
        _post_link_13 = getattr(self, "post_link_13", "")
        _raw_post_id_13 = getattr(self, "raw_post_id_13", "")
        if _post_link_13 and "facebook.com" in _post_link_13:
            _real_fid_13 = await get_real_feedback_id(_post_link_13, self.cookie or "",
                                                        getattr(self, 'user_agent', None),
                                                        numeric_post_id=_raw_post_id_13)
            if _real_fid_13:
                self.idbv = _real_fid_13

        acct_type = getattr(self, "account_type", None) or "2"
        actors = []
        if acct_type == "1":
            if not getattr(self, "uid", None):
                self.getuid()
            if not getattr(self, "uid", None):
                print(f"{neon_red}[X] Unable to determine UID. Skipping.{reset}")
                return
            actors.append(self.uid)
        elif acct_type == "2":
            if not self.pro5:
                return
            actors.extend(self.pro5)
        elif acct_type == "3":
            if not getattr(self, "uid", None):
                self.getuid()
            if getattr(self, "uid", None):
                actors.append(self.uid)
            actors.extend(self.pro5)

        async def _run_one(actor, offset):
            if offset > 0:
                await asyncio.sleep(offset)
            await self.poll_vote_then_comment(actor)

        d = getattr(self, "delay", 0)
        tasks = [_run_one(actor, i * d) for i, actor in enumerate(actors)]
        await asyncio.gather(*tasks)

    async def main(self):
        global cp
        uid_short = ""
        try:
            uid_short = re.findall(r"c_user=(\d*)", self.cookie)[0] if self.cookie != "no" else "no-cookie"
        except Exception:
            uid_short = "unknown"

        await self._open_session()
        try:
            # Step 1: Login
            login_result = await self.login()
            if login_result["status"] == "Fail":
                with COUNTER_LOCK:
                    cp += 1
                try:
                    account_id = re.findall(r"c_user=(\d*)", self.cookie)[0]
                except Exception:
                    account_id = self.user if self.user != "no" else "Unknown ID"
                colored_id = "".join(colors[(i + cp) % len(colors)] + ch + reset for i, ch in enumerate(str(account_id)))
                print(f"\033[38;5;196m[\033[38;5;243m--\033[38;5;196m] \033[1m\033[38;5;243mCOOKIE \033[38;5;249mEXPIRED\033[0m \033[38;5;255m==> Actor: {colored_id} \033[38;5;196m[\033[38;5;243m{cp}\033[38;5;196m]{reset}")
                return

            # Step 2: fb_dtsg
            if not getattr(self, "fb_dtsg", None):
                get_dtsg_success = await self.get_dtsg()
                if not get_dtsg_success:
                    with COUNTER_LOCK:
                        cp += 1
                    colored_uid = "".join(colors[(i + cp) % len(colors)] + ch + reset for i, ch in enumerate(str(getattr(self, "uid", "Unknown"))))
                    print(f"\033[38;5;196m[\033[38;5;243m--\033[38;5;196m] \033[1m\033[38;5;243mCOOKIE \033[38;5;249mEXPIRED\033[0m \033[38;5;255m==> Actor: {colored_uid} \033[38;5;196m[\033[38;5;243m{cp}\033[38;5;196m]{reset}")
                    return

            # Step 3: Page data
            if getattr(self, "account_type", None) and self.account_type in ("2", "3"):
                get_page_data = await self.get_page_data()
                if not get_page_data and self.account_type == "2":
                    return

            # Step 4: Action
            if self.cv == "1":
                # ── pfbid fix: Like/Reaction mein bhi real feedback_id use karo ──
                # Pehle yahan sirf numeric feedback:{post_id} use ho raha tha, isliye
                # React kisi comment pe chala jata tha, post pe nahi. Ab slow/fast
                # comment mode jaisa hi proximity-based real pfbid fetch karte hain.
                _post_link_cv1 = getattr(self, "_post_link_cv1", "")
                if _post_link_cv1 and "facebook.com" in _post_link_cv1:
                    # idbv abhi tak base64("feedback:<numeric_id>") hai — numeric id nikalo
                    try:
                        _decoded_cv1 = base64.b64decode(self.idbv).decode("utf-8")
                        _numeric_id_cv1 = _decoded_cv1.replace("feedback:", "", 1)
                    except Exception:
                        _numeric_id_cv1 = ""
                    _real_fid_cv1 = await get_real_feedback_id(_post_link_cv1, self.cookie or "",
                                                                 getattr(self, 'user_agent', None),
                                                                 numeric_post_id=_numeric_id_cv1)
                    if _real_fid_cv1:
                        self.idbv = _real_fid_cv1

                _reaction_mode = getattr(self, "reaction_mode", "fast")
                if _reaction_mode == "smooth":
                    self.maincamxuc_smooth()   # pure sync — koi asyncio nahi
                else:
                    await self.maincamxuc()    # original AROOJ async fast mode
            elif self.cv == "2":
                _cmt_data = getattr(self, '_cmt_payload', None)
                if _cmt_data:
                    _cmt_mode  = _cmt_data.get('mode', 'fast')
                    _post_id   = _cmt_data.get('post_id', '')
                    _cpu       = _cmt_data.get('count', 1)
                    _delay     = _cmt_data.get('delay', 0)
                    _cmts      = _cmt_data.get('inline_comments', [])
                    _acct_type = _cmt_data.get('account_type', '1')
                    _use_emoji = _cmt_data.get('use_emoji', True)

                    # ── pfbid fix: post ki page se real feedback_id fetch karo ──
                    _post_link = _cmt_data.get('post_link', '')
                    _real_fid = None
                    if _post_link and 'facebook.com' in _post_link:
                        _real_fid = await get_real_feedback_id(_post_link, self.cookie or "",
                                                                getattr(self, 'user_agent', None),
                                                                numeric_post_id=_post_id)
                    if _cmt_mode == "fast":
                        # ── OLD AROOJ FAST MODE: async cmt() ──
                        if _real_fid:
                            self.idbv = _real_fid
                        else:
                            self.idbv = base64.b64encode(f"feedback:{_post_id}".encode()).decode("utf-8")
                        self.inline_comments = _cmts
                        self.use_emoji = _use_emoji
                        self.count_per_unit = _cpu
                        self.cmt_mode = "fast"
                        self.account_type = _acct_type
                        self.delay = _delay
                        _selc = _cmt_data.get('slow_selc', 'timeline')
                        self.slow_selc = _selc
                        self.cmt_mode_selc = _selc  # fast mode ke liye bhi set karo
                        await self.maincmt()
                    else:
                        # ── MURSHAD SLOW MODE: FBComment engine (thread executor mein chalo) ──
                        # FB.main ne already login + dtsg + pages fetch kar li hain
                        # FBComment ko wahi data pass karo taake double requests na hon
                        _ua = random.choice(USER_AGENTS_LIST)
                        _fb_c = FBComment(self.cookie, _post_id, _cpu, _delay, _ua, _use_emoji, _cmts)
                        # Already fetched data inject karo — getdata/getuid dobara nahi chalega
                        _fb_c.uid    = getattr(self, 'uid', '0') or '0'
                        _fb_c.token  = getattr(self, 'token', None)
                        _fb_c.fb_dtsg = getattr(self, 'fb_dtsg', None)
                        _fb_c.pro5   = list(getattr(self, 'pro5', []))
                        # pfbid inject karo slow mode mein bhi
                        _fb_c.real_feedback_id = _real_fid
                        _fb_c.slow_selc = _cmt_data.get('slow_selc', 'timeline')

                        def _slow_run():
                            # getuid/getdata skip — data already injected
                            # Sirf pro5 setup karo agar nahi tha
                            if _acct_type == "2":
                                if not _fb_c.pro5:
                                    _fb_c.pro5 = [_fb_c.uid]
                            elif _acct_type == "3":
                                if _fb_c.uid not in _fb_c.pro5:
                                    _fb_c.pro5 = [_fb_c.uid] + _fb_c.pro5
                            else:
                                _fb_c.pro5 = [_fb_c.uid]

                            from concurrent.futures import ThreadPoolExecutor, as_completed as _asc
                            from time import sleep as _slp
                            _tasks = []
                            with ThreadPoolExecutor(max_workers=32) as _executor:
                                for _actor in _fb_c.pro5:
                                    for _ in range(_fb_c.comments_per_id):
                                        _slp(get_random_delay(_fb_c.delay))
                                        _f = _executor.submit(_fb_c.post_comment, _actor)
                                        _tasks.append(_f)
                                for _f in _asc(_tasks):
                                    try:
                                        _f.result()
                                    except Exception:
                                        pass

                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, _slow_run)
            elif self.cv == "3":
                await self.mainjoin()
            elif self.cv == "4":
                await self.mainFollow()
            elif self.cv == "5":
                self.page_create()
                await self.do_sleep()
            elif self.cv == "6":
                if getattr(self, "pa_method", "1") == "2":
                    await self.page_activate_slow()
                else:
                    await self.page_activate()
                await self.do_sleep()

            elif self.cv == "8":
                await self.mainPoll()
            elif self.cv == "13":
                await self.mainPollWithComment()

        except Exception as e:
            logger.exception("FB.main error uid=%s: %s", uid_short, e)
        finally:
            await self._close_session()

# -------------------------
# Runner / CLI flow (async)
# -------------------------

async def run(data, jsondata, loaicv, count):
    try:
        if len(data.split("|")) == 3:
            cookie = "no"
            user = data.split("|")[0]
            password = data.split("|")[1]
            try:
                twofa = data.split("|")[2]
                if twofa == "":
                    twofa = "no"
            except Exception:
                twofa = "no"
        elif len(data.split("|")) == 2:
            cookie = "no"
            user = data.split("|")[0]
            password = data.split("|")[1]
            twofa = "no"
        else:
            user = "no"
            password = "no"
            twofa = "no"
            cookie = data
        # Cookie string clean karo - "cookie: " prefix hata do
        if cookie and cookie != "no":
            _c = cookie.strip()
            if _c.lower().startswith("cookie:"):
                cookie = _c[7:].strip()
        main_obj = FB(user, password, twofa, cookie, jsondata, loaicv, count)
        # Pass comment payload for comment engine (cv=="2")
        if loaicv == "2" and "2" in jsondata:
            _d2 = jsondata["2"]
            main_obj._cmt_payload = {
                "post_id":         _d2.get("idbv", ""),
                "count":           _d2.get("count", 1),
                "delay":           _d2.get("delay", 0),
                "inline_comments": _d2.get("inline_comments", []),
                "account_type":    _d2.get("type", "1"),
                "use_emoji":       _d2.get("use_emoji", True),
                "mode":            _d2.get("mode", "fast"),
                "slow_selc":       _d2.get("slow_selc", "timeline"),
                "post_link":       _d2.get("post_link", ""),
            }
        await main_obj.main()
    except Exception as e:
        logger.exception("run() EXCEPTION: %s", e)


def main():
    banner()

    # ══ LAYER 2: Machine Key ══
    check(block=True)
    create_initial_files()

    _MENU_THEMES = [
        {"MC1":"\033[38;5;57m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;213m","MC6":"\033[38;5;207m","MC7":"\033[38;5;57m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;20m","MC2":"\033[38;5;159m","MC3":"\033[38;5;123m","MC4":"\033[38;5;87m","MC5":"\033[38;5;81m","MC6":"\033[38;5;75m","MC7":"\033[38;5;20m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;28m","MC2":"\033[38;5;231m","MC3":"\033[38;5;194m","MC4":"\033[38;5;157m","MC5":"\033[38;5;120m","MC6":"\033[38;5;83m","MC7":"\033[38;5;28m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;89m","MC2":"\033[38;5;225m","MC3":"\033[38;5;212m","MC4":"\033[38;5;206m","MC5":"\033[38;5;200m","MC6":"\033[38;5;164m","MC7":"\033[38;5;89m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;130m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;229m","MC5":"\033[38;5;228m","MC6":"\033[38;5;222m","MC7":"\033[38;5;130m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;54m","MC2":"\033[38;5;219m","MC3":"\033[38;5;183m","MC4":"\033[38;5;177m","MC5":"\033[38;5;171m","MC6":"\033[38;5;141m","MC7":"\033[38;5;54m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;26m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;123m","MC6":"\033[38;5;117m","MC7":"\033[38;5;26m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;124m","MC2":"\033[38;5;229m","MC3":"\033[38;5;223m","MC4":"\033[38;5;217m","MC5":"\033[38;5;211m","MC6":"\033[38;5;205m","MC7":"\033[38;5;124m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;23m","MC2":"\033[38;5;159m","MC3":"\033[38;5;122m","MC4":"\033[38;5;86m","MC5":"\033[38;5;50m","MC6":"\033[38;5;44m","MC7":"\033[38;5;23m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;91m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;189m","MC5":"\033[38;5;183m","MC6":"\033[38;5;147m","MC7":"\033[38;5;91m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;58m","MC2":"\033[38;5;228m","MC3":"\033[38;5;192m","MC4":"\033[38;5;156m","MC5":"\033[38;5;120m","MC6":"\033[38;5;84m","MC7":"\033[38;5;58m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;197m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;213m","MC6":"\033[38;5;207m","MC7":"\033[38;5;197m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;31m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;153m","MC6":"\033[38;5;117m","MC7":"\033[38;5;31m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;202m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;228m","MC5":"\033[38;5;222m","MC6":"\033[38;5;214m","MC7":"\033[38;5;202m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;61m","MC2":"\033[38;5;225m","MC3":"\033[38;5;219m","MC4":"\033[38;5;183m","MC5":"\033[38;5;147m","MC6":"\033[38;5;141m","MC7":"\033[38;5;61m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;34m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;158m","MC5":"\033[38;5;121m","MC6":"\033[38;5;85m","MC7":"\033[38;5;34m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;53m","MC2":"\033[38;5;231m","MC3":"\033[38;5;218m","MC4":"\033[38;5;212m","MC5":"\033[38;5;206m","MC6":"\033[38;5;170m","MC7":"\033[38;5;53m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;95m","MC2":"\033[38;5;231m","MC3":"\033[38;5;224m","MC4":"\033[38;5;217m","MC5":"\033[38;5;180m","MC6":"\033[38;5;173m","MC7":"\033[38;5;95m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;19m","MC2":"\033[38;5;189m","MC3":"\033[38;5;153m","MC4":"\033[38;5;117m","MC5":"\033[38;5;81m","MC6":"\033[38;5;75m","MC7":"\033[38;5;19m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;128m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;177m","MC6":"\033[38;5;171m","MC7":"\033[38;5;128m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;66m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;153m","MC6":"\033[38;5;116m","MC7":"\033[38;5;66m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;208m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;229m","MC5":"\033[38;5;228m","MC6":"\033[38;5;227m","MC7":"\033[38;5;208m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;36m","MC2":"\033[38;5;159m","MC3":"\033[38;5;122m","MC4":"\033[38;5;86m","MC5":"\033[38;5;79m","MC6":"\033[38;5;43m","MC7":"\033[38;5;36m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;164m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;213m","MC6":"\033[38;5;171m","MC7":"\033[38;5;164m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;33m","MC2":"\033[38;5;159m","MC3":"\033[38;5;123m","MC4":"\033[38;5;117m","MC5":"\033[38;5;81m","MC6":"\033[38;5;75m","MC7":"\033[38;5;33m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;167m","MC2":"\033[38;5;231m","MC3":"\033[38;5;224m","MC4":"\033[38;5;218m","MC5":"\033[38;5;211m","MC6":"\033[38;5;204m","MC7":"\033[38;5;167m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;25m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;123m","MC6":"\033[38;5;87m","MC7":"\033[38;5;25m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;136m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;224m","MC5":"\033[38;5;221m","MC6":"\033[38;5;215m","MC7":"\033[38;5;136m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;55m","MC2":"\033[38;5;225m","MC3":"\033[38;5;219m","MC4":"\033[38;5;183m","MC5":"\033[38;5;177m","MC6":"\033[38;5;141m","MC7":"\033[38;5;55m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;160m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;218m","MC5":"\033[38;5;211m","MC6":"\033[38;5;204m","MC7":"\033[38;5;160m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;40m","MC2":"\033[38;5;231m","MC3":"\033[38;5;194m","MC4":"\033[38;5;157m","MC5":"\033[38;5;121m","MC6":"\033[38;5;85m","MC7":"\033[38;5;40m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;60m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;189m","MC5":"\033[38;5;153m","MC6":"\033[38;5;117m","MC7":"\033[38;5;60m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;131m","MC2":"\033[38;5;231m","MC3":"\033[38;5;224m","MC4":"\033[38;5;218m","MC5":"\033[38;5;211m","MC6":"\033[38;5;181m","MC7":"\033[38;5;131m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;27m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;123m","MC6":"\033[38;5;117m","MC7":"\033[38;5;27m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;214m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;229m","MC5":"\033[38;5;227m","MC6":"\033[38;5;221m","MC7":"\033[38;5;214m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;63m","MC2":"\033[38;5;225m","MC3":"\033[38;5;219m","MC4":"\033[38;5;183m","MC5":"\033[38;5;147m","MC6":"\033[38;5;141m","MC7":"\033[38;5;63m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;106m","MC2":"\033[38;5;231m","MC3":"\033[38;5;229m","MC4":"\033[38;5;192m","MC5":"\033[38;5;156m","MC6":"\033[38;5;149m","MC7":"\033[38;5;106m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;205m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;212m","MC6":"\033[38;5;206m","MC7":"\033[38;5;205m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;38m","MC2":"\033[38;5;159m","MC3":"\033[38;5;123m","MC4":"\033[38;5;116m","MC5":"\033[38;5;80m","MC6":"\033[38;5;44m","MC7":"\033[38;5;38m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;56m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;183m","MC6":"\033[38;5;147m","MC7":"\033[38;5;56m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;24m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;153m","MC5":"\033[38;5;117m","MC6":"\033[38;5;81m","MC7":"\033[38;5;24m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;126m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;183m","MC6":"\033[38;5;177m","MC7":"\033[38;5;126m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;172m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;229m","MC5":"\033[38;5;223m","MC6":"\033[38;5;215m","MC7":"\033[38;5;172m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;65m","MC2":"\033[38;5;231m","MC3":"\033[38;5;194m","MC4":"\033[38;5;157m","MC5":"\033[38;5;150m","MC6":"\033[38;5;114m","MC7":"\033[38;5;65m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;199m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;212m","MC6":"\033[38;5;205m","MC7":"\033[38;5;199m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;32m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;116m","MC6":"\033[38;5;80m","MC7":"\033[38;5;32m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;93m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;177m","MC6":"\033[38;5;141m","MC7":"\033[38;5;93m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;22m","MC2":"\033[38;5;231m","MC3":"\033[38;5;193m","MC4":"\033[38;5;156m","MC5":"\033[38;5;119m","MC6":"\033[38;5;83m","MC7":"\033[38;5;22m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;161m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;218m","MC5":"\033[38;5;212m","MC6":"\033[38;5;205m","MC7":"\033[38;5;161m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;37m","MC2":"\033[38;5;159m","MC3":"\033[38;5;122m","MC4":"\033[38;5;86m","MC5":"\033[38;5;79m","MC6":"\033[38;5;43m","MC7":"\033[38;5;37m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;211m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;212m","MC6":"\033[38;5;211m","MC7":"\033[38;5;211m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;29m","MC2":"\033[38;5;231m","MC3":"\033[38;5;194m","MC4":"\033[38;5;158m","MC5":"\033[38;5;121m","MC6":"\033[38;5;85m","MC7":"\033[38;5;29m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;201m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;213m","MC6":"\033[38;5;207m","MC7":"\033[38;5;201m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;67m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;189m","MC5":"\033[38;5;152m","MC6":"\033[38;5;116m","MC7":"\033[38;5;67m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;94m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;224m","MC5":"\033[38;5;221m","MC6":"\033[38;5;215m","MC7":"\033[38;5;94m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;104m","MC2":"\033[38;5;231m","MC3":"\033[38;5;189m","MC4":"\033[38;5;183m","MC5":"\033[38;5;147m","MC6":"\033[38;5;111m","MC7":"\033[38;5;104m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;143m","MC2":"\033[38;5;231m","MC3":"\033[38;5;229m","MC4":"\033[38;5;222m","MC5":"\033[38;5;192m","MC6":"\033[38;5;156m","MC7":"\033[38;5;143m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;176m","MC2":"\033[38;5;231m","MC3":"\033[38;5;225m","MC4":"\033[38;5;219m","MC5":"\033[38;5;183m","MC6":"\033[38;5;177m","MC7":"\033[38;5;176m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;75m","MC2":"\033[38;5;231m","MC3":"\033[38;5;195m","MC4":"\033[38;5;159m","MC5":"\033[38;5;123m","MC6":"\033[38;5;117m","MC7":"\033[38;5;75m","MC8":"\033[38;5;255m"},
        {"MC1":"\033[38;5;215m","MC2":"\033[38;5;231m","MC3":"\033[38;5;230m","MC4":"\033[38;5;229m","MC5":"\033[38;5;228m","MC6":"\033[38;5;222m","MC7":"\033[38;5;215m","MC8":"\033[38;5;255m"},
    ]
    # Non-repeat: same theme 45 ke baad hi dobara aaye
    _mtheme_file = os.path.join(APP_DATA_DIR, "mtheme.dat")
    try:
        _used_mt = list(map(int, open(_mtheme_file).read().split())) if os.path.exists(_mtheme_file) else []
    except Exception:
        _used_mt = []
    _all_mt = list(range(len(_MENU_THEMES)))
    _avail_mt = [i for i in _all_mt if i not in _used_mt]
    if not _avail_mt:
        _avail_mt = _all_mt
        _used_mt = []
    _mti = random.choice(_avail_mt)
    _used_mt.append(_mti)
    if len(_used_mt) > len(_MENU_THEMES) - 45:
        _used_mt = _used_mt[-(len(_MENU_THEMES) - 45):]
    try:
        open(_mtheme_file, "w").write(" ".join(map(str, _used_mt)))
    except Exception:
        pass
    _MT = _MENU_THEMES[_mti]
    C1=MC3=_MT["MC3"]; C2=MC7=_MT["MC7"]; C3=_MT["MC3"]; C4=MC2=_MT["MC2"]
    C5=MC6=_MT["MC6"]; C6=_MT["MC4"]; C7=MC5=_MT["MC5"]; C8=MC8=_MT["MC8"]
    MC1=_MT["MC1"]; MC4=_MT["MC4"]

    print(f"\n{BOLD}{MC1}╔{'═'*63}╗{reset}")
    print(f"{BOLD}{MC1}║{MC2}{'  ══► WALI KHAN LALA  ◄══  SELECT MODE':^63}{MC1}║{reset}")
    print(f"{BOLD}{MC1}╠{'═'*63}╣{reset}")
    print(f"{BOLD}{MC1}║{reset}  {BOLD}{MC2}»1«{reset} {MC4}REACTIONS        {reset} {MC1}│{reset} {BOLD}{MC5}»2«{reset} {MC3}COMMENTS        {reset}  {BOLD}{MC1}║{reset}")
    print(f"{BOLD}{MC1}║{reset}  {BOLD}{MC5}»3«{reset} {MC6}JOIN GROUP       {reset} {MC1}│{reset} {BOLD}{MC3}»4«{reset} {MC7}FOLLOWERS       {reset}  {BOLD}{MC1}║{reset}")
    print(f"{BOLD}{MC1}║{reset}  {BOLD}{MC7}»5«{reset} {MC2}PAGE CREATE      {reset} {MC1}│{reset} {BOLD}{MC4}»6«{reset} {MC5}PAGE ACTIVATE   {reset}  {BOLD}{MC1}║{reset}")
    print(f"{BOLD}{MC1}║{reset}  {BOLD}{MC6}»7«{reset} {MC2}POLL VOTING      {reset} {MC1}│{reset} {BOLD}{MC2}»8«{reset} {MC5}COOKIE CLEANER  {reset}  {BOLD}{MC1}║{reset}")
    print(f"{BOLD}{MC1}║{reset}  {BOLD}{MC3}»9«{reset} {MC2}TEMP MAIL IDS   {reset} {MC1}│{reset} {BOLD}{MC7}»10«{reset} {MC4}POLL WITH CMT  {reset}  {BOLD}{MC1}║{reset}")
    print(f"{BOLD}{MC1}║{reset}  {BOLD}{MC2}»11«{reset} {MC4}ENTER COOKIES  {reset} {MC1}│{reset} {BOLD}{MC5}»12«{reset} {MC3}HOW TO USE     {reset}  {BOLD}{MC1}║{reset}")
    print(f"{BOLD}{MC1}╚{'═'*63}╝{reset}")

    loaicv = input(f"\n{BOLD}\033[38;5;220m  ══► Select (1-12): {reset}").strip()
    # Map new numbers to internal logic numbers
    _menu_map = {"1":"1","2":"2","3":"3","4":"4","5":"5","6":"6","7":"8","8":"9","9":"11","10":"13","11":"ENTER_COOKIES","12":"HOW_TO_USE"}
    if loaicv not in _menu_map:
        print(f"{neon_red}[X] Invalid mode selection!{reset}")
        input(f"{gold}Press Enter to exit...{reset}")
        return
    loaicv = _menu_map[loaicv]
    if loaicv == "9":
        asyncio.run(remove_expired_cookies())
        return
    if loaicv == "ENTER_COOKIES":
        enter_cookies()
        return
    if loaicv == "HOW_TO_USE":
        how_to_use()
        return
    if loaicv == "11":
        print(f"\n{BOLD}\033[38;5;51m╔{'═'*55}╗{reset}")
        print(f"{BOLD}\033[38;5;51m║\033[38;5;215m{'░'*55}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}{BOLD}\033[38;5;226m{'  ══► TEMP MAIL IDS ◄══':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║\033[38;5;215m{'░'*55}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;255m{'':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}{BOLD}\033[38;5;196m{'  !! APPROVAL NEEDED !!':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;255m{'':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;220m{'  Per Month: 250 USDT':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;255m{'':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;123m{'  Please Contact:':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}{BOLD}\033[38;5;213m{'  WALI KHAN LALA':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║{reset}\033[38;5;255m{'':^55}{reset}{BOLD}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m║\033[38;5;215m{'░'*55}\033[38;5;51m║{reset}")
        print(f"{BOLD}\033[38;5;51m╚{'═'*55}╝{reset}\n")
        input(f"{gold}Press Enter to go back...{reset}")
        return

    # Cookie file number ya path — sirf tab puche jab mode 1-8 ho
    print(f'\n{BOLD}\033[38;5;93m{"═"*65}{reset}')
    print(f'{BOLD}\033[38;5;93m{"":^5}╔{"═"*53}╗{reset}')
    print(f'{BOLD}\033[38;5;93m{"":^5}║{BOLD}\033[38;5;220m{"  ══► WALI KHAN LALA  ◄══  COOKIE FILE":^53}{BOLD}\033[38;5;93m║{reset}')
    print(f'{BOLD}\033[38;5;93m{"":^5}╚{"═"*53}╝{reset}')
    print(f'{BOLD}\033[38;5;93m{"═"*65}{reset}')

    def _resolve_cookie_file(raw_input):
        """File number (1-20) ya full path dono accept karta hai."""
        raw_input = raw_input.strip()
        # Agar sirf number hai
        try:
            n = int(raw_input)
            if 1 <= n <= 20:
                return f"{n}.txt"
            else:
                return None  # number range se bahar
        except ValueError:
            pass
        # Path hai — direct use karo
        if os.path.isabs(raw_input) or os.sep in raw_input or "/" in raw_input or "\\" in raw_input or raw_input.endswith(".txt"):
            return raw_input
        # Koi aur string — try as filename
        return raw_input

    cookie_file = None
    _attempts = 0
    while True:
        try:
            cookie_file_input = input(f"\033[38;5;51m══► File number (1-20) ya file path likho: {reset}").strip()
        except KeyboardInterrupt:
            return
        if not cookie_file_input:
            _attempts += 1
            print(f"{neon_red}[X] Kuch nahi likha! Dobara likho.{reset}")
        else:
            _resolved = _resolve_cookie_file(cookie_file_input)
            if _resolved is None:
                _attempts += 1
                print(f"{neon_red}[X] 1-20 ke beech number ya sahi file path likho!{reset}")
            else:
                cookie_file = _resolved
                break
        if _attempts >= 2:
            print(f"\n{neon_cyan}  [1] ══► Try Again{reset}")
            print(f"{neon_yellow}  [2] ══► Main Menu{reset}")
            try:
                _ch = input(f"{electric_blue}  Select (1/2): {reset}").strip()
            except KeyboardInterrupt:
                return
            if _ch == "1":
                _attempts = 0
                continue
            else:
                main()
                return
    while True:
        try:
            filedata = open(cookie_file, mode="r", encoding="utf-8", errors="ignore").read().split("\n")
            filedata = [x.strip() for x in filedata if x.strip() and not x.strip().startswith("#")]
            if not filedata:
                raise Exception("empty")
            break
        except Exception as e:
            try:
                with open(cookie_file, mode="a", encoding="utf-8") as f:
                    pass
            except Exception:
                logger.exception("main() file create error: %s", e)
            print(f"{neon_red}[X] {cookie_file} mein cookies nahi hain!{reset}")
            files_with_cookies = []
            for i in range(1, 21):
                try:
                    data = open(f"{i}.txt", "r", encoding="utf-8", errors="ignore").read()
                    lines = [l.strip() for l in data.split("\n") if l.strip() and not l.strip().startswith("#")]
                    if lines:
                        files_with_cookies.append(str(i))
                except Exception:
                    pass
            if files_with_cookies:
                print(f"{neon_yellow}Aap ne jo file number/path diya hai us mein koi cookie nahi hai,{reset}")
                print(f"{neon_yellow}lekin apki cookies {', '.join(files_with_cookies)} number wali file(s) mein mojood hain.{reset}")
            else:
                print(f"{neon_yellow}Kisi bhi file mein cookies nahi hain.{reset}")
            print(f"\n{neon_cyan}  [1] ══► Try Again{reset}")
            print(f"{neon_yellow}  [2] ══► Main Menu{reset}")
            try:
                _fch = input(f"{electric_blue}  Select (1/2): {reset}").strip()
            except KeyboardInterrupt:
                return
            if _fch == "1":
                # File selection dobara
                _attempts = 0
                while True:
                    try:
                        cookie_file_input = input(f"\033[38;5;51m══► File number (1-20) ya file path likho: {reset}").strip()
                    except KeyboardInterrupt:
                        return
                    if not cookie_file_input:
                        _attempts += 1
                        print(f"{neon_red}[X] Kuch nahi likha!{reset}")
                    else:
                        _resolved2 = _resolve_cookie_file(cookie_file_input)
                        if _resolved2 is None:
                            _attempts += 1
                            print(f"{neon_red}[X] 1-20 ke beech number ya sahi file path likho!{reset}")
                        else:
                            cookie_file = _resolved2
                            break
                    if _attempts >= 2:
                        print(f"\n{neon_cyan}  [1] ══► Try Again{reset}")
                        print(f"{neon_yellow}  [2] ══► Main Menu{reset}")
                        try:
                            _c2 = input(f"{electric_blue}  Select (1/2): {reset}").strip()
                        except KeyboardInterrupt:
                            return
                        if _c2 == "1":
                            _attempts = 0
                            continue
                        else:
                            main()
                            return
            else:
                main()
                return

    print(f"\n{neon_green}[+] {len(filedata)} cookies load hui!{reset}")

    jsondata = {}
    delay = 0.0

    if loaicv == "1":
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► SELECT ACCOUNT TYPE ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Use IDs          {reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Use Pages        {reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  IDs + Pages Both {reset}")
        account_type = input(f"\033[38;5;228m══► Select Account Type (1/2/3): {reset}").strip()
        if account_type not in ["1", "2", "3"]:
            print(f"{neon_red}[X] Invalid account type selection!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        idbv_raw = input(f"\033[38;5;51m══► Post ID or Link: {reset}")
        print(f"\033[38;5;228m[*] Link check ho raha hai...{reset}")
        idbv = asyncio.run(extract_post_id(idbv_raw))
        if not idbv or not re.match(r'^\d+$', idbv):
            print(f"\033[38;5;196m[X] Link se Post ID nahi mili!{reset}")
            idbv = input(f"\033[38;5;228m══► Post ID manually daalo: {reset}").strip()
        if not idbv or not re.match(r'^\d+$', idbv):
            print(f"\033[38;5;196m[X] Invalid Post ID! Wapas menu par jao.{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        print(f"\033[38;5;40m[+] Post ID: \033[38;5;228m{idbv}{reset}")
        print(f"\n\033[38;5;51m══► REACTIONS: \033[38;5;228m[1]\033[38;5;45mLike \033[38;5;228m[2]\033[38;5;205mLove \033[38;5;228m[3]\033[38;5;123mCare \033[38;5;228m[4]\033[38;5;208mWow \033[38;5;228m[5]\033[38;5;40mHaha \033[38;5;228m[6]\033[38;5;161mSad \033[38;5;228m[7]\033[38;5;88mAngry{reset}")
        print(f"\033[38;5;228m══► Multiple: \033[38;5;51m1+2+4{reset}")
        camxuc = input(f"\033[38;5;45m══► Select Reactions: {reset}").split("+")
        delay = get_delay()

        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► REACTION MODE SELECT ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Fast Mode   {{All Parallel}}{reset}")
        print(f"\033[38;5;123m  ══► [2] ◄══  Smooth Mode {{Save For IDs}}{reset}")
        react_mode_sel = input(f"\033[38;5;228m══► Select Mode (1/2): {reset}").strip()
        reaction_mode = "smooth" if react_mode_sel == "2" else "fast"

        _original_link_r1 = idbv_raw if 'facebook.com' in idbv_raw else ""
        json_data = {"1": {"type": account_type, "idbv": idbv, "camxuc": camxuc, "delay": delay, "reaction_mode": reaction_mode, "post_link": _original_link_r1}}
        jsondata.update(json_data)
    elif loaicv == "2":
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► COMMENT MODE SELECT ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;123m  ══► [1] ◄══  Slow Mode       {{Best for Timeline}}{reset}")
        print(f"\033[38;5;51m  ══► [2] ◄══  Fast Mode       {{Best for RC}}{reset}")
        mode_sel = input(f"\033[38;5;228m══► Select Mode (1/2): {reset}").strip()
        if mode_sel not in ["1", "2"]:
            mode_sel = "2"
        cmt_mode = "slow" if mode_sel == "1" else "fast"

        # ── Account Type ──
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► SELECT ACCOUNT TYPE ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Use IDs          {reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Use Pages        {reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  IDs + Pages Both {reset}")
        account_type = input(f"\033[38;5;228m══► Select Account Type (1/2/3): {reset}").strip()
        if account_type not in ["1", "2", "3"]:
            print(f"{neon_red}[X] Invalid account type!{reset}")
            input(f"{gold}Press Enter...{reset}")
            return

                # ══════════════════════════════════════════
        # SLOW / FAST MODE — Normal flow
        # ══════════════════════════════════════════

        # ── Speed ── (dono modes mein user apna delay set kare — Murshad jaisi tarah)
        delay = get_delay()

        # ── Comments per account ──
        lbl = "ID" if account_type in ("1", "3") else "Page"
        try:
            count_per_unit = int(input(f"{electric_blue}-> Comments per {lbl}: {reset}").strip())
            if count_per_unit < 1:
                count_per_unit = 1
        except Exception:
            count_per_unit = 1

        # ── Emoji option ──
        print(f"\n{neon_yellow}══► Emoji add karo?")
        print(f"  [1] ══► Yes — Emoji lagao")
        print(f"  [2] ══► No  — Bina Emoji{reset}")
        _emoji_sel = input(f"{neon_yellow}══► Select (1/2): {reset}").strip()
        use_emoji = (_emoji_sel != "2")

        # ── Inline Comments Input (SIDD style) ──
        print(f"\n\033[38;5;205m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;205m║\033[38;5;228m{'  ══► COMMENTS LIKHO ◄══':^59}\033[38;5;205m║{reset}")
        print(f"\033[38;5;205m╚{'─'*59}╝{reset}")
        print(f"  {neon_cyan}Ek line = Ek comment  |  Khali Enter = Done{reset}\n")
        inline_comments = []
        _cidx = 1
        while True:
            try:
                _ln = input(f"  {BOLD}\033[38;5;228m{_cidx}:{reset} ").strip()
            except KeyboardInterrupt:
                break
            if not _ln:
                break
            inline_comments.append(_ln)
            _cidx += 1
        if not inline_comments:
            print(f"{neon_red}[X] Koi comment nahi likha!{reset}")
            input(f"{gold}Press Enter...{reset}")
            return
        print(f"\n{neon_green}[+] {len(inline_comments)} comment(s) ready!{reset}")

        # ── Post link / ID ──
        idbv_raw = input(f"\n\033[38;5;51m══► Post ID or Link: {reset}").strip()
        print(f"\033[38;5;228m[*] Link check ho raha hai...{reset}")
        idbv = asyncio.run(extract_post_id(idbv_raw))
        if not idbv or not re.match(r'^\d+$', idbv):
            print(f"\033[38;5;196m[X] Link se Post ID nahi mili!{reset}")
            idbv = input(f"\033[38;5;228m══► Post ID manually daalo: {reset}").strip()
        if not idbv or not re.match(r'^\d+$', idbv):
            print(f"\033[38;5;196m[X] Invalid Post ID!{reset}")
            input(f"{gold}Press Enter...{reset}")
            return
        print(f"\033[38;5;40m[+] Post ID: \033[38;5;228m{idbv}{reset}")

        # Slow mode ke liye group/timeline detect karo
        slow_selc = "timeline"
        if cmt_mode == "slow":
            raw_link = idbv_raw.lower()
            if "groups" in raw_link:
                slow_selc = "group"

        # post_link save karo taake pfbid fetch ho sake (sirf agar original input URL tha)
        _original_link = idbv_raw if 'facebook.com' in idbv_raw else ""
        json_data = {"2": {"type": account_type, "idbv": idbv, "count": count_per_unit, "delay": delay, "inline_comments": inline_comments, "mode": cmt_mode, "slow_selc": slow_selc, "use_emoji": use_emoji, "post_link": _original_link}}
        jsondata.update(json_data)
    elif loaicv == "3":
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► SELECT ACCOUNT TYPE ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Use IDs          {reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Use Pages        {reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  IDs + Pages Both {reset}")
        account_type = input(f"\033[38;5;228m══► Select Account Type (1/2/3): {reset}").strip()
        if account_type not in ["1", "2", "3"]:
            print(f"{neon_red}[X] Invalid account type selection!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        group_id = input(f"{electric_blue}-> Group ID paste karen: {reset}").strip()
        if not group_id:
            print(f"{neon_red}[X] Group ID nahi di!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        delay = get_delay()
        json_data = {"3": {"type": account_type, "delay": delay, "group_id": group_id}}
        jsondata.update(json_data)
    elif loaicv == "4":
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► SELECT ACCOUNT TYPE ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Use IDs          {reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Use Pages        {reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  IDs + Pages Both {reset}")
        account_type = input(f"\033[38;5;228m══► Select Account Type (1/2/3): {reset}").strip()
        if account_type not in ["1", "2", "3"]:
            print(f"{neon_red}[X] Invalid account type selection!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        follow_input = input(f"{electric_blue}-> Profile/Page link ya ID paste karen: {reset}").strip()
        if not follow_input:
            print(f"{neon_red}[X] Link ya ID nahi di!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        print(f"\033[38;5;51m[*] Link check ho raha hai...{reset}")
        if re.match(r'^\d+$', follow_input):
            follow_id = follow_input
        else:
            follow_id = asyncio.run(extract_profile_id(follow_input))
        if follow_id:
            print(f"\033[38;5;40m[+] Profile/Page ID: {follow_id}{reset}")
        else:
            print(f"\033[38;5;196m[!] ID extract nahi hui, manually enter karo{reset}")
            follow_id = input(f"{electric_blue}-> ID manually enter karo: {reset}").strip()
        if not follow_id:
            print(f"{neon_red}[X] ID nahi di!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► ACTION SELECT ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Page Follows{reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Page Likes{reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  Follows + Likes Both{reset}")
        follow_sub_mode = input(f"\033[38;5;228m══► Select (1/2/3): {reset}").strip()
        if follow_sub_mode not in ["1", "2", "3"]:
            follow_sub_mode = "1"
        delay = get_delay()
        json_data = {"4": {"type": account_type, "delay": delay, "follow_id": follow_id, "follow_sub_mode": follow_sub_mode}}
        jsondata.update(json_data)
    elif loaicv == "5":
        print(f"\n\033[38;5;45m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;45m║\033[38;5;228m{'  ══► PAGE CREATE SETTINGS ◄══':^59}\033[38;5;45m║{reset}")
        print(f"\033[38;5;45m╚{'─'*59}╝{reset}")
        page_name = input(f"{electric_blue}-> Enter page name prefix: {reset}")
        delay = get_delay()
        json_data = {"5": {"page_name": page_name, "delay": delay}}
        jsondata.update(json_data)
    elif loaicv == "6":
        print(f"\n\033[38;5;123m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;123m║\033[38;5;228m{'  ══► PAGE ACTIVATE SETTINGS ◄══':^59}\033[38;5;123m║{reset}")
        print(f"\033[38;5;123m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Fast Method  {{Parallel — Sab ek saath}}{reset}")
        print(f"\033[38;5;123m  ══► [2] ◄══  Slow Method  {{One by One — Natural Behavior}}{reset}")
        _pa_method = input(f"\033[38;5;228m══► Select Method (1/2): {reset}").strip()
        if _pa_method not in ["1", "2"]:
            _pa_method = "1"
        delay = get_delay()
        json_data = {"6": {"delay": delay, "pa_method": _pa_method}}
        jsondata.update(json_data)

    elif loaicv == "8":
        print(f"\n\033[38;5;40m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;40m║\033[38;5;228m{'  ══► POLL VOTING SETTINGS ◄══':^59}\033[38;5;40m║{reset}")
        print(f"\033[38;5;40m╚{'─'*59}╝{reset}")

        poll_link = input(f"{electric_blue}-> Poll Link daalo: {reset}").strip()

        all_cookies = []
        try:
            lines = [l.strip() for l in open(cookie_file, "r", encoding="utf-8").readlines()
                     if l.strip() and not l.strip().startswith("#")]
            all_cookies.extend(lines)
        except Exception:
            pass

        if not all_cookies:
            print(f"{neon_red}[X] Koi cookie nahi mili! Pehle cookie daalo.{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return

        question_id, options = fetch_poll_options(poll_link, all_cookies)

        if not (question_id and options):
            print(f"\n{neon_red}[X] Poll options fetch nahi hue!{reset}")
            print(f"{neon_yellow}    Link mein issue hai. Sahi link lagayen aur dobara try karen.{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return

        if question_id and options:
            print(f"\n{neon_green}Poll Options:{reset}")
            for idx, (opt_id, opt_text, vote_count) in enumerate(options, 1):
                print(f"{neon_cyan}  [{idx}] {opt_text}  {gold}Votes: {vote_count}  ID: {opt_id}{reset}")
            print()
            try:
                sel = int(input(f"{gold}-> Option select karo (number): {reset}").strip())
                if 1 <= sel <= len(options):
                    option_id = options[sel - 1][0]
                    poll_data = f"{question_id}|{option_id}"
                    print(f"\n{neon_green}Selected: {options[sel-1][1]}{reset}")
                else:
                    print(f"{neon_red}[X] Invalid selection!{reset}")
                    input(f"{gold}Press Enter to exit...{reset}")
                    return
            except Exception:
                print(f"{neon_red}[X] Invalid input!{reset}")
                input(f"{gold}Press Enter to exit...{reset}")
                return

        print(f"\n{neon_green}Poll Ready:{reset}")
        print(f"{neon_cyan}  Question ID: {question_id}{reset}")
        print(f"{neon_cyan}  Option ID: {option_id}{reset}")

        print(f"\n\033[38;5;205m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;205m║\033[38;5;228m{'  ══► SELECT ACCOUNT TYPE - POLL ◄══':^59}\033[38;5;205m║{reset}")
        print(f"\033[38;5;205m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Use IDs{reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Use Pages{reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  IDs + Pages Both{reset}")
        account_type = input(f"\033[38;5;228m══► Select Account Type (1/2/3): {reset}").strip()
        if account_type not in ["1", "2", "3"]:
            print(f"{neon_red}[X] Invalid! Defaulting to Pages (2).{reset}")
            account_type = "2"
        jsondata = {"8": {"poll_data": poll_data, "poll_count": 0, "type": account_type}}

    elif loaicv == "13":
        print(f"\n\033[38;5;51m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;51m║\033[38;5;228m{'  ══► POLL WITH COMMENT SETTINGS ◄══':^59}\033[38;5;51m║{reset}")
        print(f"\033[38;5;51m╚{'─'*59}╝{reset}")

        poll_link = input(f"{electric_blue}-> Poll Link daalo: {reset}").strip()

        # Selected file ki cookies use karo fetch ke liye
        all_cookies = []
        try:
            lines = [l.strip() for l in open(cookie_file, "r", encoding="utf-8").readlines()
                     if l.strip() and not l.strip().startswith("#")]
            all_cookies.extend(lines)
        except Exception:
            pass

        if not all_cookies:
            print(f"{neon_red}[X] Koi cookie nahi mili! Pehle cookie daalo.{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return

        # Poll options fetch karo
        question_id, options = fetch_poll_options(poll_link, all_cookies)

        if not (question_id and options):
            print(f"\n{neon_red}[X] Poll options fetch nahi hue!{reset}")
            print(f"{neon_yellow}    Link mein issue hai. Sahi link lagayen aur dobara try karen.{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return

        # Option select karo
        print(f"\n{neon_green}Poll Options:{reset}")
        for idx, (opt_id, opt_text, vote_count) in enumerate(options, 1):
            print(f"{neon_cyan}  [{idx}] {opt_text}  {gold}Votes: {vote_count}  ID: {opt_id}{reset}")
        print()
        try:
            sel = int(input(f"{gold}-> Option select karo (number): {reset}").strip())
            if 1 <= sel <= len(options):
                option_id = options[sel - 1][0]
                poll_data = f"{question_id}|{option_id}"
                print(f"\n{neon_green}Selected: {options[sel-1][1]}{reset}")
            else:
                print(f"{neon_red}[X] Invalid selection!{reset}")
                input(f"{gold}Press Enter to exit...{reset}")
                return
        except Exception:
            print(f"{neon_red}[X] Invalid input!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return

        # Post ID poll link se nikalo (comment ke liye idbv chahiye)
        print(f"\033[38;5;228m[*] Post ID extract ho raha hai...{reset}")
        raw_post_id = asyncio.run(extract_post_id(poll_link))
        if not raw_post_id or not re.match(r'^\d+$', raw_post_id):
            raw_post_id = input(f"\033[38;5;228m══► Post ID manually daalo: {reset}").strip()
        if not raw_post_id or not re.match(r'^\d+$', raw_post_id):
            print(f"{neon_red}[X] Post ID nahi mili!{reset}")
            input(f"{gold}Press Enter to exit...{reset}")
            return
        text_idbv = f"feedback:{raw_post_id}"
        idbv_encoded = base64.b64encode(text_idbv.encode()).decode("utf-8")
        print(f"\033[38;5;40m[+] Post ID: \033[38;5;228m{raw_post_id}{reset}")

        # Comments — inline input (SIDD style)
        print(f"\n\033[38;5;205m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;205m║\033[38;5;228m{'  ══► COMMENTS LIKHO ◄══':^59}\033[38;5;205m║{reset}")
        print(f"\033[38;5;205m╚{'─'*59}╝{reset}")
        print(f"  {neon_cyan}Ek line = Ek comment  |  Khali Enter = Done{reset}\n")
        inline_comments = []
        _cidx13 = 1
        while True:
            try:
                _ln13 = input(f"  {BOLD}\033[38;5;228m{_cidx13}:{reset} ").strip()
            except KeyboardInterrupt:
                break
            if not _ln13:
                break
            inline_comments.append(_ln13)
            _cidx13 += 1
        if not inline_comments:
            print(f"{neon_red}[X] Koi comment nahi likha!{reset}")
            input(f"{gold}Press Enter...{reset}")
            return
        print(f"\n{neon_green}[+] {len(inline_comments)} comment(s) ready!{reset}")

        # Account type
        print(f"\n\033[38;5;205m╔{'─'*59}╗{reset}")
        print(f"\033[38;5;205m║\033[38;5;228m{'  ══► SELECT ACCOUNT TYPE ◄══':^59}\033[38;5;205m║{reset}")
        print(f"\033[38;5;205m╚{'─'*59}╝{reset}")
        print(f"\033[38;5;51m  ══► [1] ◄══  Use IDs{reset}")
        print(f"\033[38;5;45m  ══► [2] ◄══  Use Pages{reset}")
        print(f"\033[38;5;123m  ══► [3] ◄══  IDs + Pages Both{reset}")
        account_type = input(f"\033[38;5;228m══► Select Account Type (1/2/3): {reset}").strip()
        if account_type not in ["1", "2", "3"]:
            print(f"{neon_red}[X] Invalid! Defaulting to Pages (2).{reset}")
            account_type = "2"

        delay = get_delay()

        jsondata = {"13": {
            "poll_data": poll_data,
            "idbv": idbv_encoded,
            "raw_post_id": raw_post_id,
            "post_link": poll_link,
            "inline_comments": inline_comments,
            "type": account_type,
            "delay": delay
        }}


    else:
        print(f"{neon_red}[X] Invalid option!{reset}")
        input(f"{gold}Press Enter...{reset}")
        main()
        return

    print(f"\n\033[38;5;205m╔{'═'*59}╗{reset}")
    print(f"\033[38;5;205m║\033[38;5;255m{'':^59}\033[38;5;205m║{reset}")
    print(f"\033[38;5;205m║\033[1m\033[38;5;228m{'  ══► WALI KHAN LALA - PROCESS STARTED ◄══':^59}\033[38;5;205m║{reset}")
    print(f"\033[38;5;205m║\033[38;5;255m{'':^59}\033[38;5;205m║{reset}")
    print(f"\033[38;5;205m╚{'═'*59}╝{reset}\n")

    # ── Async run_round ──
    async def run_round():
        global count, cp, ok, reaction_count, comment_count, follow_count, page_like_count
        global join_count, page_create_count, page_activate_count, poll_vote_count

        count = 0; cp = 0; ok = 0
        reaction_count = 0; comment_count = 0; follow_count = 0; page_like_count = 0
        join_count = 0; page_create_count = 0; page_activate_count = 0
        poll_vote_count = 0; poll_comment_count = 0

        # Semaphore: PC pe 50, mobile/Termux pe 20 (network stability ke liye)
        _is_mobile = platform.system() == "Linux" and "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")
        _max_concurrent = 20 if _is_mobile else 50
        sem = asyncio.Semaphore(_max_concurrent)

        async def run_one(data, idx):
            async with sem:
                await run(data, jsondata, loaicv, idx)

        tasks = [run_one(data, i) for i, data in enumerate(filedata)]
        await asyncio.gather(*tasks, return_exceptions=True)

    # First round
    asyncio.run(run_round())

    # Repeat option for comment, page create, page activate
    if loaicv in ("2", "5", "6"):
        while True:
            try:
                print(f"\n{BOLD}\033[38;5;93m╔{'═'*59}╗{reset}")
                print(f"{BOLD}\033[38;5;93m║\033[38;5;220m{'  ══► ROUND COMPLETE ◄══':^59}\033[38;5;93m║{reset}")
                print(f"{BOLD}\033[38;5;93m╚{'═'*59}╝{reset}")
                if loaicv == "2":
                    print(f"  {BOLD}\033[38;5;118m[1]{reset} ══► Same setting + same link   {{Instant Start}}")
                    print(f"  {BOLD}\033[38;5;208m[2]{reset} ══► Setting change karo        {{New speed/comments}}")
                    print(f"  {BOLD}\033[38;5;196m[3]{reset} ══► Main menu par wapas jao")
                else:
                    print(f"  {BOLD}\033[38;5;118m[1]{reset} ══► Round dobara repeat karo (same settings)")
                    print(f"  {BOLD}\033[38;5;196m[2]{reset} ══► Main menu par wapas jao")
                choice = input(f"\n{BOLD}\033[38;5;220m══► Select: {reset}").strip()
            except KeyboardInterrupt:
                print("\nExiting...")
                break

            if loaicv == "2":
                if choice == "1":
                    print(f"\n{BOLD}\033[38;5;93m╔{'═'*59}╗{reset}")
                    print(f"{BOLD}\033[38;5;93m║\033[1m\033[38;5;220m{'  ══► ROUND REPEAT HO RAHA HAI ◄══':^59}\033[38;5;93m║{reset}")
                    print(f"{BOLD}\033[38;5;93m╚{'═'*59}╝{reset}\n")
                    asyncio.run(run_round())
                elif choice == "2":
                    _new_delay = get_delay()
                    _new_cpu = jsondata["2"].get("count", 1)
                    try:
                        _new_cpu = int(input(f"{electric_blue}-> Comments per account: {reset}").strip())
                        if _new_cpu < 1:
                            _new_cpu = 1
                    except Exception:
                        pass
                    print(f"  {neon_cyan}Naye comments likho (khali Enter = done):{reset}\n")
                    _new_cmts = []
                    _pi = 1
                    while True:
                        try:
                            _pl = input(f"  {BOLD}\033[38;5;228m{_pi}:{reset} ").strip()
                        except KeyboardInterrupt:
                            break
                        if not _pl:
                            break
                        _new_cmts.append(_pl)
                        _pi += 1
                    if _new_cmts:
                        print(f"{neon_green}[+] {len(_new_cmts)} comment(s) ready!{reset}")
                        jsondata["2"]["inline_comments"] = _new_cmts
                    else:
                        print(f"{neon_yellow}[!] Koi comment nahi diya, purane use ho rahe hain.{reset}")
                    jsondata["2"]["delay"] = _new_delay
                    jsondata["2"]["count"] = _new_cpu
                    print(f"\n{BOLD}\033[38;5;93m╔{'═'*59}╗{reset}")
                    print(f"{BOLD}\033[38;5;93m║\033[1m\033[38;5;220m{'  ══► ROUND REPEAT HO RAHA HAI ◄══':^59}\033[38;5;93m║{reset}")
                    print(f"{BOLD}\033[38;5;93m╚{'═'*59}╝{reset}\n")
                    asyncio.run(run_round())
                elif choice == "3":
                    break
                else:
                    print(f"\033[38;5;196m[X] Sirf 1, 2 ya 3 likho!{reset}")
            else:
                if choice == "1":
                    print(f"\n{BOLD}\033[38;5;93m╔{'═'*59}╗{reset}")
                    print(f"{BOLD}\033[38;5;93m║\033[1m\033[38;5;220m{'  ══► ROUND REPEAT HO RAHA HAI ◄══':^59}\033[38;5;93m║{reset}")
                    print(f"{BOLD}\033[38;5;93m╚{'═'*59}╝{reset}\n")
                    asyncio.run(run_round())
                elif choice == "2":
                    break
                else:
                    print(f"\033[38;5;196m[X] Sirf 1 ya 2 likho!{reset}")


if __name__ == "__main__":
    while True:
        try:
            main()
            try:
                print(f"\n\033[38;5;228m══► \033[38;5;51mProcess Completed Successfully! \033[38;5;205m◄══{reset}")
            except Exception:
                print("\nProcess has been completed.")
            try:
                input(f"\033[38;5;123m══► Press Enter to return to menu (Ctrl+C to exit)... ◄══{reset}")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
