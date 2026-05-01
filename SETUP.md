# Setup & Deployment Guide

Once you have internet connectivity, follow these steps to deploy and test the application.

## Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `fastapi` - Modern Python web framework
- `uvicorn` - ASGI server for running FastAPI
- `httpx` - Async HTTP client for API calls
- `python-dotenv` - Load environment variables from .env
- `pydantic` - Data validation and settings management
- `aiofiles` - Async file operations (for future features)

## Step 2: Set Up Hugging Face API Key

1. Go to https://huggingface.co/settings/tokens
2. Generate a new API token (free tier available)
3. Copy the token
4. Edit `backend/.env` and replace `your_huggingface_api_key_here` with your actual token:
   ```
   HF_API_KEY=hf_YOUR_ACTUAL_TOKEN_HERE
   ```
5. **Never commit `.env` to git** - it's already in `.gitignore`

## Step 3: Start the Backend Server

```bash
cd backend
uvicorn main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Application startup complete
```

Test the backend:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","service":"Political Text Analysis API"}
```

## Step 4: Install Frontend Dependencies

In a **new terminal**:

```bash
cd client
npm install
```

This installs:
- `react` & `react-dom` - UI framework
- `axios` - HTTP client for API calls
- `tailwindcss` - CSS framework
- `autoprefixer` & `postcss` - CSS processing
- `react-scripts` - Build and dev tools

## Step 5: Start the Frontend Development Server

```bash
npm start
```

Expected output:
```
Compiled successfully!

You can now view political-text-analyzer in the browser.

  Local:            http://localhost:3000
```

The app should automatically open in your default browser.

## Step 6: Full System Test

### Test 1: Health Check
1. Keep both servers running
2. Look for green "Connected" badge in top-right of app
3. Frontend should show backend status

### Test 2: Basic Analysis
1. Paste a short political text (50-100 words) in the textarea
2. Click "Analyze Text"
3. Wait 3-5 seconds for results
4. Verify you see:
   - Tone card (POSITIVE/NEGATIVE with confidence)
   - Bias card (NONE/LOW/MEDIUM/HIGH with score)
   - Summary card (3-4 line summary)

### Test 3: Edge Cases
1. **Long text**: Paste 2000+ words → should see truncation warning
2. **Empty input**: Click analyze → button should be disabled
3. **Character limit**: Type 5000+ chars → warning banner + auto-truncation
4. **Copy buttons**: Click "Copy Result" → should show "✓ Copied"
5. **Responsive design**: Resize browser → verify card layout changes

### Test 4: Error Handling
1. **Backend down**: Stop uvicorn → frontend should show "Connecting..." in header
2. **Invalid API key**: Change HF_API_KEY in .env → try analysis → error message
3. **Rate limit**: Submit 30+ requests in 60 seconds → should see 429 error, then auto-retry
4. **Retry button**: On error, click "Retry" → should attempt analysis again

## Step 7: Build for Production

### Backend
```bash
# Install production ASGI server
pip install gunicorn

# Run with production settings (4 workers, no reload)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Frontend
```bash
npm run build
# Creates optimized production build in 'client/build/'
# Ready to deploy to Vercel, Netlify, or static host
```

## Common Issues & Solutions

### "Connection failed" Error
**Problem**: Frontend can't reach backend
**Solution**:
- Verify backend is running on http://localhost:8000
- Check REACT_APP_API_URL in `client/.env` is correct
- Check CORS settings in `backend/main.py`

### "Invalid HF_API_KEY" Error
**Problem**: Your Hugging Face token is invalid or expired
**Solution**:
- Generate a new token at https://huggingface.co/settings/tokens
- Update `backend/.env` with the new token
- Restart the backend server

### Models Take 30+ Seconds on First Request
**Problem**: Hugging Face free tier puts models to sleep after ~30 min
**Solution**:
- This is normal behavior - first request loads the model
- Subsequent requests will be fast (3-5s)
- No action needed, just wait

### "Rate limit exceeded" (429 error)
**Problem**: You've made too many requests too quickly
**Solution**:
- The app automatically retries with exponential backoff
- Wait 60+ seconds before making new requests
- Consider Hugging Face Pro for higher limits

### Frontend Looks Plain (No Tailwind Styles)
**Problem**: Tailwind CSS not compiling
**Solution**:
```bash
cd client
npm install  # Ensure tailwindcss is installed
npm start    # Restart dev server
```

### "React not defined" or Module Errors
**Problem**: Missing dependencies or corrupted node_modules
**Solution**:
```bash
cd client
rm -rf node_modules package-lock.json
npm install
npm start
```

## Performance Optimization Tips

### Backend
1. **Use flan-t5-large** (not base) for better bias detection
2. **Enable caching** for repeated texts using Redis (future enhancement)
3. **Batch requests** for high throughput (see `/analyze-batch` endpoint)
4. **Monitor token usage** on Hugging Face to optimize costs

### Frontend
1. **Debounce textarea input** (already implemented in AnalysisForm)
2. **Memoize components** with React.memo() for large result sets
3. **Lazy load images** (if added)
4. **Minify CSS** with Tailwind purge (automatic in production build)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Browser                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ React Frontend (http://localhost:3000)              │   │
│  │ - Textarea input with validation                    │   │
│  │ - Result cards with color-coded analysis            │   │
│  │ - Loading spinner & error handling                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────┬──────────────────────────────────────────┘
                  │ POST /analyze
                  │ (JSON request/response)
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Backend                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ main.py                                              │   │
│  │ - CORS configuration                                │   │
│  │ - Pydantic models & validation                       │   │
│  │ - /analyze endpoint (main entry point)              │   │
│  │ - Error handling & logging                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ services/                                            │   │
│  │ ├── hf_client.py (Async API calls + retries)       │   │
│  │ ├── output_parser.py (Parse & validate outputs)     │   │
│  │ └── text_manager.py (Text truncation)              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ prompts.py                                           │   │
│  │ - Few-shot bias detection prompt                    │   │
│  │ - Chain-of-thought reasoning prompt                 │   │
│  │ - Direct classification prompt                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────┬──────────────────────────────────────────┘
                  │ Parallel async calls
                  ├─→ GET /models/{distilbert}/...
                  ├─→ GET /models/{bart}/...
                  └─→ GET /models/{flan-t5}/...
                  ↓
       ┌──────────────────────────┐
       │ Hugging Face Inference   │
       │ API (api.huggingface.co) │
       │                          │
       │ Models:                  │
       │ - distilbert (sentiment) │
       │ - BART (summarization)   │
       │ - FLAN-T5 (bias)         │
       └──────────────────────────┘
```

## Scaling Considerations

For production use:

1. **Load Balancing**: Deploy multiple FastAPI instances behind Nginx
2. **Caching**: Add Redis for frequently analyzed texts
3. **Database**: Store analysis history in PostgreSQL
4. **Async Workers**: Increase Gunicorn workers based on CPU cores
5. **API Rate Limiting**: Implement Redis-backed rate limiter
6. **Monitoring**: Add Prometheus/Grafana for metrics
7. **Logging**: Centralize logs with ELK stack or CloudWatch

## Next Steps

1. ✅ Install all dependencies (backend + frontend)
2. ✅ Set up HF API key
3. ✅ Start both servers
4. ✅ Test basic analysis flow
5. ✅ Verify error handling works
6. ✅ Test responsive design on mobile
7. 🚀 Ready for production deployment!

---

For detailed API documentation, visit http://localhost:8000/docs (FastAPI Swagger UI)
