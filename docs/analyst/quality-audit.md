# Code Quality Audit

- Semgrep: high=0, medium=0, low=0 (ok)
- Gitleaks: findings=0 (skipped)

## Hotspots (by file count)
- a2a: 20 files
- .: 14 files
- docs/analyst: 12 files
- a2a/roles: 11 files
- docs/proposals: 7 files
- docs: 6 files
- docs/architecture: 5 files
- scripts: 4 files
- docs/sprints: 3 files
- features/story-2: 3 files

## Hotspots (by total bytes)
- .: 8883430 bytes
- a2a: 114923 bytes
- a2a/roles: 16932 bytes
- docs: 8908 bytes
- scripts: 7151 bytes
- examples: 6046 bytes
- docs/security/semgrep: 5174 bytes
- docs/proposals: 4108 bytes
- docs/architecture: 3884 bytes
- docs/analyst: 3834 bytes

## Recommendations
- Address high-severity findings before new feature work.
- Rotate and remove any detected secrets immediately.
- Consider stabilization epics for hotspots with significant findings or size.
- Right-size large stories touching hotspots or break them into smaller slices.
