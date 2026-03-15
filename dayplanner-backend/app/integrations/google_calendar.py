from datetime import datetime, timedelta, timezone

import httpx


class GoogleCalendarClient:
    def get_events_for_day(self, access_token: str, day: str) -> list[dict]:
        day_start = datetime.fromisoformat(f'{day}T00:00:00').replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        try:
            response = httpx.get(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                headers={'Authorization': f'Bearer {access_token}'},
                params={
                    'timeMin': day_start.isoformat(),
                    'timeMax': day_end.isoformat(),
                    'singleEvents': 'true',
                    'orderBy': 'startTime',
                    'maxResults': 250,
                },
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
            items = payload.get('items', [])

            events = []
            for item in items:
                start_value = item.get('start', {}).get('dateTime')
                end_value = item.get('end', {}).get('dateTime')
                if not start_value or not end_value:
                    continue
                events.append(
                    {
                        'id': item.get('id', ''),
                        'title': item.get('summary', 'Untitled event'),
                        'starts_at': start_value,
                        'ends_at': end_value,
                    }
                )
            return events
        except Exception:
            return []
