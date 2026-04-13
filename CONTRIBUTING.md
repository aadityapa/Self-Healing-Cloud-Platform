# Contributing

Thanks for contributing to the Self-Healing Cloud Platform.

## Development Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   - `powershell -ExecutionPolicy Bypass -File .\scripts\install-deps.ps1`
3. Start services:
   - `powershell -ExecutionPolicy Bypass -File .\scripts\start-platform.ps1`

## Code Standards

- Keep changes small and focused.
- Add clear doc updates for behavior changes.
- Ensure `GET /health` stays healthy after your change.
- Prefer safe-by-default automation logic and explicit fallbacks.

## Pull Request Checklist

- [ ] Code builds and runs locally.
- [ ] Updated tests and docs when needed.
- [ ] No secrets or sensitive values committed.
- [ ] Changelog updated for visible user changes.

