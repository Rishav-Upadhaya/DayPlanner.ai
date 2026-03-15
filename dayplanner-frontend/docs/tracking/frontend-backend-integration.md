# Frontend ↔ Backend Integration Plan

## Goal
Replace current mock/local feature state with backend API integration while preserving UX flow.

## Feature Mapping
- Today page → `/api/v1/plans/today`, `/api/v1/plans/generate`, `/api/v1/plans/{plan_id}/blocks/{block_id}`
- Chat page → `/api/v1/chat/sessions`, `/api/v1/chat/sessions/{session_id}/messages`
- Calendar page → `/api/v1/calendar/accounts`, `/api/v1/calendar/sync-all`, `/api/v1/calendar/conflicts`
- History page → `/api/v1/history/summary`, `/api/v1/history/weekly-performance`, `/api/v1/history/plans`
- Settings page → `/api/v1/settings`, `/api/v1/memory/context`, `/api/v1/memory/reset`

## Migration Sequence
1. Add typed API client and auth token wiring.
2. Replace Today page mock plan calls.
3. Replace Chat local flow invocation with backend calls.
4. Integrate Calendar/History/Settings endpoints.
5. Remove local mocks and fallback temporary adapters.
