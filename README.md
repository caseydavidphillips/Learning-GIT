# Hello Git and GitHub

### This is a practical test for working on my:

1. **GitHub** skills
2. practically testing **CI/CD** pipelines.
3. Test building and deploying websites like this one: [Excursion](https://caseydavidphillips.github.io/Learning-GIT/excursion/)

## New CI/CD learning resources

- Step-by-step C++ GitHub Actions guide: [Project Docs](docs/github-actions-cpp-guide.md)
- Starter workflow: `.github/workflows/cpp-ci.yml`


## Testing

- Unit tests are registered with CTest and run in CI via `.github/workflows/cpp-ci.yml`.
- Test runs now produce a JUnit XML file at `build/test-results/reelocator-unit.xml` and an HTML dashboard at `build/test-results/report.html`.
- Run locally with:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python3 testing/generate_test_report.py build/test-results/reelocator-unit.xml --output build/test-results/report.html
```
