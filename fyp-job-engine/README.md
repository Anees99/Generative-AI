# AI Job Search & Resume Tailoring Engine

## Final Year Project - Academic Documentation

### Overview
This project is a **Python re-engineering** of career evaluation concepts inspired by the open-source [Career-Ops](https://github.com/career-ops) project (MIT License). It provides a desktop application for job seekers to analyze job postings, receive AI-powered match scores, and generate tailored resumes with transparent cost tracking.

### Key Features
- 🖥️ **Desktop GUI**: Modern dark/light mode interface using CustomTkinter
- 🔍 **Job Scraping**: Ethical public web scraping via Playwright (no login, no anti-bot bypass)
- 🤖 **AI Analysis**: LLM-powered job matching and resume tailoring (OpenAI/Gemini compatible)
- 📄 **PDF Generation**: ATS-friendly resume output with match scores
- 💰 **Cost Transparency**: Real-time token counting and USD cost estimation
- 📊 **Local Tracking**: SQLite database for job history and application management

---

## Architecture

```
fyp-job-engine/
├── main.py              # Desktop UI entry point (CustomTkinter)
├── engine/              # Core processing modules
│   ├── scraper.py       # Playwright-based job text extractor
│   ├── ai_processor.py  # LLM scoring & resume tailoring
│   └── pdf_generator.py # ATS-compliant PDF compiler
├── core/                # Infrastructure layer
│   ├── database.py      # SQLite job history tracker
│   └── cost_tracker.py  # Token counting & cost estimation
└── config/              # Configuration & prompts
    └── prompts.py       # Career-Ops inspired system prompts
```

### Design Decisions

1. **User-in-the-Loop**: All AI suggestions require manual review before PDF generation
2. **Transparent Costs**: Every API call displays token usage and USD estimates
3. **Local-First**: All data stored locally in SQLite; no cloud dependencies beyond LLM APIs
4. **Ethical Scraping**: Respects robots.txt, uses 10s timeouts, extracts only visible public text

---

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

```bash
# Clone or navigate to project directory
cd fyp-job-engine

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Environment Configuration

Create a `.env` file in the project root:

```env
# Required: Choose LLM provider (openai or google)
LLM_PROVIDER=openai

# For OpenAI:
OPENAI_API_KEY=your_openai_api_key_here

# For Google Gemini:
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Customize model selection
# OPENAI_MODEL=gpt-4o-mini
# GOOGLE_MODEL=gemini-1.5-flash
```

### Running the Application

```bash
python main.py
```

---

## Usage Guide

1. **Enter Job URL**: Paste a public job posting URL (e.g., LinkedIn, Indeed company pages)
2. **Paste Your Resume**: Input your current resume text in the provided field
3. **Click "Analyze Job"**: The system will:
   - Scrape the job posting (visible text only)
   - Send to LLM for analysis and scoring
   - Display match score, key skills, and tailored bullet points
   - Show token usage and cost estimate
4. **Review Results**: Examine the AI suggestions in the results panel
5. **Generate PDF**: Click "Generate Tailored Resume" to create an ATS-friendly PDF
6. **Track Applications**: All analyzed jobs are logged in the local database

---

## Ethical Compliance

### What This System Does ✅
- Extracts **publicly visible** text from job postings
- Requires **explicit user action** for each analysis
- Provides **transparent cost estimates** before API calls complete
- Stores all data **locally** on user's machine
- Generates resumes for **user review** before any submission

### What This System Does NOT Do ❌
- ❌ No CAPTCHA solving or anti-bot bypass techniques
- ❌ No authenticated scraping (no login credentials used)
- ❌ No automated job applications
- ❌ No resume spam or mass submissions
- ❌ No data sharing with third parties (beyond LLM API providers)

### Academic Integrity
This project re-engineers career evaluation methodologies from the MIT-licensed Career-Ops project. All prompt engineering and scoring logic are original implementations designed for educational purposes.

---

## Cost Estimation

The system uses `tiktoken` for precise token counting. Estimated costs (as of 2024):

| Provider | Model | Input Cost | Output Cost |
|----------|-------|------------|-------------|
| OpenAI | gpt-4o-mini | $0.15 / 1M tokens | $0.60 / 1M tokens |
| Google | gemini-1.5-flash | ~$0.075 / 1M tokens | ~$0.30 / 1M tokens |

**Typical analysis cost**: $0.001 - $0.005 per job posting

---

## API Reference

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `openai` or `google` |
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `GOOGLE_API_KEY` | If using Google | Your Google AI API key |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` |
| `GOOGLE_MODEL` | No | Default: `gemini-1.5-flash` |

### Database Schema

The SQLite database (`jobs.db`) contains:

```sql
CREATE TABLE job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT,
    company TEXT,
    match_score REAL,
    tailored_resume TEXT,
    token_count INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Troubleshooting

### Playwright Installation Issues
```bash
# Reinstall Playwright browsers
playwright install chromium --force

# On Linux, you may need additional dependencies:
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

### API Key Errors
- Ensure your `.env` file is in the project root
- Verify API keys are active and have sufficient credits
- Check that `LLM_PROVIDER` matches your configured API key

### PDF Generation Issues
- Ensure the `output/` directory exists and is writable
- Check that resume text is not empty

---

## Citation

If referencing this project in academic work, please cite:

```bibtex
@software{fyp_job_engine_2024,
  author = {Your Name},
  title = {AI Job Search \& Resume Tailoring Engine},
  year = {2024},
  note = {Final Year Project - Python re-engineering of Career-Ops concepts},
  url = {https://github.com/yourusername/fyp-job-engine}
}

@software{career_ops,
  title = {Career-Ops},
  year = {2023},
  license = {MIT},
  url = {https://github.com/career-ops}
}
```

---

## License

This project is released under the **MIT License**.

Portions of the prompt engineering methodology are conceptually derived from the Career-Ops project (MIT License). This implementation is an original Python re-engineering for educational purposes.

---

## Author

*Final Year Project - [Your Name]*  
*[Your University]*  
*[Year]*
