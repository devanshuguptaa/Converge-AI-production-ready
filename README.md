<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/NVIDIA%20AI-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA">
  <img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white" alt="Slack">
  <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white" alt="WhatsApp">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

<h1 align="center">🤖 Converge AI</h1>

<p align="center">
  <strong>A Production-Ready, Multi-Platform AI Assistant with Gmail, Calendar & Workspace Intelligence</strong>
</p>

<p align="center">
  <em>Multi-LLM (Gemini · NVIDIA) • Slack · Telegram · WhatsApp • MCP Architecture • RAG • Long-Term Memory • Per-User OAuth</em>
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Platform Setup](#-platform-setup)
  - [Slack](#slack)
  - [Telegram](#telegram)
  - [WhatsApp](#whatsapp)
- [Gmail & Calendar Setup](#-gmail--calendar-setup)
- [Running the Application](#-running-the-application)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**Converge AI** is an enterprise-grade AI assistant that connects to **Slack**, **Telegram**, and **WhatsApp** — bringing the power of large language models into the messaging platforms your team already uses. It combines intelligent conversation with practical productivity integrations like Gmail, Google Calendar, and workspace-wide semantic search.

Built on a **Model Context Protocol (MCP)** architecture with support for multiple LLM backends, this assistant can:

- 📧 Read, send, draft, and summarize emails on your behalf
- 📅 Manage calendar events with natural language
- 🔍 Search through your Slack message history using semantic RAG
- 🧠 Remember your preferences and context across sessions
- ⏰ Schedule reminders and recurring messages
- 🔐 Authenticate each user independently via OAuth 2.0

---

## ✨ Key Features

### 🧠 Multi-LLM Intelligence

| Provider | Model | Use Case |
|----------|-------|----------|
| **Google Gemini** | `gemini-2.0-flash-exp` | Default — fast, accurate, multimodal |
| **NVIDIA AI** | `meta/llama-3.1-8b-instruct` | Alternative — open-weight, self-hosted option |

Switch between providers with a single environment variable (`LLM_PROVIDER`).

### 💬 Multi-Platform Messaging

| Platform | Transport | Features |
|----------|-----------|----------|
| **Slack** | Socket Mode (WebSocket) | DMs, @mentions, channel messages, reactions, thread awareness, DM access policies |
| **Telegram** | Long-polling via Bot API | Private chats, group messages, concurrent update processing |
| **WhatsApp** | Evolution API gateway + webhooks | Text messages, media captions, QR code pairing, typing indicators, read receipts |

### 📧 Gmail Integration

| Tool | Description |
|------|-------------|
| `list_recent_emails` | Browse your inbox with customizable filters |
| `get_email_details` | Read full email content with parsed MIME bodies |
| `get_multiple_email_details` | Batch-fetch multiple emails at once |
| `send_email` | Compose and send emails via natural language |
| `create_draft` | Save email drafts for later |
| `summarize_email_thread` | Get AI-powered thread summaries |

### 📅 Google Calendar Integration

| Tool | Description |
|------|-------------|
| `list_calendar_events` | View upcoming events within date ranges (defaults to next 7 days) |
| `create_calendar_event` | Schedule new events with descriptions and ISO timestamps |

### 📚 RAG (Retrieval-Augmented Generation)

- **ChromaDB** vector database with persistent storage for semantic search
- Automatic background indexing of Slack message history (configurable interval)
- Dual embedding support: Gemini (`text-embedding-004`, 768-dim) or NVIDIA (`llama-nemotron-embed-1b-v2`, 2048-dim)
- Context-aware middleware that detects history-related queries and injects relevant results

### 💾 Long-Term Memory

- **mem0** integration for persistent user preferences and facts
- Three dedicated tools: `remember_fact`, `recall_memories`, `forget_memory`
- Personalized responses based on learned context across sessions

### ⏰ Task Scheduling

- **APScheduler** with both one-time and recurring (cron) task support
- `set_reminder` — natural language time parsing ("tomorrow", "in 2 hours")
- `schedule_message` — schedule future or recurring workspace messages
- Tasks persist in SQLite and reload automatically on restart

### 🔐 Per-User OAuth 2.0

- Each user authenticates independently — no shared tokens
- PKCE-enhanced authorization code flow
- Per-user token isolation: `token_gmail_{channel}_{user}.pickle`
- Automatic token refresh with graceful re-authentication prompts
- Platform-aware callbacks (Slack, Telegram, WhatsApp)

### 🔧 MCP (Model Context Protocol)

- Clean separation between tool schemas, permissions, and execution
- Permission scopes: `GMAIL_READ`, `GMAIL_SEND`, `GMAIL_MODIFY`, `CALENDAR_READ`, `CALENDAR_WRITE`
- Extensible registry with placeholder GitHub and Notion integrations
- Thread-safe execution for non-thread-safe HTTP libraries

---

## 🏗 Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        MESSAGING PLATFORMS                                │
│   ┌───────────────┐   ┌───────────────┐   ┌────────────────────────┐    │
│   │     Slack      │   │   Telegram    │   │       WhatsApp         │    │
│   │ (Socket Mode)  │   │(Long-Polling) │   │  (Evolution API +      │    │
│   │                │   │              │   │   Webhooks)             │    │
│   └───────┬───────┘   └──────┬────────┘   └───────────┬────────────┘    │
│           └──────────────────┼────────────────────────┘                  │
│                              ↓                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                      FASTAPI APPLICATION                                  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     MIDDLEWARE LAYER                                 │ │
│  │   ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │ │
│  │   │     RAG      │  │    Memory    │  │    Slack Context       │  │ │
│  │   │  Middleware   │  │  Middleware  │  │    Middleware          │  │ │
│  │   │ (intent      │  │ (mem0 query  │  │ (platform-aware        │  │ │
│  │   │  detection)  │  │  injection)  │  │  formatting)           │  │ │
│  │   └──────────────┘  └──────────────┘  └────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │              LANGCHAIN AGENT (Gemini or NVIDIA)                     │ │
│  │         Tool Selection • Planning • Context Variables               │ │
│  │                     ~21 Bound Tools                                 │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        TOOL LAYER                                   │ │
│  │  ┌────────┐ ┌─────────┐ ┌───────┐ ┌─────┐ ┌────────┐ ┌────────┐ │ │
│  │  │ Email  │ │Calendar │ │ Slack │ │ RAG │ │ Memory │ │Schedule│ │ │
│  │  │ Tools  │ │ Tools   │ │ Tools │ │Tools│ │ Tools  │ │ Tools  │ │ │
│  │  │  (6)   │ │  (2)    │ │  (5)  │ │ (1) │ │  (3)   │ │  (2)   │ │ │
│  │  └────────┘ └─────────┘ └───────┘ └─────┘ └────────┘ └────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    MCP INTEGRATIONS                                 │ │
│  │  ┌──────────────────┐  ┌─────────────────────────────────────────┐ │ │
│  │  │    Gmail API     │  │       Google Calendar API               │ │ │
│  │  │ (Per-User OAuth) │  │       (Per-User OAuth)                  │ │ │
│  │  └──────────────────┘  └─────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                       DATA LAYER                                    │ │
│  │  ┌──────────┐   ┌──────────────┐   ┌────────────────────────────┐ │ │
│  │  │ ChromaDB │   │    SQLite    │   │          mem0              │ │ │
│  │  │  (RAG    │   │ (Sessions,  │   │    (Long-term Memory)      │ │ │
│  │  │ Vectors) │   │  Messages,  │   │                            │ │ │
│  │  │          │   │  Tasks)     │   │                            │ │ │
│  │  └──────────┘   └──────────────┘   └────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **LLM** | [Google Gemini 2.0 Flash](https://ai.google.dev/) / [NVIDIA AI Endpoints](https://build.nvidia.com/) |
| **Framework** | [LangChain](https://python.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| **Slack** | [Slack Bolt for Python](https://slack.dev/bolt-python/) (Socket Mode) |
| **Telegram** | [Telegram Bot API](https://core.telegram.org/bots/api) via `httpx` |
| **WhatsApp** | [Evolution API](https://github.com/EvolutionAPI/evolution-api) gateway |
| **Vector DB** | [ChromaDB](https://www.trychroma.com/) (persistent) |
| **Memory** | [mem0](https://mem0.ai/) |
| **Database** | [SQLite](https://www.sqlite.org/) via [SQLAlchemy](https://www.sqlalchemy.org/) ORM |
| **Scheduler** | [APScheduler](https://apscheduler.readthedocs.io/) |
| **Authentication** | Google OAuth 2.0 with PKCE |
| **Containerization** | [Docker](https://www.docker.com/) + Docker Compose |
| **Reverse Proxy** | [Nginx](https://nginx.org/) with TLS 1.2/1.3 |
| **CI/CD** | [GitHub Actions](https://github.com/features/actions) |

---

## 📋 Prerequisites

- **Python 3.13+** ([Download](https://www.python.org/downloads/))
- **Slack Workspace** with admin access
- **Google Cloud Project** with Gmail & Calendar APIs enabled
- **API Keys:**
  - [Google Gemini API Key](https://aistudio.google.com/apikey) — or [NVIDIA AI API Key](https://build.nvidia.com/)
  - [mem0 API Key](https://app.mem0.ai/) *(optional)*

**Optional (for additional platforms):**
- **Telegram Bot Token** from [@BotFather](https://t.me/botfather)
- **WhatsApp** via Evolution API (included in Docker Compose)

---

## 📥 Installation

### Option 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/devanshuguptaa/Converge-AI.git
cd Converge-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using UV (Faster)

```bash
# Install uv if not already installed
pip install uv

# Install dependencies with uv
uv sync
```

### Option 3: Docker

```bash
# Build and run with Docker Compose
docker compose up --build
```

---

## ⚙️ Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Variables

Edit `.env` with your credentials. Below is a complete reference of all available options:

#### Core (Required)

```env
# ── Slack ──────────────────────────────────────────
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# ── LLM Provider ──────────────────────────────────
LLM_PROVIDER=gemini                          # "gemini" or "nvidia"

# Gemini (default)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_CHAT_MODEL=gemini-2.0-flash-exp
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

# NVIDIA (alternative)
NVIDIA_API_KEY=your-nvidia-api-key
NVIDIA_CHAT_MODEL=meta/llama-3.1-8b-instruct
NVIDIA_EMBEDDING_MODEL=nvidia/llama-nemotron-embed-1b-v2
```

#### Features (Optional)

```env
# ── Memory ─────────────────────────────────────────
MEM0_API_KEY=your-mem0-api-key
MEMORY_ENABLED=true

# ── RAG ────────────────────────────────────────────
RAG_ENABLED=true
RAG_MAX_RESULTS=10
RAG_INDEXER_INTERVAL_MINUTES=60
VECTOR_DB_PATH=./data/chromadb

# ── MCP Integrations ──────────────────────────────
MCP_ENABLED=true
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...         # Placeholder for future use
NOTION_API_TOKEN=secret_...                  # Placeholder for future use

# ── Scheduler & Database ──────────────────────────
DATABASE_PATH=./data/assistant.db
```

#### Additional Platforms (Optional)

```env
# ── Telegram ───────────────────────────────────────
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# ── WhatsApp ───────────────────────────────────────
WHATSAPP_ENABLED=false
WHATSAPP_API_URL=http://whatsapp-gateway:8080
WHATSAPP_API_KEY=your-evolution-api-key
WHATSAPP_WEBHOOK_SECRET=your-webhook-secret
WHATSAPP_WEBHOOK_URL=http://localhost:8000/webhooks/whatsapp
WHATSAPP_INSTANCE_NAME=converge_assistant
```

#### Application Settings

```env
# ── Server ─────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO                               # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=development                      # development or production
REDIRECT_URI_BASE=http://localhost:8000       # Base URL for OAuth callbacks

# ── Gmail & Calendar ──────────────────────────────
GMAIL_CREDENTIALS_PATH=credentials/client_secret_for_gmail_and_calender.json
GMAIL_TOKEN_PATH=credentials/token_gmail.pickle
CALENDAR_TOKEN_PATH=credentials/token_calendar.pickle

# ── Access Control ─────────────────────────────────
DM_POLICY=open                               # "open", "pairing", or "allowlist"
ALLOWED_USERS=                               # Comma-separated user IDs (for allowlist)
```

---

## 📱 Platform Setup

### Slack

<details>
<summary><strong>Click to expand Slack setup instructions</strong></summary>

#### Step 1: Create Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Name your app (e.g., "Converge AI") and select your workspace

#### Step 2: Configure OAuth Scopes

Navigate to **OAuth & Permissions** and add these **Bot Token Scopes**:

| Scope | Purpose |
|-------|---------|
| `app_mentions:read` | Read @mentions of your bot |
| `channels:history` | Read channel message history |
| `channels:read` | View channel information |
| `chat:write` | Send messages as the bot |
| `im:history` | Read DM history |
| `im:read` | View DM information |
| `im:write` | Send DMs |
| `users:read` | View user information |
| `reactions:write` | Add emoji reactions |

#### Step 3: Enable Socket Mode

1. Navigate to **Socket Mode** in the sidebar
2. Toggle **Enable Socket Mode** ON
3. Create an **App-Level Token** with scope `connections:write`
4. Copy this token as `SLACK_APP_TOKEN`

#### Step 4: Subscribe to Events

Navigate to **Event Subscriptions**:

1. Toggle **Enable Events** ON
2. Under **Subscribe to bot events**, add:
   - `app_mention`
   - `message.im`
   - `message.channels`

#### Step 5: Install to Workspace

1. Go to **Install App**
2. Click **Install to Workspace**
3. Copy the **Bot User OAuth Token** as `SLACK_BOT_TOKEN`

</details>

---

### Telegram

<details>
<summary><strong>Click to expand Telegram setup instructions</strong></summary>

#### Step 1: Create a Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** provided

#### Step 2: Configure

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

#### Step 3: Start

The Telegram bot starts automatically with the application. It uses long-polling (no webhook setup required) and processes messages concurrently via background tasks.

</details>

---

### WhatsApp

<details>
<summary><strong>Click to expand WhatsApp setup instructions</strong></summary>

#### Step 1: Start the Evolution API Gateway

The WhatsApp integration uses the [Evolution API](https://github.com/EvolutionAPI/evolution-api) as a gateway. It's included in the Docker Compose configuration:

```bash
docker compose up whatsapp-gateway -d
```

#### Step 2: Configure

```env
WHATSAPP_ENABLED=true
WHATSAPP_API_URL=http://whatsapp-gateway:8080
WHATSAPP_API_KEY=your-evolution-api-key
WHATSAPP_WEBHOOK_SECRET=your-webhook-secret
WHATSAPP_WEBHOOK_URL=http://slack-bot:8000/webhooks/whatsapp
WHATSAPP_INSTANCE_NAME=converge_assistant
```

#### Step 3: Link Your Device

1. Start the application
2. Visit `http://localhost:8000/webhooks/whatsapp/qr` in your browser
3. Scan the QR code with WhatsApp on your phone
4. The QR page auto-disappears once connected

> **Note:** The gateway automatically rejects voice/video calls with a polite message, enables always-online status, and sends read receipts.

</details>

---

## 📧 Gmail & Calendar Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the following APIs:
   - [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
   - [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

### Step 2: Create OAuth 2.0 Credentials

1. Navigate to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Choose **Web application** as application type
4. Add `{REDIRECT_URI_BASE}/auth/callback` to **Authorized redirect URIs**
5. Download the JSON file
6. Rename to `client_secret_for_gmail_and_calender.json`
7. Place in `credentials/` folder

### Step 3: Authorize (Development)

For local development, run the interactive setup script:

```bash
python setup_auth.py
```

This opens a browser for Google OAuth consent and creates default token pickle files.

### Per-User Authentication (Production)

In production, each user authenticates individually:

1. User asks the bot to access email or calendar
2. Bot detects missing credentials and responds with a **Sign In** link
3. User clicks the link → Google consent screen → callback
4. Token saved as `credentials/token_gmail_{channel}_{user}.pickle`
5. All subsequent requests use the user's own credentials

---

## 🚀 Running the Application

### Development Mode

```bash
# Activate virtual environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac

# Run with hot reload
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Run directly
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Or use the entry point
python main.py
```

### Docker Mode

```bash
docker compose up -d
```

This starts three services:

| Service | Description | Port |
|---------|-------------|------|
| `slack-bot` | Main FastAPI application | 8000 (internal) |
| `whatsapp-gateway` | Evolution API for WhatsApp | 8080 (internal) |
| `nginx` | Reverse proxy with TLS | 80, 443 |

### Startup Sequence

```
✅ Validating configuration...
✅ Initializing database (SQLite)...
✅ Setting up RAG system (ChromaDB)...
✅ Initializing memory (mem0)...
✅ Loading MCP tools (Email, Calendar)...
✅ Creating AI agent (Gemini / NVIDIA)...
✅ Starting scheduler (APScheduler)...
✅ Connecting Slack app (Socket Mode)...
✅ Initializing WhatsApp gateway...
✅ Starting Telegram bot (long-polling)...
✅ Launching background RAG indexer...
🚀 Ready to receive messages!
```

---

## 💬 Usage Examples

### Basic Conversation
```
You: Hello!
Bot: Hi! I'm your AI assistant. I can help with emails, calendar,
     reminders, and searching your Slack history.
```

### Email Operations

```
You: Show me my last 5 emails
Bot: 📧 Here are your recent emails:
     1. From: john@example.com — "Project Update" — Feb 9
     2. From: hr@company.com  — "Benefits Enrollment" — Feb 8
     ...

You: Send an email to sarah@company.com about the meeting tomorrow at 3pm
Bot: ✅ Email sent successfully!
     To: sarah@company.com
     Subject: Meeting Tomorrow
     Body: Hi Sarah, Just a reminder about our meeting tomorrow at 3pm...

You: Summarize the email thread about the Q4 report
Bot: 📋 Thread Summary:
     The Q4 report discussion spans 5 emails over 3 days...
```

### Calendar Operations

```
You: What's on my calendar this week?
Bot: 📅 Upcoming Events:
     • Mon Feb 10, 10:00 AM — Team Standup
     • Tue Feb 11, 2:00 PM  — Client Call
     • Wed Feb 12, 9:00 AM  — Project Review

You: Schedule a meeting called "Design Review" tomorrow at 2pm for 1 hour
Bot: ✅ Event created!
     📅 Design Review
     🕐 Tomorrow, 2:00 PM – 3:00 PM
```

### Memory

```
You: Remember that I prefer dark mode and Python
Bot: Got it! I'll remember that.

[Later...]
You: What theme should I use for the new dashboard?
Bot: Based on your preferences, I'd recommend dark mode!
```

### RAG Search

```
You: What did we discuss about the API redesign last week?
Bot: Based on your Slack history:
     • Moving to REST from GraphQL (discussed with @john)
     • Authentication changes proposed by @sarah
     • Timeline set for Q2 release
```

### Reminders & Scheduling

```
You: Remind me in 2 hours to review the PR
Bot: ⏰ Reminder set for 2 hours from now!

You: Schedule a daily standup message in #engineering at 9am
Bot: ✅ Recurring message scheduled!
```

### Slack Commands

| Command | Description |
|---------|-------------|
| `help` / `?` | Display interactive help guide |
| `reset` / `clear` | Reset conversation session |
| `summarize` / `tldr` | Summarize current channel thread |

---

## 📁 Project Structure

```
Converge-AI/
├── 📄 main.py                          # Application entry point
├── 📄 setup_auth.py                    # Google OAuth setup (development)
├── 📄 verify_email.py                  # Email integration diagnostics
├── 📄 requirements.txt                 # Python dependencies
├── 📄 pyproject.toml                   # Project metadata & build config
├── 📄 docker-compose.yml               # Multi-service Docker config
├── 📄 Dockerfile                       # Container definition
├── 📄 .env.example                     # Environment variable template
│
├── 📁 src/                             # Source code
│   ├── 📄 main.py                      # FastAPI app, lifespan, endpoints
│   ├── 📄 config.py                    # Pydantic settings & validation
│   ├── 📄 database.py                  # SQLAlchemy models & helpers
│   │
│   ├── 📁 agent/                       # AI Agent
│   │   ├── 📄 core.py                  # LangChain agent, multi-LLM, tool binding
│   │   └── 📄 middleware.py            # RAG / Memory / Context injection
│   │
│   ├── 📁 slack/                       # Slack Integration
│   │   ├── 📄 app.py                   # Bolt handlers, events, commands
│   │   └── 📄 tools.py                 # Slack action tools (5 tools)
│   │
│   ├── 📁 telegram/                    # Telegram Integration
│   │   └── 📄 client.py               # Long-polling bot client
│   │
│   ├── 📁 whatsapp/                    # WhatsApp Integration
│   │   ├── 📄 client.py               # Evolution API client & QR pairing
│   │   └── 📄 webhook.py              # FastAPI webhook router
│   │
│   ├── 📁 auth/                        # Authentication
│   │   └── 📄 router.py               # Multi-platform OAuth 2.0 + PKCE
│   │
│   ├── 📁 mcp/                         # Model Context Protocol
│   │   ├── 📄 registry.py             # Tool registration & aggregation
│   │   ├── 📄 email_calendar_integration.py  # LangChain tool wrappers
│   │   ├── 📁 core/
│   │   │   ├── 📄 server.py           # MCP server & thread-safe dispatch
│   │   │   ├── 📄 permissions.py      # Scope-based access control
│   │   │   └── 📄 context_builder.py  # Structured prompt context
│   │   ├── 📁 tools/
│   │   │   ├── 📄 email_tools.py      # Gmail tools (6 tools)
│   │   │   └── 📄 calendar_tools.py   # Calendar tools (2 tools)
│   │   └── 📁 integrations/
│   │       ├── 📁 gmail/
│   │       │   ├── 📄 service.py      # Gmail API client & token mgmt
│   │       │   ├── 📄 reader.py       # MIME parsing & thread reading
│   │       │   └── 📄 sender.py       # Email composition & sending
│   │       └── 📁 calendar/
│   │           ├── 📄 service.py      # Calendar API client & token mgmt
│   │           ├── 📄 reader.py       # Event listing & date parsing
│   │           └── 📄 writer.py       # Event creation
│   │
│   ├── 📁 rag/                         # Retrieval-Augmented Generation
│   │   ├── 📄 vectorstore.py          # ChromaDB wrapper
│   │   ├── 📄 embeddings.py           # Gemini / NVIDIA embeddings
│   │   ├── 📄 indexer.py             # Background Slack history indexer
│   │   └── 📄 retriever.py           # Semantic search tool
│   │
│   ├── 📁 memory/                      # Long-Term Memory
│   │   └── 📄 mem0_client.py          # mem0 integration & tools
│   │
│   ├── 📁 scheduler/                   # Task Scheduling
│   │   └── 📄 tasks.py               # APScheduler + reminder tools
│   │
│   └── 📁 utils/                       # Utilities
│       └── 📄 logger.py              # Logging configuration
│
├── 📁 credentials/                     # OAuth credentials (gitignored)
├── 📁 data/                            # Runtime data (gitignored)
│   ├── 📄 assistant.db               # SQLite database
│   └── 📁 chromadb/                   # Vector database
├── 📁 nginx/                           # Reverse proxy config
│   └── 📄 nginx.conf                 # TLS, rate limiting, security headers
├── 📁 docs/                            # Documentation
│   └── 📄 aws_setup_guide.md         # AWS EC2 production deployment guide
└── 📁 .github/                         # CI/CD
    ├── 📁 workflows/
    │   └── 📄 deploy.yml              # CI + CD pipeline
    └── 📄 PULL_REQUEST_TEMPLATE.md    # PR template
```

---

## 📡 API Reference

### HTTP Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service metadata and enabled feature flags |
| `GET` | `/health` | Health status across all 7 subsystem components |
| `POST` | `/slack/events` | Slack event webhook receiver |
| `GET` | `/auth/login` | Initiate OAuth flow (`user_id`, `channel_id`, `service`) |
| `GET` | `/auth/callback` | OAuth authorization code callback |
| `POST` | `/webhooks/whatsapp` | WhatsApp message webhook |
| `GET` | `/webhooks/whatsapp/qr` | WhatsApp QR code pairing page |

### MCP Scopes

| Scope | Permission |
|-------|------------|
| `GMAIL_READ` | Read emails and threads |
| `GMAIL_SEND` | Send emails and create drafts |
| `GMAIL_MODIFY` | Modify email labels and state |
| `CALENDAR_READ` | View calendar events |
| `CALENDAR_WRITE` | Create and modify events |

### Tool Inventory

| Category | Tool | Description |
|----------|------|-------------|
| **Email** | `list_recent_emails` | List inbox emails with filters |
| | `get_email_details` | Fetch full email content |
| | `get_multiple_email_details` | Batch-fetch email details |
| | `send_email` | Send an email |
| | `create_draft` | Create email draft |
| | `summarize_email_thread` | Get thread messages for summarization |
| **Calendar** | `list_calendar_events` | List upcoming events |
| | `create_calendar_event` | Create a new event |
| **Slack** | `send_slack_message` | Send message to channel/thread |
| | `get_channel_history` | Fetch channel message history |
| | `list_channels` | List all public channels |
| | `get_user_info` | Get user profile details |
| | `add_reaction` | Add emoji reaction to a message |
| **RAG** | `search_slack_history` | Semantic search over indexed messages |
| **Memory** | `remember_fact` | Store a fact about a user |
| | `recall_memories` | Retrieve stored user facts |
| | `forget_memory` | Delete a specific memory |
| **Scheduler** | `set_reminder` | Set a one-time reminder |
| | `schedule_message` | Schedule a future/recurring message |

### Database Schema

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `conversation_sessions` | `session_id`, `user_id`, `channel_id`, `thread_ts`, `is_active` | Track conversation sessions across platforms |
| `messages` | `session_id`, `role`, `content`, `msg_metadata` | Store conversation history |
| `scheduled_tasks` | `task_id`, `user_id`, `task_type`, `schedule_time`, `cron_expression`, `is_active` | Persist scheduled reminders and messages |

---

## 🚢 Deployment

### Docker Compose (Recommended)

The included `docker-compose.yml` runs three services:

```yaml
services:
  slack-bot:         # FastAPI application (Python 3.13-slim)
  whatsapp-gateway:  # Evolution API (atendai/evolution-api:latest)
  nginx:             # Reverse proxy (nginx:alpine) with TLS
```

```bash
docker compose up -d --build
```

### AWS EC2 Production

A complete production deployment guide is available at [`docs/aws_setup_guide.md`](docs/aws_setup_guide.md), covering:

- EC2 instance setup (`t2.micro` / `t3.micro`, Ubuntu 24.04)
- Security group configuration (ports 22, 80, 443)
- Elastic IP and DuckDNS dynamic DNS
- Docker Engine & Compose installation
- Let's Encrypt SSL certificates (Certbot + HTTP-01 challenge)
- Automated daily certificate renewal via crontab
- Nginx reverse proxy with TLS 1.2/1.3, rate limiting, and hardened security headers

### Nginx Security Features

The included Nginx configuration provides:

- **TLS 1.2 / 1.3** with modern cipher suites
- **Rate limiting**: 10 requests/second with burst of 20
- **WebSocket** upgrade support for Socket Mode
- **Security headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Certbot** integration for free SSL via Let's Encrypt

---

## 🔄 CI/CD Pipeline

The project uses **GitHub Actions** with a **Git Flow** branching model:

| Branch | Purpose |
|--------|---------|
| `main` | Production — triggers deployment |
| `develop` | Integration — receives feature PRs |
| `feature/*` | Feature development branches |
| `hotfix/*` | Production hotfix branches |

### Pipeline Stages

```
┌─────────────────────────────────────────────────┐
│  CI (PRs to develop or main)                    │
│  ├── Python 3.13 setup                          │
│  ├── Ruff lint check (src/)                     │
│  ├── Ruff format check (src/)                   │
│  └── Smoke test (config import validation)      │
├─────────────────────────────────────────────────┤
│  CD (push to main only)                         │
│  ├── SSH to AWS EC2                             │
│  ├── git reset --hard origin/main               │
│  ├── docker compose build --no-cache            │
│  ├── docker compose up -d --remove-orphans      │
│  └── docker image prune -f                      │
└─────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

<details>
<summary><strong>Configuration Errors</strong></summary>

```
❌ Configuration errors:
   - SLACK_BOT_TOKEN is not configured
```

**Solution:** Ensure all required variables are set in `.env`:
```bash
cp .env.example .env
# Edit .env with your actual values
```

</details>

<details>
<summary><strong>Slack Connection Issues</strong></summary>

```
Failed to initialize Slack app
```

**Solutions:**
1. Verify Socket Mode is enabled in Slack App settings
2. Check that `SLACK_APP_TOKEN` starts with `xapp-`
3. Ensure `SLACK_BOT_TOKEN` starts with `xoxb-`
4. Reinstall the app to your workspace

</details>

<details>
<summary><strong>Gmail/Calendar Authentication Errors</strong></summary>

```
Error: invalid_grant
```

**Solution:** Re-authenticate:
```bash
# Delete existing tokens
rm credentials/token_gmail.pickle
rm credentials/token_calendar.pickle

# Re-run setup
python setup_auth.py
```

</details>

<details>
<summary><strong>Module Import Errors</strong></summary>

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Activate virtual environment first
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

</details>

<details>
<summary><strong>ChromaDB Errors</strong></summary>

```
Error initializing ChromaDB
```

**Solution:** Clear and rebuild:
```bash
rm -rf data/chromadb
# Restart the application — the indexer will re-populate
```

</details>

<details>
<summary><strong>WhatsApp QR Code Not Loading</strong></summary>

**Solutions:**
1. Ensure Evolution API gateway is running: `docker compose up whatsapp-gateway -d`
2. Check the QR page at `http://localhost:8000/webhooks/whatsapp/qr`
3. Verify `WHATSAPP_API_URL` and `WHATSAPP_API_KEY` are correct
4. Check gateway logs: `docker compose logs whatsapp-gateway`

</details>

<details>
<summary><strong>Telegram Bot Not Responding</strong></summary>

**Solutions:**
1. Verify `TELEGRAM_ENABLED=true` in `.env`
2. Check the bot token with: `curl https://api.telegram.org/bot<TOKEN>/getMe`
3. Ensure no other instance is polling the same bot token
4. Check application logs for polling errors

</details>

<details>
<summary><strong>Email/Calendar Pre-flight Diagnostics</strong></summary>

Run the built-in verification script:
```bash
python verify_email.py
```

This checks: Python dependencies, credential files, token pickles, and tool loading.

</details>

---

## 🤝 Contributing

Contributions are welcome! This project follows **Git Flow** and **Conventional Commits**.

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/voice-messages` |
| Hotfix | `hotfix/description` | `hotfix/token-refresh` |

### Commit Messages

```
feat: add WhatsApp media support
fix: resolve token refresh race condition
docs: update deployment guide for ARM64
refactor: extract email parsing to utility
test: add scheduler unit tests
chore: upgrade langchain to v2
```

### Workflow

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes
4. Run linting: `ruff check src/ && ruff format --check src/`
5. Commit with conventional commit messages
6. Push and open a Pull Request to `develop`

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full guidelines.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Devanshu Gupta**

- GitHub: [@devanshuguptaa](https://github.com/devanshuguptaa)

---

<p align="center">
  <a href="#-table-of-contents">⬆️ Back to Top</a>
</p>
