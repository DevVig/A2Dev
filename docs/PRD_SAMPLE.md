# Product Requirements Document (Sample)

## Authentication

Overview
Users must sign in to access their dashboard and personalized data.

### Stories
- As a user, I can sign up with email and password.
- As a user, I can sign in and sign out.
- As a user, I can reset my password via email.

### Acceptance
- Passwords must be at least 12 characters.
- Sign‑in should lock after 5 failed attempts.
- Reset link expires after 30 minutes.

## Dashboard

Overview
Signed‑in users see a summary of their data and quick actions.

### Stories
- As a user, I can view key metrics for the last 7 days.
- As a user, I can filter metrics by date range.

### Acceptance
- Loading state appears while data fetches.
- Empty state explains no data conditions.

