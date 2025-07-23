# Bitespeed Contact Reconciliation

A FastAPI backend service for tracking and consolidating customer identity across multiple purchases.

## Live API Endpoint

**POST** `https://bitespeed-task-q3hg.onrender.com/identify`

### Example Request:
```bash
curl -X POST "https://bitespeed-task-q3hg.onrender.com/identify" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "mcfly@hillvalley.edu",
    "phoneNumber": "123456"
  }'
```

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/KR15HNA-243/bitespeed-task.git
   cd bitespeed-task
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run locally:
   ```bash
   python main.py
   ```

## Tech Stack
- FastAPI
- SQLite
- Python