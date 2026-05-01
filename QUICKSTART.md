# ⚡ Quick Start (When Internet Available)

## 1-Minute Setup

```bash
# Terminal 1: Backend
cd c:\DS-project\backend
pip install -r requirements.txt
# Edit .env: set HF_API_KEY=hf_YOUR_KEY_HERE
uvicorn main:app --reload

# Terminal 2: Frontend
cd c:\DS-project\client
npm install
npm start

# Open browser: http://localhost:3000
```

## That's it! 🎉

Now paste political text and analyze away.

---

## Get Hugging Face API Key (FREE)

1. Visit: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: "political-analyzer"
4. Type: "Read"
5. Copy the token
6. Edit `backend/.env`: `HF_API_KEY=hf_YOUR_TOKEN_HERE`
7. Save and restart backend

---

## First Run Expectations

**First request**: 10-30 seconds (model warming up - normal)
**Next requests**: 3-5 seconds (fast!)

---

## Test It Works

Paste this text and analyze:
> "The current policies are destroying our economy and violating our rights."

Expected results:
- **Tone**: NEGATIVE (~95% confidence)
- **Bias**: HIGH (strong emotional language)
- **Summary**: Brief summary of the statement

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Connection failed" | Ensure backend running on localhost:8000 |
| "Invalid API key" | Generate new token at huggingface.co/settings/tokens |
| 30+ sec on first request | Normal! HF Inference API warms up the model |
| 429 "Too many requests" | Wait 60 seconds, then retry |

---

## Server Endpoints

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

---

## Keyboard Shortcuts

- `Ctrl+C` in terminal: Stop server
- `F12`: Open browser dev tools (see API errors)
- `Ctrl+Shift+Delete`: Clear browser cache (if styles broken)

---

## Production Deployment

```bash
# Build frontend
cd client && npm run build

# Start backend with Gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

Deploy `client/build/` to Vercel/Netlify/GitHub Pages.

---

**Questions?** Check `README.md` or `SETUP.md` for detailed guides.
