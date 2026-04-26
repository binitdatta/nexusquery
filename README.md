# NexusQuery

**Flask 3.12 + Anthropic Claude + Azure Databricks SQL**

A procurement analytics chatbot that translates natural language questions
into Databricks SQL, executes them against Gold Delta tables in ADLS Gen2,
and narrates results in plain English.

---

## Project structure

```
nexusquery/
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── routes/
│   │   ├── home.py            # / and /chatbot pages
│   │   ├── chat.py            # POST /chat/message, POST /chat/reset
│   │   └── health.py          # GET /health/
│   ├── services/
│   │   ├── anthropic_service.py  # LLM calls — SQL gen + narration
│   │   └── chat_service.py       # Orchestrates full NL→SQL→execute→narrate
│   ├── rest_clients/
│   │   └── databricks_client.py  # databricks-sql-connector wrapper
│   ├── utils/
│   │   ├── schema_context.py     # Gold schema + system prompt
│   │   └── sql_utils.py          # SQL extraction, safety check, formatting
│   └── templates/
│       ├── base.html
│       ├── home.html          # Landing page with architecture + comparison
│       └── chatbot.html       # Chat UI
├── config.py                  # Config from env vars
├── main.py                    # Entry point
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick start

### 1. Clone and install

```bash
git clone <your-repo>
cd nexusquery
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `DATABRICKS_SERVER_HOSTNAME` — `<your-databricks-server-hostname>`
- `DATABRICKS_HTTP_PATH` — from cluster → Advanced → JDBC/ODBC tab
- `DATABRICKS_ACCESS_TOKEN` — from Databricks UI → Settings → Developer → Access tokens

### 3. Start your Databricks cluster

In the Azure Databricks portal start `Binit Datta's Cluster`.
Wait for green status (~4 minutes).

### 4. Get the HTTP path

In Databricks:
1. Click **Compute** → your cluster
2. Scroll to **Advanced options** → **JDBC/ODBC** tab
3. Copy the **HTTP Path** value → paste into `.env`

### 5. Generate a personal access token

1. Databricks top-right → your avatar → **Settings**
2. **Developer** → **Access tokens** → **Generate new token**
3. Copy the token → paste into `.env` as `DATABRICKS_ACCESS_TOKEN`

### 6. Run the app

```bash
python main.py
```

Open http://localhost:5000

---

## Architecture

```
Browser (Bootstrap 5 dark)
    │  POST /chat/message
    ▼
Flask ChatService
    ├── AnthropicService  →  Claude generates SQL
    ├── DatabricksClient  →  executes SQL on Gold tables
    └── AnthropicService  →  Claude narrates results
```

### Gold tables available

| Table | Description |
|-------|-------------|
| `fact_spend_by_supplier` | Monthly spend per supplier |
| `fact_spend_by_category` | Monthly spend per category |
| `fact_otd_by_supplier` | On-time delivery % per supplier |
| `fact_invoice_match` | Invoice match rate per supplier |
| `fact_budget_variance` | Budget vs actual by category/plant |
| `fact_defect_rate` | Defect rate per supplier |

Data range: January 2024 – June 2024

---

## Limitations

- Data is historical (batch pipeline) — not real-time
- Read-only — cannot approve POs, update records, or trigger workflows
- Answers limited to what exists in the Gold schema
- LLM-generated SQL should be validated before operational use

---

## Cost reminder

Databricks cluster (`Standard_DS3_v2`, single node) costs ~$0.61/hour.
**Terminate the cluster when not in use.**
ADLS Gen2 storage costs pennies per month regardless.

``` 
jdbc:databricks://<your-databricks-server-hostname>:443/default;transportMode=http;ssl=1;httpPath=sql/protocolv1/o/<workspace-id>/<warehouse-id>;AuthMech=3;UID=token;PWD=<personal-access-token>


cd ~/Development/nexusquery
source .venv/bin/activate
python3 -c "
from databricks import sql
conn = sql.connect(
    server_hostname='<your-databricks-server-hostname>',
    http_path='<your-databricks-http-path>',
    access_token=os.getenv("DATABRICKS_ACCESS_TOKEN")
)
cursor = conn.cursor()
cursor.execute('SELECT 1 AS ping')
print(cursor.fetchall())
conn.close()
print('CONNECTION OK')
"


cat > /tmp/test_db.py << 'EOF'
import os
import sys
sys.path.insert(0, '/Users/binitdatta/Development/nexusquery')

from dotenv import load_dotenv
load_dotenv('/Users/binitdatta/Development/nexusquery/.env')

from databricks import sql

hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
token = os.getenv("DATABRICKS_ACCESS_TOKEN")

print("Hostname :", hostname)
print("HTTP Path:", http_path)
print("Token    :", token[:12] + "..." if token else "NOT SET")

try:
    print("\nConnecting...")
    conn = sql.connect(
        server_hostname=hostname,
        http_path=http_path,
        access_token=token
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1 AS ping")
    result = cursor.fetchall()
    print("SUCCESS:", result)
    conn.close()
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))
EOF

python3 /tmp/test_db.py
```