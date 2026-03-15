from typing import Any

from app.agents.langgraph_agent.prompts import build_system_prompt, build_user_prompt
from app.agents.langgraph_agent.state import AgentState
from app.agents.langgraph_agent.tools import (
    category_for_task,
    enforce_calendar_events,
    extract_class_window,
    extract_recurring_class_window,
    extract_task_candidates,
    normalize_hhmm,
    normalize_blocks,
    parse_json_payload,
    to_minutes,
)
from app.integrations.llm_client import AgentLLMGateway


class ReasonAndRespondNode:
    def __init__(self, llm_gateway: AgentLLMGateway) -> None:
        self.llm = llm_gateway

    def run(self, state: AgentState) -> AgentState:
        llm_config = state.get('llm_config', {})
        existing_calendar_events = state.get('existing_calendar_events', [])
        user_input = state.get('user_input', '')
        approval_intent = self._is_approval_intent(user_input)

        parsed = None
        try:
            raw = self.llm.generate(
                system_prompt=build_system_prompt(),
                user_prompt=build_user_prompt(state),
                primary_provider=llm_config.get('primary_provider', ''),
                primary_api_key=llm_config.get('primary_api_key', ''),
                primary_model=llm_config.get('primary_model', ''),
                fallback_provider=llm_config.get('fallback_provider', ''),
                fallback_api_key=llm_config.get('fallback_api_key', ''),
                fallback_model=llm_config.get('fallback_model', ''),
            )
            parsed = parse_json_payload(raw)
        except Exception:
            parsed = None

        if parsed is None:
            return self._heuristic_fallback(state)

        blocks = normalize_blocks(parsed.get('blocks', []))
        blocks = enforce_calendar_events(blocks=blocks, calendar_events=existing_calendar_events)
        follow_ups = [str(item).strip() for item in parsed.get('follow_up_questions', []) if str(item).strip()]
        assistant_reply = str(parsed.get('assistant_reply', '')).strip()
        summary = str(parsed.get('summary', '')).strip()
        needs_clarification = bool(parsed.get('needs_clarification', False))
        save_to_today = bool(parsed.get('save_to_today', False))

        if not assistant_reply:
            assistant_reply = 'I need a little more context before creating your best plan.'
            needs_clarification = True

        if needs_clarification:
            if self._has_sufficient_planning_context(state) or self._is_direct_planning_request(user_input):
                return self._heuristic_fallback(state)
            blocks = []
            save_to_today = False

        if approval_intent and blocks and not needs_clarification:
            save_to_today = True

        return {
            'assistant_reply': assistant_reply,
            'summary': summary,
            'blocks': blocks,
            'save_to_today': save_to_today,
            'needs_clarification': needs_clarification,
            'follow_up_questions': follow_ups,
        }

    def _is_approval_intent(self, text: str) -> bool:
        lower_text = text.lower()
        patterns = [
            'approve',
            'looks good',
            'save this',
            'save it',
            'apply this',
            'finalize',
            'go ahead',
            'yes save',
            'yes, save',
            'confirm plan',
        ]
        return any(pattern in lower_text for pattern in patterns)

    def _combined_user_context_text(self, state: AgentState) -> str:
        current = state.get('user_input', '').strip()
        recent = state.get('recent_messages', [])
        previous_user_lines = [
            str(item.get('content', '')).strip()
            for item in recent
            if str(item.get('role', '')).lower() == 'user' and str(item.get('content', '')).strip()
        ]
        combined = ' '.join(previous_user_lines[-6:])
        if current and current not in combined:
            combined = f'{combined} {current}'.strip()
        return combined.strip()

    def _has_sufficient_planning_context(self, state: AgentState) -> bool:
        text = self._combined_user_context_text(state)
        if not text:
            return False
        plan_date = state.get('plan_date', '')
        class_window = extract_recurring_class_window(text, plan_date) or extract_class_window(text)
        task_candidates = extract_task_candidates(text)
        return class_window is not None or len(task_candidates) >= 2

    def _is_direct_planning_request(self, text: str) -> bool:
        lower_text = text.lower()
        triggers = ['plan my day', 'help me plan', 'tasks:', 'i need to', 'start at', 'start from']
        return any(trigger in lower_text for trigger in triggers)

    def _heuristic_fallback(self, state: AgentState) -> AgentState:
        text = state.get('user_input', '').strip()
        plan_date = state.get('plan_date', '')
        existing_calendar_events = state.get('existing_calendar_events', [])
        lower_text = text.lower()
        approval_intent = self._is_approval_intent(text)
        source_text = self._combined_user_context_text(state) if approval_intent else text

        asks_meetings = (
            ('?' in lower_text and any(token in lower_text for token in ['meeting', 'meetings', 'calendar']))
            or any(
                phrase in lower_text
                for phrase in [
                    'do i have meeting',
                    'do i have meetings',
                    'any meetings',
                    'have meetings',
                    'check meetings',
                    'check calendar',
                    'what meetings',
                ]
            )
        )
        if asks_meetings:
            if existing_calendar_events:
                event_lines = []
                for event in existing_calendar_events[:6]:
                    title = str(event.get('title', 'Meeting')).strip() or 'Meeting'
                    start_time = normalize_hhmm(str(event.get('start_time', '09:00')))
                    end_time = normalize_hhmm(str(event.get('end_time', '10:00')))
                    event_lines.append(f'- {start_time}-{end_time}: {title}')

                meeting_blocks = enforce_calendar_events(blocks=[], calendar_events=existing_calendar_events)
                return {
                    'assistant_reply': (
                        'Yes — here are your meetings/calendar events for the day:\n\n'
                        + '\n'.join(event_lines)
                    ),
                    'summary': f'Found {len(existing_calendar_events)} calendar event(s) for the day.',
                    'save_to_today': False,
                    'needs_clarification': False,
                    'follow_up_questions': [],
                    'blocks': meeting_blocks,
                }

            return {
                'assistant_reply': 'I do not see any synced meetings for today yet. If you just connected Google Calendar, try syncing once and ask again.',
                'summary': 'No meetings found for today in synced calendar data.',
                'save_to_today': False,
                'needs_clarification': False,
                'follow_up_questions': [],
                'blocks': [],
            }

        class_window = extract_recurring_class_window(source_text, plan_date) or extract_class_window(source_text)
        task_candidates = extract_task_candidates(source_text)
        has_time = class_window is not None
        has_task = len(task_candidates) > 0

        if not (has_time or has_task):
            questions = [
                'What are your top 2-3 priorities for today?',
                'Any fixed commitments (meetings/classes) with times?',
                'What time do you want to start and end your day?',
            ]
            return {
                'assistant_reply': 'Thanks — before I build your plan, I need a bit more context:\n\n- ' + '\n- '.join(questions),
                'summary': 'Need more context to build a reliable schedule.',
                'save_to_today': False,
                'needs_clarification': True,
                'follow_up_questions': questions,
                'blocks': [],
            }

        blocks: list[dict[str, Any]] = []
        start_minutes = 9 * 60

        if class_window:
            class_start, class_end = class_window
            blocks.append(
                {
                    'title': 'Class Schedule',
                    'start_time': class_start,
                    'end_time': class_end,
                    'priority': 'high',
                    'category': 'class',
                    'completed': False,
                }
            )
            start_minutes = to_minutes(class_end) + 30

        for index, task in enumerate(task_candidates[:6]):
            slot_start = start_minutes + (index * 90)
            slot_end = slot_start + 75
            blocks.append(
                {
                    'title': task[:120],
                    'start_time': normalize_hhmm(f"{slot_start // 60}:{slot_start % 60:02d}"),
                    'end_time': normalize_hhmm(f"{slot_end // 60}:{slot_end % 60:02d}"),
                    'priority': 'high' if index == 0 else 'medium',
                    'category': category_for_task(task),
                    'completed': False,
                }
            )

        if not task_candidates:
            blocks.extend(
                [
                    {
                        'title': 'Priority Focus Block',
                        'start_time': '09:00',
                        'end_time': '10:30',
                        'priority': 'high',
                        'category': 'work',
                        'completed': False,
                    },
                    {
                        'title': 'Execution Sprint',
                        'start_time': '11:00',
                        'end_time': '12:00',
                        'priority': 'medium',
                        'category': 'work',
                        'completed': False,
                    },
                    {
                        'title': 'Review and Adjust',
                        'start_time': '17:00',
                        'end_time': '17:30',
                        'priority': 'medium',
                        'category': 'personal',
                        'completed': False,
                    },
                ]
            )

        blocks = enforce_calendar_events(blocks=blocks, calendar_events=existing_calendar_events)

        key_tasks = ', '.join(task_candidates[:3]) if task_candidates else 'your top priorities'
        class_note = ''
        if class_window:
            class_note = f' I included your class block from {class_window[0]} to {class_window[1]}.'

        return {
            'assistant_reply': (
                f'Great — I built a plan focused on {key_tasks}.{class_note}\n\n'
                '### Plan Outline\n'
                '- Time blocks are aligned to your stated priorities.\n'
                '- Existing calendar events are treated as hard constraints.\n'
                '- You can ask me to rebalance workload or add breaks.'
            ),
            'summary': f'Personalized plan generated from your query for {plan_date}.',
            'save_to_today': approval_intent,
            'needs_clarification': False,
            'follow_up_questions': [],
            'blocks': blocks,
        }
