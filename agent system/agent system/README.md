# 📚 Agentic AI Academic Resource Discovery System

A production-ready autonomous system for discovering academic resources using multi-agent pipelines.

**🎉 NO API KEYS REQUIRED!** Uses DuckDuckGo for search and rule-based AI for analysis.

## 🌟 Features

- **Autonomous Web Crawling**: Automatically discovers academic resources
- **Multi-Agent Pipeline**: 9 specialized agents working together
- **Rule-Based Intelligence**: Smart filtering without expensive API calls
- **Human-in-the-Loop**: Final review dashboard for quality assurance
- **Scheduled Crawling**: Automated periodic discovery
- **Domain Trust Scoring**: Learns from approvals/rejections
- **100% Free**: No OpenAI, SerpAPI, or other paid services needed

## 🏗️ Architecture

```
[Search Agent] → [Crawl Agent] → [Extraction Agent] → [Relevance Agent]
   (DuckDuckGo)   (BeautifulSoup)                      (Rule-based)
                                                            ↓
[Database] ← [Filter] ← [Score Agent] ← [Dedup Agent] ← [College Agent] ← [Classification Agent]
     ↓
[Review Dashboard]
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "agent system"
pip install -r requirements.txt
```

### 2. Start with Docker (Recommended)

```bash
docker-compose up -d
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

### 4. Access the System

- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

### Manual Start (without Docker)

```bash
# Terminal 1: Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Terminal 2: Start API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Celery worker
celery -A workers.celery_app worker --loglevel=info

# Terminal 4: Start Celery beat (scheduler)
celery -A workers.celery_app beat --loglevel=info

# Terminal 5: Start dashboard
streamlit run dashboard/app.py
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/resources/` | GET | List resources |
| `/api/resources/pending` | GET | Pending for review |
| `/api/resources/{id}/review` | PUT | Approve/reject |
| `/api/resources/stats` | GET | Statistics |
| `/api/courses/` | GET/POST | Manage courses |
| `/api/colleges/` | GET/POST | Manage colleges |

## 🤖 Agent Details

1. **Search Agent**: DuckDuckGo search (free, no API key)
2. **Crawl Agent**: BeautifulSoup web scraping
3. **Extraction Agent**: Content cleaning & structuring
4. **Relevance Agent**: Rule-based relevance scoring
5. **Classification Agent**: Resource type detection (notes, papers, etc.)
6. **College Agent**: Institution matching by domain
7. **Deduplication Agent**: Hash-based duplicate detection
8. **Scoring Agent**: Multi-factor final scoring
9. **Review Agent**: Prepares human review queue

## 📱 Dashboard Features

- View pending resources
- One-click approve/reject
- Filter by course, college, type
- Real-time statistics
- AI confidence display

## 🔧 Configuration

Edit `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | localhost:5432 |
| `REDIS_URL` | Redis connection | localhost:6379 |
| `FINAL_SCORE_THRESHOLD` | Min score for review | 90 |
| `CRAWL_INTERVAL_HOURS` | Auto-crawl frequency | 6 |

## 📁 Project Structure

```
├── agents/          # LangGraph agents (rule-based)
├── api/             # FastAPI backend
├── db/              # PostgreSQL models
├── dashboard/       # Streamlit review UI
├── workers/         # Celery scheduler
├── config/          # Settings
├── utils/           # Helper functions
├── scripts/         # DB initialization
└── tests/           # Test suite
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🔒 Security Notes

- Never commit `.env` file
- Use strong database passwords in production
- Configure CORS for production
- Use HTTPS in production

## 📄 License

MIT License
