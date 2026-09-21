# UniAssist AI — Azure Cost Management & Credit Optimization Guide

## 1. Executive Summary & Subscription Context

- **Subscription Type:** Azure Student / Academic Sponsorship (~$9,555 available credits)
- **Primary Goal:** Maximize academic development runway while avoiding accidental depletion of credits.
- **Architectural Principle:** Lean, serverless, auto-scaling, and pay-as-you-go tiers over always-on premium instances.

---

## 2. Resource Cost Breakdown Matrix

| Azure Service | Recommended Tier | Estimated Cost | Cost Driver / Notes |
| :--- | :--- | :--- | :--- |
| **Azure AI Foundry / OpenAI** | Standard pay-as-you-go (`gpt-4o-mini`, `text-embedding-3-small`) | ~$0.15 / 1M input tokens, $0.60 / 1M output tokens | **Extremely cost-effective.** Do **not** provision Provisioned Throughput Units (PTUs) which cost $1000s/month. Stick to standard token-metered models. |
| **Azure AI Search (Foundry IQ)** | Free tier (`F`) for dev, Basic tier for RAG production | Free ($0/mo for 3 indexes, 50MB) or Basic (~$73/mo) | **High Alert:** Standard tier (S1) is ~$250/mo. Always start with the **Free** or **Basic** tier. |
| **Azure Database for PostgreSQL** | Flexible Server — Burstable `B1ms` or `B2s` | ~$15 – $30/month | Enable auto-stop or stop the database instance when not working on the project. Disable Geo-redundant backup. |
| **Azure Blob Storage** | Standard General Purpose v2 (Hot / Cool) | ~$0.02 / GB/month | Very cheap for university documents, PDFs, and complaint attachments. |
| **Azure Container Apps** | Consumption Plan (Serverless) | First 180,000 vCPU-seconds and 360,000 GiB-seconds are **FREE** each month | Set `minReplicas = 0` so instances scale down to 0 when idle. No ongoing costs when not in use! |
| **Azure Key Vault** | Standard Tier | ~$0.03 / 10,000 operations | Negligible cost (<$1/month). |
| **Application Insights & Monitor** | Basic ingestion | First 5 GB/month is **FREE** | Set a daily data cap (e.g. 100 MB/day) to avoid runaway logging charges. |

---

## 3. High-Risk Services to AVOID

> [!CAUTION]
> The following resources can rapidly burn hundreds of dollars per day if accidentally misconfigured:

1. **Azure OpenAI Provisioned Throughput (PTU):** Never click "Provisioned". Always choose "Standard (Pay-as-you-go)".
2. **Azure AI Search Standard (S1 / S2 / S3):** Never deploy an S-tier index unless required. A single S3 instance costs over $1,500/month.
3. **App Service Isolated Plans (ASE) or Premium V3:** Always choose Container Apps Consumption or App Service B1/F1.
4. **PostgreSQL High Availability / Geo-redundancy:** Keep high availability disabled for student dev.
5. **Azure Cognitive Services multi-service resource:** Stick to individual resources scoped to need.

---

## 4. How to Monitor Usage & Set Budget Alerts

### Step 1: Set a Hard Monthly Budget in Azure Portal
1. Open the [Azure Portal](https://portal.azure.com).
2. Search for **Cost Management + Billing** -> **Cost Alerts** / **Budgets**.
3. Click **Add Budget**:
   - **Scope:** Your Subscription or Resource Group `rg-uniassist-prod`
   - **Budget Name:** `UniAssist-Student-Budget`
   - **Reset Period:** Monthly
   - **Amount:** $50 - $100 (triggers alert way before significant credits are consumed)
4. Set Alert Conditions:
   - Alert at **50%** ($25)
   - Alert at **75%** ($37.50)
   - Alert at **90%** ($45)
   - Action: Send email to your registered student email address.

### Step 2: Set Application Insights Daily Cap
1. Navigate to your Application Insights resource.
2. Under **Usage and estimated costs**, select **Daily cap**.
3. Set daily volume cap to **0.5 GB/day** and turn off notification overages.

---

## 5. How to Shut Down Unused Resources

When not actively developing or testing:

1. **PostgreSQL Flexible Server:**
   ```bash
   az postgres flexible-server stop --resource-group rg-uniassist --name uniassist-pg-server
   ```
   *(PostgreSQL will stay stopped for up to 7 days before Azure automatically restarts it to perform maintenance; stop again if needed).*

2. **Azure Container Apps:**
   - With `minReplicas = 0`, Container Apps will automatically idle to zero cost when no HTTP requests are arriving.

3. **Delete Temporary Test Environments:**
   - Group all resources in a dedicated resource group: `rg-uniassist-dev`.
   - When finished with a testing cycle, you can delete the entire resource group with:
   ```bash
   az group delete --name rg-uniassist-dev --yes --no-wait
   ```

---

## 6. Recommended Local Development Strategy

To preserve cloud credits for final presentation and evaluation:
- Run PostgreSQL locally using Docker (`docker compose up -d db`) or local SQLite fallback (`USE_SQLITE_FALLBACK=True`).
- Run the FastAPI backend locally (`uvicorn app.main:app --reload`).
- Run the React frontend locally (`npm run dev`).
- Only connect to Azure OpenAI and Azure AI Search for actual model and search query execution.
