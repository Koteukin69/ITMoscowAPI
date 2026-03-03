import time
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from app.models import Building
from app.services.html_service import fetch_html

# Simple in-memory TTL cache (works on warm Vercel instances)
_cache: Optional[Tuple[List[Building], float]] = None
_CACHE_TTL = 30 * 60  # 30 minutes


def _is_cache_valid() -> bool:
    return _cache is not None and (time.time() - _cache[1]) < _CACHE_TTL


async def get_all_buildings(base_url: str) -> List[Building]:
    global _cache

    if _is_cache_valid():
        return _cache[0]  # type: ignore[index]

    html = await fetch_html(base_url)
    buildings = _parse_buildings(html)
    _cache = (buildings, time.time())
    return buildings


def _parse_buildings(html: str) -> List[Building]:
    soup = BeautifulSoup(html, "lxml")

    # Sticky top nav bar (now a <header> element)
    nav = soup.find(lambda tag: tag.name == "header" and all(c in (tag.get("class") or []) for c in [
        "sticky", "top-0", "z-40", "bg-white",
    ]))
    if not nav:
        raise RuntimeError("Failed to parse buildings: nav not found")

    # First dropdown group (directly inside header, no intermediate menu_row wrapper)
    group_div = nav.find(lambda tag: tag.name == "div" and "group" in (tag.get("class") or []) and "relative" in (tag.get("class") or []))
    if not group_div:
        raise RuntimeError("Failed to parse buildings: dropdown group not found")

    # Invisible dropdown panel
    dropdown = group_div.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "invisible", "absolute", "top-full", "bg-white", "shadow-lg",
    ]))
    if not dropdown:
        raise RuntimeError("Failed to parse buildings: dropdown panel not found")

    # Building links
    links = dropdown.find_all(lambda tag: tag.name == "a" and all(c in (tag.get("class") or []) for c in [
        "flex", "items-center", "gap-2", "px-4", "py-2", "text-sm", "hover:bg-gray-100",
    ]))

    buildings: List[Building] = []
    for link in links:
        href = link.get("href", "")
        key = href.lstrip("/")
        name = link.get_text(strip=True)
        if key and name:
            buildings.append(Building(name=name, key=key))

    return buildings
