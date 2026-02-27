# GitHub Actions CI/CD for C++ (Step-by-Step)

This guide helps you stand up CI/CD for a C++ project in small, practical steps.

## 1) Start with CI first (not deployment)

Focus on getting these green on every PR:

- Build
- Test
- (Optional) formatting + static checks

Once CI is stable, add CD (releases/artifacts/deployments).

---

## 2) Prerequisites in your C++ repo

Before Actions, ensure your project can run these locally:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

If these commands are reliable locally, CI setup is straightforward.

---

## 3) Add a minimal workflow

Create `.github/workflows/cpp-ci.yml` with:

- Trigger on `pull_request`
- Trigger on `push` to `main`
- Checkout code
- Configure + build + test

A starter workflow is already included in this repo.

---

## 4) Use a matrix for confidence

Start with:

- Ubuntu + GCC
- Ubuntu + Clang

Later expand to:

- Windows + MSVC
- macOS + AppleClang

This catches compiler-specific issues early.

---

## 5) Add quality gates

Recommended checks:

- `clang-format` (formatting)
- `clang-tidy` (static analysis)
- Sanitizer builds (`-fsanitize=address,undefined`) in a dedicated job

Set branch protection so PRs must pass checks.

---

## 6) Add caching and dependencies

If you use package managers:

- `vcpkg`
- `conan`
- apt-installed libs

Add cache steps for dependency directories to reduce CI runtime.

---

## 7) Introduce CD after CI is stable

Common C++ CD options:

- Upload build artifacts from CI runs
- Publish release binaries when pushing tags like `v1.2.3`
- Build and publish Docker image (if applicable)

Trigger CD on:

- `push` tags
- `workflow_dispatch` for manual release

---

## 8) Security and maintenance basics

- Store credentials in GitHub Actions Secrets
- Keep `permissions` minimal in workflow files
- Pin major action versions (e.g. `actions/checkout@v4`)
- Keep workflows small; split CI and release workflows

---

## 9) Step-by-step adoption plan (recommended)

1. Add build + test on Ubuntu only.
2. Add compiler matrix (GCC + Clang).
3. Add formatting check.
4. Add static analysis.
5. Add sanitizer job.
6. Add release workflow for tags.
7. Enforce required checks in branch protection.

This staged approach avoids overwhelm and keeps feedback tight.

---

## 10) Next customization checklist

When you are ready, tailor the workflow for your project:

- Build system: CMake/Make/Bazel
- Test framework: GoogleTest/Catch2/etc.
- External dependencies
- Supported OS/compiler matrix
- Release artifact naming/versioning

If you share your project structure (`CMakeLists.txt`, test layout, dependencies), you can generate a production-ready CI + release setup.
