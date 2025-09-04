from __future__ import annotations

from .typing import StoryLike
from ..schema import UXDoc


class UXRole:
    def create_ux_doc(self, story: StoryLike) -> UXDoc:
        title = story.title
        flows = [
            "User logs in",
            f"User navigates to {title}",
            "User completes primary action",
        ]
        states = [
            "loading",
            "empty",
            "error",
            "success",
        ]
        validations = [
            "Required fields must be present",
            "Inputs have basic length/format checks",
        ]
        notes = [
            "Follow brand guidelines",
            "Meet WCAG AA contrast",
        ]
        return UXDoc(
            story_id=story.id,
            title=title,
            flows=flows,
            states=states,
            validations=validations,
            notes=notes,
        )

    def frontend_spec(self, project_name: str | None = None) -> str:
        name = project_name or "Project"
        return f"""# Front-End Spec — {name}

## Principles
- Accessible, performant, consistent, resilient.

## Information Architecture
- Navigation hierarchy, page map, content grouping.

## User Flows
- Primary user journeys with pre/post conditions and variants.

## Components & States
- Component library, states (loading/empty/error/success), skeletons, responsiveness.

## Forms & Validation
- Input patterns, validation rules, error messaging.

## Accessibility
- WCAG AA, keyboard navigation, focus management, ARIA usage.

## Theming & Styles
- Design tokens, layout grid, spacing/typography rules.

## Performance
- Budget, lazy loading, code splitting, caching.

## Testing
- Unit (components), integration (flows), E2E (critical paths), a11y testing.
"""
