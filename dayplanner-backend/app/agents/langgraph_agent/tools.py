import json
import re
from datetime import datetime
from typing import Any


DAY_ORDER = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}


def parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or '').strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            return None

    obj = re.search(r'(\{.*\})', text, re.DOTALL)
    if obj:
        try:
            return json.loads(obj.group(1))
        except json.JSONDecodeError:
            return None
    return None


def normalize_hhmm(value: str) -> str:
    m = re.fullmatch(r'(\d{1,2}):(\d{2})', value.strip())
    if not m:
        return '09:00'
    hour = max(0, min(23, int(m.group(1))))
    minute = max(0, min(59, int(m.group(2))))
    return f'{hour:02d}:{minute:02d}'


def normalize_ampm_time(value: str) -> str | None:
    cleaned = re.sub(r'\s+', ' ', value.strip().lower())
    for fmt in ('%I:%M %p', '%I %p'):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.strftime('%H:%M')
        except ValueError:
            continue
    return None


def to_minutes(value: str) -> int:
    normalized = normalize_hhmm(value)
    hour, minute = normalized.split(':')
    return int(hour) * 60 + int(minute)


def overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    a_start = to_minutes(start_a)
    a_end = to_minutes(end_a)
    b_start = to_minutes(start_b)
    b_end = to_minutes(end_b)
    return a_start < b_end and a_end > b_start


def normalize_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in blocks[:12]:
        title = str(item.get('title', '')).strip()[:255]
        if not title:
            continue
        start_time = normalize_hhmm(str(item.get('start_time', '09:00')))
        end_time = normalize_hhmm(str(item.get('end_time', '10:00')))
        priority = str(item.get('priority', 'medium')).lower().strip()
        if priority not in {'high', 'medium', 'low'}:
            priority = 'medium'
        category = str(item.get('category', 'work')).lower().strip()[:32] or 'work'
        normalized.append(
            {
                'title': title,
                'start_time': start_time,
                'end_time': end_time,
                'priority': priority,
                'category': category,
                'completed': bool(item.get('completed', False)),
            }
        )
    return normalized


def extract_day_name(plan_date: str) -> str | None:
    try:
        return datetime.fromisoformat(plan_date).strftime('%A').lower()
    except ValueError:
        return None


def day_in_range(day_name: str, start_day: str, end_day: str) -> bool:
    if day_name not in DAY_ORDER or start_day not in DAY_ORDER or end_day not in DAY_ORDER:
        return False
    day_value = DAY_ORDER[day_name]
    start_value = DAY_ORDER[start_day]
    end_value = DAY_ORDER[end_day]
    if start_value <= end_value:
        return start_value <= day_value <= end_value
    return day_value >= start_value or day_value <= end_value


def extract_recurring_class_window(text: str, plan_date: str) -> tuple[str, str] | None:
    lower_text = text.lower()
    day_name = extract_day_name(plan_date)
    if not day_name:
        return None

    ranged = re.search(
        r'(?:everyday\s+)?from\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+to\s+'
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+from\s+'
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))',
        lower_text,
        re.IGNORECASE,
    )
    if ranged:
        start_day = ranged.group(1).lower()
        end_day = ranged.group(2).lower()
        if day_in_range(day_name, start_day, end_day):
            start_time = normalize_ampm_time(ranged.group(3))
            end_time = normalize_ampm_time(ranged.group(4))
            if start_time and end_time:
                return start_time, end_time

    everyday = re.search(
        r'every\s*day.*?from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))',
        lower_text,
        re.IGNORECASE,
    )
    if everyday:
        start_time = normalize_ampm_time(everyday.group(1))
        end_time = normalize_ampm_time(everyday.group(2))
        if start_time and end_time:
            return start_time, end_time

    return None


def extract_class_window(text: str) -> tuple[str, str] | None:
    ampm_match = re.search(
        r'from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))',
        text,
        re.IGNORECASE,
    )
    if ampm_match:
        start_time = normalize_ampm_time(ampm_match.group(1))
        end_time = normalize_ampm_time(ampm_match.group(2))
        if start_time and end_time:
            return start_time, end_time

    hhmm_match = re.search(r'from\s+(\d{1,2}:\d{2})\s+to\s+(\d{1,2}:\d{2})', text, re.IGNORECASE)
    if hhmm_match:
        return normalize_hhmm(hhmm_match.group(1)), normalize_hhmm(hhmm_match.group(2))

    return None


def extract_task_candidates(text: str) -> list[str]:
    lower_text = text.lower()
    segment = text
    marker = 'things like'
    explicit_task_phrase = False
    if marker in lower_text:
        start_index = lower_text.find(marker) + len(marker)
        segment = text[start_index:]
        explicit_task_phrase = True
    elif 'i need to' in lower_text:
        start_index = lower_text.find('i need to') + len('i need to')
        segment = text[start_index:]
        explicit_task_phrase = True

    if 'tasks:' in lower_text:
        start_index = lower_text.find('tasks:') + len('tasks:')
        segment = text[start_index:]
        explicit_task_phrase = True

    if explicit_task_phrase:
        segment = re.split(r'[\n]', segment)[0]
    normalized = re.sub(r'\band\b', ',', segment, flags=re.IGNORECASE)
    chunks = [piece.strip(' ,;:-') for piece in normalized.split(',')]
    tasks = [
        item
        for item in chunks
        if (len(item.split()) >= 2) or (explicit_task_phrase and len(item) > 2)
    ]
    if tasks:
        return tasks[:8]

    fallback_chunks = [piece.strip(' ,;:-') for piece in re.split(r',|\band\b', text, flags=re.IGNORECASE)]
    return [item for item in fallback_chunks if len(item.split()) >= 2][:6]


def category_for_task(title: str) -> str:
    value = title.lower()
    if any(token in value for token in ['class', 'lecture', 'study']):
        return 'class'
    if any(token in value for token in ['meeting', 'call', 'sync']):
        return 'meeting'
    if any(token in value for token in ['break', 'lunch', 'rest']):
        return 'break'
    if any(token in value for token in ['personal', 'family', 'errand']):
        return 'personal'
    return 'work'


def enforce_calendar_events(blocks: list[dict[str, Any]], calendar_events: list[dict[str, str]]) -> list[dict[str, Any]]:
    event_blocks: list[dict[str, Any]] = []
    for event in calendar_events:
        title = str(event.get('title', '')).strip()
        start_time = normalize_hhmm(str(event.get('start_time', '09:00')))
        end_time = normalize_hhmm(str(event.get('end_time', '10:00')))
        if not title:
            continue
        event_type = 'meeting'
        lower_title = title.lower()
        if 'class' in lower_title or 'lecture' in lower_title:
            event_type = 'class'

        event_blocks.append(
            {
                'title': title,
                'start_time': start_time,
                'end_time': end_time,
                'priority': 'high',
                'category': event_type,
                'completed': False,
            }
        )

    if not event_blocks:
        return blocks

    filtered_blocks: list[dict[str, Any]] = []
    for block in blocks:
        overlaps_event = any(
            overlaps(block.get('start_time', '09:00'), block.get('end_time', '10:00'), event['start_time'], event['end_time'])
            for event in event_blocks
        )
        if overlaps_event:
            continue
        filtered_blocks.append(block)

    merged = event_blocks + filtered_blocks
    merged.sort(key=lambda item: to_minutes(str(item.get('start_time', '09:00'))))
    return merged[:20]
