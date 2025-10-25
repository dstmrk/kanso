# Contributing to Kanso

Thank you for considering contributing to Kanso! We welcome contributions from the community.

## Quick Links

📖 **[Full Contributing Guide](https://dstmrk.github.io/kanso/contributing/)** - Complete documentation with detailed guidelines

## Quick Start

1. **Fork and clone** the repository
2. **Set up your environment**:
   ```bash
   uv sync
   ```
3. **Make your changes** on a feature branch
4. **Run tests**:
   ```bash
   pytest -m "not e2e"  # Unit tests
   uv run mypy app --ignore-missing-imports
   uv run ruff check .
   ```
5. **Submit a Pull Request**

## Development Workflow

- **Branch naming**: `feature/your-feature` or `fix/your-fix`
- **Commit messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
- **Tests**: Add tests for new features
- **E2E tests**: Include `[e2e]` in commit message to trigger E2E CI

## Questions?

- **Issues**: [GitHub Issues](https://github.com/dstmrk/kanso/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dstmrk/kanso/discussions)

For detailed guidelines, code style, testing practices, and more, see the **[full documentation](https://dstmrk.github.io/kanso/contributing/)**.
