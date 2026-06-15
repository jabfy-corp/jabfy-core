# Contributing

## Before You Start

Every contribution must be tied to an existing issue. If no issue exists for your change, open one first using the appropriate issue template.

## Branch Naming

```
<repo>-<issue-number>-<short-description>
```

Available repo prefixes: `core`, `tts`, `voice`, `guard`, `proto`, `mobile`, `desktop`, `web`

Example: `tts-1-wiki-documentation`

Always open an issue before creating a branch.

## Commit Naming

```
<type>: <description>
```

| Type | Use for |
|---|---|
| `feat` | New feature or prototype |
| `fix` | Bug fix |
| `chore` | Maintenance / tooling / CI |
| `docs` | Documentation only |
| `refractor` | Refactoring (no functional change) |
| `test` | Tests only |

Example: `docs: created wiki documentation`

## Pull Requests

Use `Closes #<issue-number>` in the PR body to link to the issue. PRs without a linked issue will fail validation.

## Release Naming

Tag format: `Year.MonthDay.Version` (version starts at 0)

Title format: `Tag-Status`

Available statuses: `pre-release`, `beta` (for stable releases, use only the tag as title)

Example:
- Tag: `2026.324.0`
- Title: `2026.324.0-pre-release`
