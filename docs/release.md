# Release

Release workflow runs only for pushed `v*` tags. It builds once, checks artifacts,
creates SHA-256 checksums, uploads one artifact set, creates GitHub Release, and
can publish same files to PyPI. Branch pushes never publish.

## One-time PyPI Trusted Publisher setup

1. Create `ogm-agent-bridge` project on PyPI, or make first release with a PyPI
   project owner if PyPI requires project creation.
2. In PyPI project **Publishing**, add GitHub Trusted Publisher:
   - Owner: `ardiannurcahya`
   - Repository: `ogm-agent-bridge`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. In GitHub repository settings, create environment named `pypi`. Add required
   reviewers if approval before publish is needed.
4. In GitHub repository **Variables**, set `PUBLISH_PYPI` to `true` only after
   Trusted Publisher setup is verified. Without this variable, release creates
   GitHub Release and artifacts but skips PyPI.

Trusted Publishing uses GitHub OIDC `id-token: write`. No PyPI token or repository
secret belongs in GitHub.

## Release process

1. Finish changes. Update `CHANGELOG.md` from `Unreleased` to release version and date.
2. Set `project.version` in `pyproject.toml`. `importlib.metadata` exposes this same version.
3. Run serial local gates:

   ```bash
   uv sync --dev --locked
   uv run ruff format --check .
   uv run ruff check .
   uv run mypy src
   uv run pytest -q
   rm -rf dist
   uv build
   uvx twine check dist/*
   python -m venv /tmp/ogm-wheel-venv
   /tmp/ogm-wheel-venv/bin/pip install dist/*.whl
   /tmp/ogm-wheel-venv/bin/ogm-agent-bridge --version
   rm -rf /tmp/ogm-wheel-venv
   ```

4. Commit changelog and version changes. Push commit through normal review.
5. Create and push matching annotated tag. Version `0.1.0` requires tag `v0.1.0`:

   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

6. Review `Release` workflow. It rejects tag/version mismatch, runs `twine check`,
   generates `SHA256SUMS`, and makes GitHub Release from built artifacts.
7. If `PUBLISH_PYPI=true`, approve `pypi` environment when prompted. PyPI job
   uploads downloaded build artifact; it does not rebuild.
8. Verify GitHub Release checksums and PyPI version. Do not retag changed release.
