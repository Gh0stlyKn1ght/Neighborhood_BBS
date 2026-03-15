# Neighborhood BBS - Development Guide

## Project Overview

Neighborhood BBS consists of several components:

1. **Backend Server** - Flask-based REST API with WebSocket support
2. **Frontend** - Web interface for chat and board
3. **Firmware** - MicroPython for ESP8266 and Zima Board
4. **Database** - SQLite for data persistence

## Architecture

```
┌─────────────────────────────────────┐
│         Web Browser/Client          │
└────────────────┬────────────────────┘
                 │
        ┌────────▼────────┐
        │  WebSocket/HTTP │
        └────────┬────────┘
                 │
    ┌────────────▼────────────┐
    │   Flask Server (main)   │
    │  - Routes               │
    │  - SocketIO handlers    │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   Module Layer (chat/   │
    │    board)               │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   Database (SQLite)     │
    └─────────────────────────┘
```

## Environment Setup

### 1. Python Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### 3. Environment Variables

Create `.env` file:

```env
FLASK_APP=server/src/main.py
FLASK_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///data/neighborhood.db
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test file
pytest tests/test_chat.py

# Run with verbose output
pytest -v tests/
```

### Code Quality

```bash
# Format code with Black
black src/

# Sort imports
isort src/

# Lint with flake8
flake8 src/

# Type check with mypy
mypy src/

# Run all checks
black src/ && isort src/ && flake8 src/ && mypy src/
```

### Running Dev Server

```bash
cd src
python main.py --debug
```

Server runs on `http://localhost:8080`

### Database Management

```bash
# Create/initialize database
python server/scripts/init_db.py

# Run migrations
python scripts/migrate.py

# Reset database (DANGEROUS!)
python scripts/reset_db.py
```

## Adding New Features

### 1. Create New Module

For new functionality, create a new package:

```bash
mkdir src/mynewfeature
touch src/mynewfeature/__init__.py
touch src/mynewfeature/routes.py
touch src/mynewfeature/models.py
```

### 2. Add Routes

In `src/mynewfeature/routes.py`:

```python
from flask import Blueprint, jsonify

mynewfeature_bp = Blueprint('mynewfeature', __name__, url_prefix='/api/mynewfeature')

@mynewfeature_bp.route('/endpoint', methods=['GET'])
def endpoint():
    return jsonify({'result': 'ok'})
```

### 3. Register Blueprint

In `src/server.py`, add:

```python
from mynewfeature.routes import mynewfeature_bp
app.register_blueprint(mynewfeature_bp)
```

### 4. Write Tests

Create `tests/test_mynewfeature.py`:

```python
import pytest

def test_mynewfeature_endpoint(client):
    response = client.get('/api/mynewfeature/endpoint')
    assert response.status_code == 200
    assert response.json['result'] == 'ok'
```

### 5. Document

Update relevant documentation files.

## Debugging

### Using Flask Debugger

```python
# In your code
from flask import current_app
current_app.logger.debug('Debug message')
```

### Using pdb

```python
import pdb; pdb.set_trace()
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)
logger.info('Info message')
logger.error('Error message')
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my amazing feature"

# Push to fork
git push origin feature/my-feature

# Create pull request on GitHub
```

## Documentation

### Code Comments

- Write clear, concise comments
- Document complex logic
- Include examples where helpful

### Docstrings

```python
def my_function(param1, param2):
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is invalid
    """
    pass
```

## Performance Tips

1. Use database indexes for frequently queried fields
2. Cache expensive computations
3. Optimize database queries
4. Use pagination for large result sets
5. Profile code with cProfile

## Common Issues

### ModuleNotFoundError

Ensure you're in the correct directory and have activated the virtual environment.

### Port Already in Use

```bash
# Find process
lsof -i :8080

# Kill process
kill -9 <PID>
```

### Database Locks

Try running:

```python
python scripts/reset_db.py
```

## Resources

- Flask: https://flask.palletsprojects.com/
- SocketIO: https://python-socketio.readthedocs.io/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Flask-RESTful: https://flask-restful.readthedocs.io/

## Getting Help

- Check existing issues on GitHub
- Create a new issue with details
- Read existing documentation
- Join our community discussions

