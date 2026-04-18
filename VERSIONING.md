# Versioning Strategy

Neighborhood BBS follows [Semantic Versioning 2.0.0](https://semver.org/).

## Release Channels

This repository uses two release channels with Git tags:

- Stable channel: production-ready releases
   - Tag format: `vMAJOR.MINOR.PATCH`
   - Example: `v1.4.2`
- Unstable channel: pre-release builds for testing
   - Tag format: `vMAJOR.MINOR.PATCH-alpha.N`, `vMAJOR.MINOR.PATCH-beta.N`, or `vMAJOR.MINOR.PATCH-rc.N`
   - Examples: `v1.5.0-alpha.1`, `v1.5.0-beta.2`, `v1.5.0-rc.1`

Rules:

- Never move or retag an existing version tag.
- Stable tags only come from validated code on `main`.
- Unstable tags are marked as pre-releases in GitHub Releases.

## Version Format

```
MAJOR.MINOR.PATCH
```

- **MAJOR** - Breaking changes (incompatible API changes)
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

## Examples

- `1.0.0` - Initial production release
- `1.1.0` - Added new feature (backward compatible)
- `1.1.1` - Fixed bug
- `2.0.0` - Breaking changes (major version bump)

## Current Version

**1.0.0** - Production ready release

## Release Process

1. Update version in:
   - `setup.py` (version field)
   - `CHANGELOG.md` (add new section)

2. Commit with message:
   ```bash
   git commit -m "Release: v1.0.0"
   ```

3. Create git tag (stable):
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   ```

   Or create an unstable pre-release tag:
   ```bash
   git tag -a v1.1.0-rc.1 -m "Release candidate 1 for 1.1.0"
   ```

4. Push to GitHub:
   ```bash
   git push origin main --tags
   ```

5. GitHub Actions publishes a release automatically when a `v*` tag is pushed.
   - Tags containing `-alpha.`, `-beta.`, or `-rc.` are published as pre-releases.
   - Stable tags are published as full releases.

## Next Releases

- `1.0.1` - Bug fixes and patches
- `1.1.0` - New features (chat improvements, etc.)
- `1.2.0` - Admin panel and user management
- `2.0.0` - Major refactor or breaking changes

## Changelog Format

See [CHANGELOG.md](CHANGELOG.md) for format and examples.

## Deprecation Policy

- Deprecated features get 2 minor versions warning
- Removed in 3rd minor version or next major version

Example:
- `1.5.0` - Feature marked as deprecated
- `1.6.0` - Feature still works, deprecation warning
- `1.7.0` or `2.0.0` - Feature removed
