from datetime import datetime, timezone, timedelta
from typing import List, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup, Tag

from app.models import Lesson, Replacement, Schedule
from app.services.html_service import fetch_html

_MSK = timezone(timedelta(hours=3))


async def get_schedule_for_day(
    base_url: str,
    building_key: str,
    group_name: str,
    weekday: int,
    apply_replacements: bool,
) -> Schedule:
    if apply_replacements:
        today = datetime.now(_MSK).weekday()
        if weekday != today:
            raise ValueError("Replacements can only be applied for today's schedule")

    url = f"{base_url}/{building_key}/{quote(group_name, safe='')}"
    html = await fetch_html(url)
    schedules = _parse_schedules(html)

    if weekday < 0 or weekday >= len(schedules):
        raise ValueError(f"Weekday {weekday} not found in schedule (available: 0-{len(schedules)-1})")

    schedule = schedules[weekday]

    if apply_replacements:
        replacements = _parse_replacements(html)
        schedule = _apply_replacements(schedule, replacements)

    return schedule


def _parse_schedules(html: str) -> List[Schedule]:
    soup = BeautifulSoup(html, "lxml")

    grid = soup.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "grid", "lg:grid-cols-2", "gap-4",
    ]))
    if not grid:
        raise RuntimeError("Failed to parse schedule: day-cards grid not found")

    day_cards = grid.find_all(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "rounded-2xl", "border", "border-[#E7EEF6]", "bg-white", "shadow-sm",
    ]))

    schedules: List[Schedule] = []
    for card in day_cards:
        weekday_el = card.find(lambda tag: tag.name == "h2" and all(c in (tag.get("class") or []) for c in [
            "font-bold",
        ]))
        if not weekday_el:
            # try any heading-like tag with font-bold
            weekday_el = card.find(lambda tag: "font-bold" in (tag.get("class") or []))
        weekday_name = weekday_el.get_text(strip=True) if weekday_el else ""

        lesson_elements = card.find_all(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
            "flex", "flex-row", "gap-4", "rounded-xl", "bg-[#F7FAFF]",
        ]))

        lessons: List[Lesson] = []
        for el in lesson_elements:
            lesson = _parse_lesson(el)
            if lesson:
                lessons.append(lesson)

        schedules.append(Schedule(weekday=weekday_name, lessons=lessons))

    return schedules


def _parse_lesson(el: Tag) -> Optional[Lesson]:
    section1 = el.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "flex", "flex-col", "items-center", "shrink-0", "text-center",
    ]))
    section2 = el.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "flex", "flex-col", "flex-1", "justify-center", "items-start",
    ]))
    if not section1 or not section2:
        return None

    number_el = section1.find(lambda tag: "font-semibold" in (tag.get("class") or []) and "text-sm" in (tag.get("class") or []))
    time_el = section1.find(lambda tag: "mt-1" in (tag.get("class") or []) and "text-xs" in (tag.get("class") or []))
    subject_el = section2.find(lambda tag: "font-semibold" in (tag.get("class") or []) and "break-words" in (tag.get("class") or []))
    teacher_el = section2.find(lambda tag: "italic" in (tag.get("class") or []) and "text-gray-600" in (tag.get("class") or []))
    room_el = section2.find(lambda tag: "text-gray-500" in (tag.get("class") or []) and "text-sm" in (tag.get("class") or []))

    if not number_el:
        return None

    number_text = number_el.get_text(strip=True)
    time_text = time_el.get_text(strip=True) if time_el else ""
    subject = subject_el.get_text(strip=True) if subject_el else ""
    teacher = teacher_el.get_text(strip=True) if teacher_el else ""
    room_raw = room_el.get_text(strip=True) if room_el else ""

    return Lesson(
        number=_extract_number(number_text),
        time=_format_time(time_text),
        subject=subject,
        teacher=teacher,
        room=_format_room(room_raw),
    )


def _parse_replacements(html: str) -> List[Replacement]:
    soup = BeautifulSoup(html, "lxml")

    container = soup.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "border-2", "border-orange-200", "bg-orange-50",
    ]))
    if not container:
        return []

    grid = container.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "flex-1", "grid", "grid-cols-1", "gap-3",
    ]))
    if not grid:
        return []

    items = grid.find_all(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
        "flex", "flex-row", "gap-3", "rounded-xl", "bg-orange-100", "border-orange-200",
    ]))

    replacements: List[Replacement] = []
    for item in items:
        section1 = item.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
            "flex", "flex-col", "items-center", "shrink-0", "text-center",
        ]))
        section2 = item.find(lambda tag: tag.name == "div" and all(c in (tag.get("class") or []) for c in [
            "flex", "flex-col", "flex-1", "justify-center", "items-start",
        ]))
        if not section1 or not section2:
            continue

        number_el = section1.find(lambda tag: "font-semibold" in (tag.get("class") or []) and "text-xs" in (tag.get("class") or []))
        subject_el = section2.find(lambda tag: "font-semibold" in (tag.get("class") or []) and "text-orange-800" in (tag.get("class") or []))
        teacher_el = section2.find(lambda tag: "italic" in (tag.get("class") or []) and "text-orange-600" in (tag.get("class") or []))
        room_el = section2.find(lambda tag: "text-orange-500" in (tag.get("class") or []) and "text-xs" in (tag.get("class") or []))

        if not number_el:
            continue

        number_text = number_el.get_text(strip=True)
        subject = subject_el.get_text(strip=True) if subject_el else ""
        teacher_raw = teacher_el.get_text(strip=True) if teacher_el else ""
        room = room_el.get_text(strip=True) if room_el else ""

        replacements.append(Replacement(
            number=_extract_number(number_text),
            subject=subject,
            teacher=_extract_teacher(teacher_raw),
            room=room,
        ))

    return replacements


def _apply_replacements(schedule: Schedule, replacements: List[Replacement]) -> Schedule:
    if not replacements:
        return schedule

    repl_map = {r.number: r for r in replacements}
    new_lessons: List[Lesson] = []
    for lesson in schedule.lessons:
        r = repl_map.get(lesson.number)
        if r:
            teacher = lesson.teacher if (not r.teacher or r.teacher == "замена кабинета") else r.teacher
            room = f"{r.room} (замена)" if r.room else lesson.room
            new_lessons.append(Lesson(
                number=lesson.number,
                time=lesson.time,
                subject=r.subject,
                teacher=teacher,
                room=room,
            ))
        else:
            new_lessons.append(lesson)

    return Schedule(weekday=schedule.weekday, lessons=new_lessons)


def _extract_number(text: str) -> int:
    return int(text.strip().split()[0])


def _format_time(time_str: str) -> str:
    # Normalize: "8:00 9:35" → "08:00 - 09:35"
    time_str = time_str.replace("\u00a0", " ").strip()
    parts = time_str.split()
    if len(parts) == 2:
        start, end = parts[0], parts[1]
        if len(start) == 4:
            start = "0" + start  # 8:00 → 08:00
        if len(end) == 4:
            end = "0" + end
        return f"{start} - {end}"
    return time_str


def _format_room(room: str) -> str:
    if not room:
        return room
    return room[0].upper() + room[1:]


def _extract_teacher(text: str) -> str:
    prefix = "Кто заменяет: "
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
