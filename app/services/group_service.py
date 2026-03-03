import asyncio
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

from bs4 import BeautifulSoup

from app.models import Building, GroupItem
from app.services.html_service import fetch_html

# in-memory TTL cache: building_key -> (groups, timestamp)
_cache: Dict[str, Tuple[List[GroupItem], float]] = {}
_CACHE_TTL = 30 * 60  # 30 minutes


async def get_groups_for_building(building: Building, base_url: str) -> List[GroupItem]:
    cached = _cache.get(building.key)
    if cached and (time.time() - cached[1]) < _CACHE_TTL:
        return cached[0]

    url = f"{base_url}/{building.key}"
    html = await fetch_html(url)
    groups = _parse_groups(html, building.key)
    _cache[building.key] = (groups, time.time())
    return groups


async def get_all_groups(buildings: List[Building], base_url: str) -> List[GroupItem]:
    results = await asyncio.gather(*[get_groups_for_building(b, base_url) for b in buildings])
    all_groups: List[GroupItem] = []
    for group_list in results:
        all_groups.extend(group_list)
    return all_groups


def _parse_groups(html: str, building_key: str) -> List[GroupItem]:
    soup = BeautifulSoup(html, "lxml")

    # Groups list (now a <ul id="groupsList">)
    list_container = soup.find("ul", id="groupsList")
    if not list_container:
        raise RuntimeError(f"Failed to parse groups for building '{building_key}': groupsList not found")

    group_items = list_container.find_all(class_="group-item")

    groups: List[GroupItem] = []
    for item in group_items:
        link = item.find(lambda tag: tag.name == "a" and all(c in (tag.get("class") or []) for c in [
            "block", "px-4", "py-3", "rounded-lg", "font-medium",
        ]))
        if link:
            name = link.get_text(strip=True)
            groups.append(GroupItem(
                name=name,
                building=building_key,
                key=quote(name, safe=""),
            ))

    return groups
