# apps/ — intentionally-vulnerable training targets

Each subdirectory is a standalone Gradle Android project whose APK backs one or
more curriculum tasks. **These apps are deliberately insecure** — that's the
point. They contain no real user data and target no real backend.

| App | Package | Backs task | Vulnerability |
|-----|---------|-----------|---------------|
| `securenotes` | `org.masdojo.securenotes` | 001 (static_assert) | Hardcoded API key in the APK |
| `pulse` | `org.masdojo.pulse` | 005 (network_assert) | Cleartext telemetry token over HTTP |
| `vaultguard` | `org.masdojo.vaultguard` | 009 (frida_assert) | Client-side root check gating a feature |
| `vaultbank` | `org.masdojo.vaultbank` | all (practice target) | **All-in-one** — bundles every technique in one banking app (see [`vaultbank/README.md`](vaultbank/README.md)) |

`vaultbank` is the Damn-Vulnerable-Bank-style target: a single installable
`MASDojo.apk` covering the whole syllabus, offered for download from the
dashboard once built.

## Building

You need a JDK 17 and the Android SDK (the runner image already has both). From
the repo root:

```bash
infra/build-apps.sh                 # build all apps -> tasks/*/app/target.apk
infra/build-apps.sh securenotes     # build just one
infra/build-apps.sh vaultbank       # the all-in-one target -> apps/vaultbank/MASDojo.apk
```

Each app uses the Gradle wrapper if present, otherwise a system `gradle`. The
build script copies the resulting debug APK to the matching task package.
