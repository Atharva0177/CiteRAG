# Recorded fixture policy

Routine tests replay committed synthetic or redacted responses. They must not call NVIDIA NIM or any other network service.

- Do not place API keys, confidential document text, private questions, or unredacted provider payloads in fixtures.
- Record provider model ID, request shape, status, and relevant response metadata when live procedures are introduced later.
- Live smoke, burst, judge, and load procedures are separate and require explicit opt-in, a reason, and credentials from environment variables.
- `tests/conftest.py` blocks real socket connections for routine tests. Do not disable this guard to make a test pass.
