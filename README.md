# Political Text Analysis Web Application

A full-stack web application that analyzes political text for tone, bias, and generates summaries using Hugging Face Transformer models.

**⏱️ Build Time**: ~2-3 hours
**🛠️ Stack**: React + FastAPI + Hugging Face Inference API

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Hugging Face API key (free from https://huggingface.co/settings/tokens)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # Windows
# or source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Edit .env and replace 'your_huggingface_api_key_here' with your actual HF API key
# HF_API_KEY=your_actual_key_here

# Start the server
uvicorn main:app --reload
# Server runs on http://localhost:8000
```

### 2. Frontend Setup (in a new terminal)

```bash
cd client

# Install dependencies
npm install

# Start development server
npm start
# App runs on http://localhost:3000
```

### 3. Test the Application

1. Open http://localhost:3000 in your browser
2. Paste political text in the textarea (50-5000 characters)
3. Click "Analyze Text"
4. View results: tone, bias level, and summary

---

## 📁 Project Structure

```
DS-project/
├── backend/
│   ├── main.py                 # FastAPI app, endpoints
│   ├── prompts.py              # Bias detection prompt variants
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (HF_API_KEY)
│   └── services/
│       ├── hf_client.py        # Hugging Face API client with retry logic
│       ├── output_parser.py    # Parse & validate model outputs
│       └── text_manager.py     # Text truncation with metadata
│
└── client/
    ├── package.json            # Node dependencies
    ├── tailwind.config.js      # Tailwind CSS config
    ├── postcss.config.js       # PostCSS config
    ├── public/
    │   └── index.html          # HTML entry point
    └── src/
        ├── App.jsx             # Main app component
        ├── index.js            # React entry point
        ├── index.css           # Tailwind imports + custom styles
        ├── utils/
        │   └── api.js          # Axios API client + error handling
        └── components/
            ├── AnalysisForm.jsx        # Text input form
            ├── ResultsDisplay.jsx      # Results cards with color coding
            ├── LoadingSpinner.jsx      # Loading indicator
            └── ErrorDisplay.jsx        # Error message display
```

---

## 🔑 API Endpoints

### Main Analysis Endpoint
```
POST /analyze
Content-Type: application/json

Request:
{
  "text": "Your political text here..."
}

Response:
{
  "tone": "POSITIVE" | "NEGATIVE",
  "tone_score": 0.95,
  "tone_confidence": "high" | "medium" | "low",
  "bias": "NONE" | "LOW" | "MEDIUM" | "HIGH",
  "bias_score": 3.5,
  "bias_explanation": "...",
  "summary": "...",
  "truncation_warning": null or "Text was truncated..."
}
```

### Lightweight Endpoints
- `POST /analyze-sentiment` - Tone analysis only
- `POST /analyze-summary` - Summarization only
- `POST /analyze-bias` - Bias detection only
- `GET /health` - Health check

---

## 🧠 NLP Models

| Analysis | Model | Task |
|----------|-------|------|
| **Tone** | `distilbert-base-uncased-finetuned-sst-2-english` | Sentiment classification (POSITIVE/NEGATIVE) |
| **Summary** | `facebook/bart-large-cnn` | Abstractive summarization |
| **Bias** | `google/flan-t5-large` | Text generation with few-shot prompting |

---

## 🎯 Features

### ✅ Core Analysis
- **Sentiment Analysis**: Classify text tone as positive/negative with confidence scoring
- **Bias Detection**: Identify political lean (NONE/LOW/MEDIUM/HIGH) with explanation
- **Summarization**: Generate 3-4 line summaries of political content

### ✅ Error Handling & Resilience
- **Exponential Backoff**: 3 retries with 0.5s, 1s, 2s delays for API failures
- **Status Code Handling**: Graceful handling of 429 (rate limit), 502-504 (service errors), 401-403 (auth)
- **Text Truncation**: Smart truncation with user warnings if text exceeds model limits
- **Fallback Outputs**: Sensible defaults if API calls fail

### ✅ User Experience
- **Real-time Character Count**: Warn at 90% limit, prevent over-submission
- **Color-Coded Results**: Green/yellow/orange/red for bias levels; green/red for tone
- **Copy-to-Clipboard**: One-click result copying
- **Responsive Design**: Mobile (1-col) → Tablet (2-col) → Desktop (3-col) layouts
- **Loading States**: Animated spinner with estimated time
- **Truncation Warnings**: Banner alert if text was truncated for analysis

### ✅ Optimization
- **Parallel Processing**: All 3 analyses run concurrently via `asyncio.gather()`
- **Prompt Engineering**: Few-shot and chain-of-thought variants for bias detection
- **Output Cleaning**: Regex-based parsing and validation for all model outputs

---

## ⚙️ Configuration

### Backend (.env)
```
HF_API_KEY=hf_YOUR_API_KEY_HERE
```

Get your free API key at: https://huggingface.co/settings/tokens

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
```

---

## 🚨 Troubleshooting

### "Connection failed" or "Backend server not ready"
- Ensure backend is running: `cd backend && uvicorn main:app --reload`
- Check it's on http://localhost:8000
- Verify `.env` has a valid `HF_API_KEY`

### "Too many requests" (429 error)
- You've hit rate limits (likely on free HF tier)
- The app will automatically retry with exponential backoff
- Wait 60+ seconds before trying again
- Consider upgrading to HF Pro or using batch endpoints

### Models taking 10-30 seconds on first request
- Hugging Face Inference API puts free-tier models to sleep after ~30 min of inactivity
- First request after sleep triggers model load (~10-30s)
- Subsequent requests are fast (3-5s)

### Text analysis fails or returns "Analysis inconclusive"
- Check if text is too long (>5000 chars) - it will be truncated
- Try a shorter text (300-500 words recommended)
- Verify internet connection is stable

---

## 📊 Performance Notes

| Metric | Expected |
|--------|----------|
| First request (cold model) | 10-30s |
| Subsequent requests | 3-5s |
| Max text input | 5,000 characters |
| Max concurrent requests | 5 (soft limit) |
| Rate limit | 30 requests/minute per IP |

---

## 🔄 Workflow Architecture

```
User (Browser)
    ↓
React Frontend (http://localhost:3000)
    ↓ [POST /analyze]
FastAPI Backend (http://localhost:8000)
    ↓ [Parallel tasks]
    ├─→ HF Inference API (Sentiment: distilbert)
    ├─→ HF Inference API (Summarization: BART)
    └─→ HF Inference API (Bias: FLAN-T5)
    ↑ [All results]
React Frontend
    ↓
Results Display (color-coded cards)
```

---

## 📝 Example Usage

### Input
```
"The current administration's economic policies have unfairly hurt working-class Americans. 
Socialism never works, and the liberal media won't tell you the truth."
```

### Output
```json
{
  "tone": "NEGATIVE",
  "tone_score": 0.92,
  "tone_confidence": "high",
  "bias": "HIGH",
  "bias_score": 4.5,
  "bias_explanation": "Strong emotional language and partisan framing. 
                       Uses loaded terms like 'unfairly' and 'never works'. 
                       No acknowledgment of alternative perspectives.",
  "summary": "The administration's economic policies negatively impact working-class Americans. 
             The speaker criticizes socialism and mainstream media.",
  "truncation_warning": null
}
```

---

## 🛡️ Privacy & Security

- ✅ No data stored permanently (stateless API)
- ✅ Texts sent only to Hugging Face Inference API
- ✅ API key stored locally in `.env` (never committed to git)
- ✅ CORS enabled only for localhost (development)
- ⚠️ For production: Configure proper CORS, use environment variables for secrets

---

## 🚀 Deployment (Future)

### Backend (Production)
```bash
# Use production ASGI server (Gunicorn + Uvicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# Or Docker
docker build -t political-analyzer-api .
docker run -p 8000:8000 -e HF_API_KEY=$HF_API_KEY political-analyzer-api
```

### Frontend (Production)
```bash
npm run build
# Deploy 'build/' folder to Vercel, Netlify, or GitHub Pages
```

---

## 📚 Dependencies

### Backend
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **httpx** - Async HTTP client
- **pydantic** - Data validation
- **python-dotenv** - Environment variables

### Frontend
- **react** - UI library
- **axios** - HTTP client
- **tailwindcss** - CSS framework

---

## 🔮 Future Enhancements

- [ ] Database for analysis history
- [ ] Redis caching for repeated texts
- [ ] Batch API for multiple texts
- [ ] PDF/CSV export of results
- [ ] User authentication
- [ ] Advanced filters (by ideology, topic)
- [ ] Fine-tuned bias detection model
- [ ] Multi-language support

---

## 📄 License

This project is provided as-is for educational purposes.

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify backend is running on http://localhost:8000
3. Check `.env` has a valid HF_API_KEY
4. Review browser console for API errors (F12)

---

**Happy analyzing! 🎉**
