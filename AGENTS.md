# Dima Chat — AGENTS.md

## Project
Single-file chat SPA (`index.html`) with persona-driven avatar that changes expression based on conversation context and idle time.

## Key Files
| File | Purpose |
|---|---|
| `DEVELOPMENT_SPEC.md` | Full technical spec — read before implementing |
| `AVATAR_ALGORITHM_SPEC.md` | Avatar state machine logic |
| `replies_mapping.md` | Reply data (id, text, avatar, emotion) |
| `avatars/*.jpeg` | 9 avatar images (avatar_1 through avatar_9) |
| `BUILD_TODO.md` | Build checklist |

## Constraints
- **Strictly one file**: `index.html` — no external dependencies, no CDN links.
- All avatars must be embedded as Base64 Data URIs in a constant `ASSETS`.
- Reply data must be hardcoded from `replies_mapping.md` as `DI_REPLIES` array.
- UI language: **Russian** (all labels, placeholders, prompts).

## Core Mechanics
- **Typewriter**: 200ms per character (5 chars/sec).
- **Idle threshold**: 5 seconds of inactivity → show `avatar_8.jpeg` (Tired).
- **Heartbeat**: check every 100ms.
- **Rapid-fire**: clear typewriter buffer on new message to prevent overlap.

## Helper Scripts
- `python3 parse_replies.py` — generates `DI_REPLIES` JS from `replies_mapping.md`.
- `python3 encode_assets.py` — generates `ASSETS` Base64 object from `avatars/`.
