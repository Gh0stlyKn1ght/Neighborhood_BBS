# Release Checklist

Use this checklist for every release tag push.

## 1. Scope and Branch Hygiene

- [ ] Release changes are merged to `main`
- [ ] Working tree is clean (`git status`)
- [ ] No unresolved TODOs or known blockers for this release

## 2. Validation

- [ ] Core tests pass locally (`pytest server/tests/`)
- [ ] Security tests pass (`python test_security_fixes.py`)
- [ ] Endpoint tests pass (`python test_endpoints.py`)
- [ ] Installer scripts pass syntax checks (`bash -n` on setup scripts)

## 3. Documentation and Versioning

- [ ] `CHANGELOG.md` updated with release notes
- [ ] `VERSIONING.md` policy still accurate
- [ ] Installer and setup docs reflect current paths under `devices/`

## 4. Tag Selection

Choose one release channel:

- Stable release tag: `vMAJOR.MINOR.PATCH`
  - Example: `v1.6.0`
- Unstable prerelease tag: `vMAJOR.MINOR.PATCH-alpha.N`, `-beta.N`, or `-rc.N`
  - Example: `v1.7.0-rc.1`

## 5. Tag and Publish

- [ ] Create annotated tag

```bash
git tag -a v1.6.0 -m "Stable release 1.6.0"
```

or

```bash
git tag -a v1.7.0-rc.1 -m "Release candidate 1 for 1.7.0"
```

- [ ] Push tag

```bash
git push origin <tag>
```

- [ ] Confirm GitHub Actions created the Release automatically
- [ ] Confirm prerelease flag is correct for alpha/beta/rc tags

## 6. Post-Release

- [ ] Smoke-test deployment from the tagged release
- [ ] Announce release notes to contributors/users
- [ ] Open follow-up issues for deferred work
