# Code Quality Audit

- Semgrep: high=0, medium=0, low=0 (ok)
- Gitleaks: findings=0 (skipped)

## Hotspots (by file count)
- a2a: 21 files
- .: 15 files
- docs/analyst: 13 files
- a2a/roles: 11 files
- docs/proposals: 7 files
- docs: 6 files
- docs/architecture: 5 files
- docs/sprints: 3 files
- features/story-2: 3 files
- docs/data/analytics: 2 files

## Hotspots (by total bytes)
- .: 342281064685 bytes
- a2a: 175355 bytes
- a2a/roles: 23848 bytes
- docs: 9562 bytes
- docs/security/semgrep: 5282 bytes
- docs/analyst: 4555 bytes
- docs/proposals: 4108 bytes
- docs/architecture: 3884 bytes
- docs/integrations: 2546 bytes
- docs/no-tool: 2452 bytes

## Recommendations
- Address high-severity findings before new feature work.
- Rotate and remove any detected secrets immediately.
- Consider stabilization epics for hotspots with significant findings or size.
- Right-size large stories touching hotspots or break them into smaller slices.
