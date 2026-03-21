# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **video-generator** (1127 symbols, 2685 relationships, 86 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/video-generator/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/video-generator/context` | Codebase overview, check index freshness |
| `gitnexus://repo/video-generator/clusters` | All functional areas |
| `gitnexus://repo/video-generator/processes` | All execution flows |
| `gitnexus://repo/video-generator/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

- Re-index: `npx gitnexus analyze`
- Check freshness: `npx gitnexus status`
- Generate docs: `npx gitnexus wiki`

<!-- gitnexus:end -->

---

# Project Guide

## Build & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 15321

# Or run directly
cd src/api && python main.py
```

API will be available at `http://localhost:15321`. FastAPI auto-generates interactive docs at `/docs`.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_file_management.py -v

# Run tests by keyword
pytest tests/ -v -k "upload"

# Run with coverage
pytest tests/ -v --cov=src
```

## Architecture Overview

### Layered Structure

```
src/
├── api/
│   └── main.py          # FastAPI app, routes, request/response models
├── services/            # Business logic layer
│   ├── file_service.py  # File upload/download/management
│   ├── task_service.py  # Async task queue management
│   ├── video_service.py # Video processing (MoviePy/FFmpeg)
│   ├── audio_service.py # TTS/ASR audio processing
│   ├── ai_video_service.py  # Sora/third-party AI video
│   ├── script_service.py    # AI script generation
│   ├── storyboard_service.py # Script to storyboard conversion
│   ├── batch_service.py     # Batch job orchestration
│   ├── quota_service.py     # User quota management
│   ├── dashboard_service.py # Dashboard statistics
│   ├── template_service.py  # Template management
│   ├── material_service.py  # Music/template library
│   └── system_service.py    # System health/info
├── models/              # Pydantic models (quota.py, etc.)
└── video_generator.py   # Legacy video processing module
```

### Request Flow

```
HTTP Request → FastAPI Route → Service Layer → Async Task Queue → Background Worker
                    ↓                                              ↓
              Response (202 Accepted)                    Task Status Update
                    ↓                                              ↓
              taskId returned                            FileService → Storage
```

### Key Design Patterns

1. **Async Task Queue**: Long-running operations (video processing, AI generation) return `202 Accepted` with `taskId`. Clients poll `GET /api/v1/tasks/{taskId}` for status.

2. **Service Layer**: Each module has a dedicated service class with dependency injection (e.g., `VideoService(file_service=..., task_service=...)`).

3. **File Abstraction**: `FileService` provides unified storage interface. Files stored in `uploads/` with UUID-based naming.

4. **Pipeline Processing**: `VideoService.process_pipeline()` chains multiple operations (add_music → add_voiceover → add_subtitles) atomically.

## API Modules

| Module | Endpoints | Description |
|--------|-----------|-------------|
| `/api/v1/files/*` | 6 | File upload, download, list, delete |
| `/api/v1/video/*` | 8 | Video processing (concat, overlay, music, subtitles) |
| `/api/v1/audio/*` | 2 | TTS voiceover, ASR subtitle generation |
| `/api/v1/tasks/*` | 3 | Task status query, cancellation |
| `/api/v1/ai/script/*` | 5 | AI script generation, expansion |
| `/api/v1/ai/video/*` | 4 | Sora/third-party AI video |
| `/api/v1/ai/batch/*` | 4 | Batch drama generation |
| `/api/v1/quota/*` | 5 | User quota management |
| `/api/v1/templates/*` | 5 | Template CRUD and apply |
| `/api/v1/materials/*` | 5 | Music/template library |
| `/api/v1/dashboard/*` | 2 | Dashboard statistics |
| `/api/v1/system/*` | 2 | Health check, system info |

## Service Dependencies

```
FileService (core)
    ↓
TaskService → Async queue (in-memory)
    ↓
VideoService ──→ MoviePy + FFmpeg
AudioService ──→ Edge TTS + Aliyun ASR
AIVideoService ─→ Sora API / Third-party
ScriptService ──→ GPT API
StoryboardService ─→ GPT API
BatchService ──→ Orchestrates all above
QuotaService ──→ SQLite database
```

## Data Storage

| Data | Storage | Location |
|------|---------|----------|
| Uploaded files | Filesystem | `uploads/` |
| Output videos | Filesystem | `uploads/outputs/` |
| Task metadata | In-memory (dict) | Lost on restart |
| Quota data | SQLite | `data/quota.db` |
| Scripts/Storyboards | JSON files | `data/scripts/`, `data/storyboards/` |
| Templates | JSON files | `data/templates/` |

## Common Development Tasks

### Add a new API endpoint

1. Add route in `src/api/main.py`
2. Create request/response Pydantic models
3. Implement service method in corresponding `src/services/*.py`
4. Add error codes to `ERROR_CODES` dict
5. Write tests in `tests/test_*.py`

### Add a new service

1. Create `src/services/new_service.py`
2. Instantiate in `src/api/main.py`
3. Inject dependencies via constructor

### Debug a failing task

1. Check task status: `GET /api/v1/tasks/{taskId}`
2. Review logs in `logs/` (if loguru configured)
3. Use `gitnexus_query({query: "task failure"})` to find related flows
4. Run unit test: `pytest tests/test_*.py -v -k <test_name>`

## Dependencies

```
# Core
moviepy==1.0.3
ffmpeg-python>=0.2.0
pydub>=0.25.1
pysubs2>=0.2.4

# Web
fastapi
uvicorn
python-multipart

# AI/ML
edge-tts>=6.0.0
aliyun-python-sdk-core>=2.13.0

# Utilities
numpy>=1.24.0
opencv-python>=4.8.0
pillow>=10.0.0
pyyaml>=6.0
loguru>=0.7.0
click>=8.1.0
```

## Environment Variables

No environment variables currently required. API keys for third-party services (Sora, Aliyun, GPT) should be configured in service classes directly or via `.env` file (not yet implemented).

## Known Limitations

1. **In-memory task queue**: Tasks are lost on server restart. Consider Redis integration for persistence.
2. **No authentication**: v3.1 removed auth. Re-add if deploying publicly.
3. **Single-node only**: No distributed processing support.
4. **GPU acceleration**: Not configured by default. Install `nvidia-cuda-toolkit` for hardware encoding.
