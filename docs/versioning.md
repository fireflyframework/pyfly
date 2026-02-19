# Versioning

PyFly follows the same versioning system as [Spring Boot](https://spring.io/projects/spring-boot), based on **Semantic Versioning** with clearly defined release stages.

---

## Version Format

All PyFly versions follow the `MAJOR.MINOR.PATCH` scheme:

- **MAJOR** — Incompatible API changes
- **MINOR** — New functionality in a backward-compatible manner
- **PATCH** — Backward-compatible bug fixes

Pre-release versions append a stage suffix: `0.2.0-M6`, `0.2.0-RC1`.

---

## Release Stages

Every PyFly release progresses through four stages, from early development to production-ready:

```
SNAPSHOT  →  M1 → M2 → ...  →  RC1 → RC2 → ...  →  GA
  (dev)       (milestones)       (candidates)      (stable)
```

### SNAPSHOT — Development Builds

| | |
|-|-|
| **Format** | `X.Y.Z-SNAPSHOT` (e.g., `0.2.0-SNAPSHOT`) |
| **Stability** | Unstable — may change at any time |
| **Purpose** | Active development toward the next release |
| **Audience** | Framework contributors and early adopters |

SNAPSHOT versions represent the bleeding edge of development. They are rebuilt frequently and should never be used in production.

### Milestone (M) — Feature Previews

| | |
|-|-|
| **Format** | `X.Y.Z-MN` (e.g., `0.1.0-M1`, `0.2.0-M6`) |
| **Stability** | Pre-release — APIs may still change |
| **Purpose** | Feature previews and early feedback |
| **Audience** | Developers evaluating upcoming features |

Each milestone marks a development iteration checkpoint. New features are introduced in milestones and may still be refined based on community feedback. Multiple milestones (M1, M2, M3, ...) are released before a version becomes feature-complete.

### Release Candidate (RC) — Final Testing

| | |
|-|-|
| **Format** | `X.Y.Z-RCN` (e.g., `0.1.0-RC1`, `0.1.0-RC2`) |
| **Stability** | Near-stable — only bug fixes from this point |
| **Purpose** | Final validation before GA |
| **Audience** | Teams preparing for production adoption |

Release candidates are feature-complete. Only bug fixes and documentation improvements are accepted. If no critical issues are found, the RC becomes the GA release.

### GA — General Availability

| | |
|-|-|
| **Format** | `X.Y.Z` (e.g., `0.1.0`, `1.0.0`) |
| **Stability** | Stable — production-ready |
| **Purpose** | Official release for production use |
| **Audience** | All users |

GA releases have undergone thorough testing across all milestones and release candidates. They are the only versions recommended for production environments.

---

## PEP 440 Mapping

Python packaging standards ([PEP 440](https://peps.python.org/pep-0440/)) use a different naming convention for pre-release versions. PyFly uses Spring Boot naming for display and communication, with the following PEP 440 equivalents in `pyproject.toml`:

| PyFly (Spring Boot Style) | PEP 440 (`pyproject.toml`) | Example |
|---------------------------|---------------------------|---------|
| `0.2.0-SNAPSHOT` | `0.2.0.dev1` | Development |
| `0.2.0-M6` | `0.2.0a6` | Milestone 6 |
| `0.2.0-RC1` | `0.2.0rc1` | Release Candidate 1 |
| `0.2.0` (GA) | `0.2.0` | General Availability |

The display version (`__version__` in `pyfly/__init__.py`) uses the Spring Boot format (`0.2.0-M6`), which is what you see in the startup banner, CLI output, and admin dashboard. The `pyproject.toml` version uses PEP 440 format for compatibility with Python packaging tools (pip, uv, hatchling).

---

## Version History

| Version | Date | Stage | Highlights |
|---------|------|-------|------------|
| `0.2.0-M6` | 2026-02-19 | Milestone | ASGI pathsend extension fix for Granian |
| `0.2.0-M5` | 2026-02-19 | Milestone | Auto-configuration audit (8 new auto-config classes), stdlib logging fallback, post-processor deduplication |
| `0.2.0-M4` | 2026-02-18 | Milestone | Admin dashboard overhaul, pure ASGI middleware (anyio fix), built-in metrics, bean categories, mapping/trace/logger enhancements |
| `0.2.0-M3` | 2026-02-18 | Milestone | Clean server startup, graceful shutdown, admin dashboard enhancements, mypy strict compliance |
| `0.2.0-M2` | 2026-02-18 | Milestone | Application server architecture, FastAPI adapter, Granian/Hypercorn support |
| `0.1.0-M6` | 2026-02-18 | Milestone | Web archetype, `@controller`, admin log viewer, cache introspection |
| `0.1.0-M5` | 2026-02-17 | Milestone | Transactional engine (SAGA + TCC), saga composition |
| `0.1.0-M4` | 2026-02-17 | Milestone | Admin dashboard, CLI archetype, shell subsystem |
| `0.1.0-M3` | 2026-02-15 | Milestone | Spring Data refactoring, MongoDB support, CLI wizard revamp |
| `0.1.0-M2` | 2026-02-15 | Milestone | Lifecycle protocol, fail-fast startup, config loading |
| `0.1.0-M1` | 2026-02-14 | Milestone | Initial release — 27 modules across all layers |

See **[CHANGELOG.md](../CHANGELOG.md)** for detailed release notes.

---

## Checking Your Version

**Python code:**

```python
import pyfly
print(pyfly.__version__)  # e.g., "0.2.0-M6"
```

**CLI:**

```bash
pyfly info
```

**Startup banner:**

```
                _____.__
______ ___.__._/ ____\  | ___.__.
\____ <   |  |\   __\|  |<   |  |
|  |_> >___  | |  |  |  |_\___  |
|   __// ____| |__|  |____/ ____|
|__|   \/                 \/

:: PyFly Framework :: (v0.2.0-M6) (Python 3.13.9)
Copyright 2026 Firefly Software Solutions Inc. | Apache License 2.0
```

**Admin dashboard:**

The current framework version is displayed in the admin dashboard overview page and footer.
