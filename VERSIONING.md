# Versioning Strategy

Neighborhood BBS follows [Semantic Versioning 2.0.0](https://semver.org/).

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

3. Create git tag:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   ```

4. Push to GitHub:
   ```bash
   git push origin main --tags
   ```

5. (Optional) Create GitHub release with release notes

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
