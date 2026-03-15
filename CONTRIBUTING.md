# Contributing to Neighborhood BBS

Thank you for considering contributing to Neighborhood BBS! 🎉

We welcome contributions from everyone. Here's how you can help:

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/Neighborhood_BBS.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

## Development Workflow

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use Black for code formatting: `black src/`
- Use isort for import sorting: `isort src/`
- Lint with flake8: `flake8 src/`

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=src  # With coverage
```

### Git Commit Messages

- Use clear, descriptive commit messages
- Reference issues when relevant: "Fixes #123"
- Use present tense: "Add feature" not "Added feature"
- Limit to 72 characters for first line

### Submitting Changes

1. Push your branch: `git push origin feature/your-feature-name`
2. Create a Pull Request with a clear description
3. Ensure all tests pass and code quality checks pass
4. Wait for review and address feedback

## Reporting Bugs

Found a bug? Please create an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Screenshots if applicable

## Feature Requests

Have an idea? We'd love to hear it!
- Describe the feature clearly
- Use cases and benefits
- Any potential implementation approaches

## Questions?

- Open an issue with the "question" label
- Check existing documentation first
- Ask in our community chat

## Code of Conduct

- Be respectful and inclusive
- Assume good intentions
- Provide constructive feedback
- No harassment or discrimination

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thanks for making Neighborhood BBS better! 💙
