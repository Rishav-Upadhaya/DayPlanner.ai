# UI ↔ API Field Mapping

## Today TimeBlock
- UI `title` -> API `title`
- UI `startTime` -> API `start_time`
- UI `endTime` -> API `end_time`
- UI `priority` -> API `priority`
- UI `category` -> API `category`
- UI `completed` -> API `completed`

## Chat
- UI message input -> API `content`
- API response `summary` -> chat plan preview summary
- API response `blocks[]` -> plan preview blocks

## Settings
- UI planning style -> API `planning_style`
- UI timezone -> API `timezone`
- UI morning briefing time -> API `morning_briefing_time`
- UI evening check-in time -> API `evening_checkin_time`
