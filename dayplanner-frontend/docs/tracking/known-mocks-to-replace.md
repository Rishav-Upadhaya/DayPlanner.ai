# Known Mocks To Replace

## Replaced in current implementation
- `src/app/(app)/today/page.tsx` now calls backend plans endpoints.
- `src/components/chat/chat-interface.tsx` now uses backend chat endpoints.
- `src/app/(app)/calendar/page.tsx` now uses backend calendar endpoints.
- `src/app/(app)/history/page.tsx` now uses backend history endpoints.
- `src/app/(app)/settings/page.tsx` now reads/writes backend settings and memory reset.

## Remaining placeholders
- Multi-account provider callback/account-selection UX beyond current single-account flow.
- Calendar conflict generation still seeds fallback conflict when there are no real overlaps yet.
- Graph memory retrieval still uses a skeleton service for snippets while CRUD persistence is active.
