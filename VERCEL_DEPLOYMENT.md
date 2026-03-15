# Vercel Deployment Configuration

## Overview

This document describes the Vercel deployment configuration for the Neighborhood BBS Flask application.

## Files Added

### `vercel.json`
- **Version**: 2 (Vercel's latest schema)
- **Runtime**: Python 3.11
- **Output Directory**: `api` (where the serverless function builds)
- **Static Assets**: `server/web/static`

### `api/index.py`
- Entry point for Vercel's serverless environment
- Imports and exports the Flask app
- Handles all routing through the Flask application

## Configuration Details

### Builds
- **Source**: `api/index.py` - The Flask app entry point
- **Builder**: `@vercel/python` - Vercel's Python runtime
- **Runtime**: Python 3.11
- **Max Lambda Size**: 15MB

### Routes
1. **Static Assets** (`/static/*`): Served from `server/web/static`
2. **All Other Routes** (`/*`): Handled by `api/index.py` (Flask app)

### Environment Variables
- `PYTHONUNBUFFERED=1` - Ensures Python output is flushed immediately

## Deployment Steps

### Prerequisites
1. Python 3.11+ installed locally
2. All dependencies in `requirements.txt`
3. Git configured and committed

### Local Testing Before Deploy
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1

# Install Vercel CLI
npm install -g vercel

# Test locally
vercel dev

# Run tests
pytest server/src/test_audit_log_phase4_w11.py -v
```

### Deploy to Vercel
```bash
# Login to Vercel
vercel login

# Deploy
vercel --prod

# Or just:
vercel
```

### Environment Variables on Vercel Dashboard
Set these in Vercel project settings:
- `ADMIN_PASSWORD`: Your admin password
- `CORS_ORIGINS`: Allowed CORS origins
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: (if using remote DB)
- `DEBUG`: `false` (for production)

## File Structure
```
Neighborhood_BBS/
├── api/
│   └── index.py                    # Vercel entry point
├── server/
│   ├── src/
│   │   ├── server.py              # Flask app factory
│   │   ├── models.py              # Database models
│   │   └── ...
│   └── web/
│       ├── static/                # Static assets (CSS, JS, images)
│       └── templates/             # HTML templates
├── vercel.json                     # Vercel configuration
└── requirements.txt                # Python dependencies
```

## Troubleshooting

### "No Output Directory named dist found"
- ✅ Fixed by setting `outputDirectory: "api"` in vercel.json
- The `api` directory contains the built Python function

### Import Errors
- Ensure `sys.path` in `api/index.py` correctly references `server/src`
- Check that all Python modules are importable from that path

### Database Issues
- Use persistent storage (not /tmp, as Vercel lambdas are ephemeral)
- Consider using a cloud database like PostgreSQL on Railway/Render
- Current SQLite database works locally but not in serverless

### Static Files Not Loading
- Verify `server/web/static` directory exists and contains assets
- Check routes in `vercel.json` for correct `/static/(.*)`pattern

## Production Considerations

### For Production Deployment:

1. **Database**: Move from SQLite to cloud PostgreSQL
   ```python
   # Update models.py to use PostgreSQL instead of SQLite
   DATABASE_URL = os.environ.get('DATABASE_URL')
   ```

2. **Security**:
   - Use strong `SECRET_KEY` from environment only
   - Enable `SESSION_COOKIE_SECURE = True`
   - Set correct CORS origins

3. **Rate Limiting**:
   - Current rate limiter works in serverless
   - Consider Redis for distributed rate limiting

4. **Logging**:
   - Logs go to Vercel's dashboard
   - Set up log aggregation if needed

5. **Performance**:
   - Cold start time ~2-3 seconds for Python lambdas
   - Consider upgrading to Pro plan for better performance

## Related Files
- `requirements.txt` - All Python dependencies
- `server/src/server.py` - Flask application factory
- `server/src/models.py` - Database models
- `.env.example` - Environment variables template

## Next Steps
1. Commit `vercel.json` and `api/index.py` to GitHub
2. Push to your repository
3. Connect repository to Vercel project
4. Set environment variables in Vercel dashboard
5. Deploy with `vercel --prod`

For more information, visit: https://vercel.com/docs/concepts/functions/serverless-functions
