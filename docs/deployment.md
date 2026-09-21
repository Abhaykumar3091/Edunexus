# UniAssist AI — Azure Deployment Guide

## 1. Target Azure Architecture

UniAssist AI is designed for containerized deployment on **Azure Container Apps** with **Azure Database for PostgreSQL (Flexible Server)**, leveraging **Azure AI Foundry**, **Azure OpenAI**, **Azure AI Search**, **Azure Blob Storage**, and **Azure Key Vault**.

---

## 2. Recommended Cost-Effective Deployment Topology

```
Azure Resource Group: rg-uniassist-prod (Region: East US / Central India)
│
├── Azure Container Apps Environment (Consumption Plan - Auto-scales to 0)
│   ├── uniassist-backend (FastAPI Python 3.11 container)
│   └── uniassist-frontend (React Nginx SPA container)
│
├── Azure Database for PostgreSQL Flexible Server
│   └── Compute: Burstable B1ms (1 vCore, 2 GiB RAM, 32 GiB storage)
│
├── Microsoft Azure AI Foundry / OpenAI
│   ├── gpt-4o-mini (Standard Pay-as-you-go deployment)
│   └── text-embedding-3-small (Standard Pay-as-you-go deployment)
│
├── Azure AI Search
│   └── Tier: Basic (Supports vector search and semantic ranker)
│
├── Azure Storage Account (Standard LRS)
│   └── Container: university-documents
│
├── Azure Key Vault (Standard Tier)
│   └── Secrets: DATABASE-URL, JWT-SECRET, AZURE-OPENAI-KEY, AZURE-SEARCH-KEY
│
└── Application Insights
    └── Daily Volume Cap: 0.5 GB/day
```

---

## 3. Deployment Steps (Azure CLI)

### Step 1: Create Resource Group
```bash
az group create --name rg-uniassist-prod --location eastus
```

### Step 2: Deploy Container Registry (ACR)
```bash
az acr create --resource-group rg-uniassist-prod --name acruniassistprod --sku Basic --admin-enabled true
```

### Step 3: Build & Push Images
```bash
az acr build --registry acruniassistprod --image uniassist-backend:v1.0.0 ./backend
az acr build --registry acruniassistprod --image uniassist-frontend:v1.0.0 ./frontend
```

### Step 4: Deploy Azure Container Apps Environment & Apps
```bash
az containerapp env create --name ca-env-uniassist --resource-group rg-uniassist-prod --location eastus

# Deploy Backend Container App
az containerapp create \
  --name uniassist-backend \
  --resource-group rg-uniassist-prod \
  --environment ca-env-uniassist \
  --image acruniassistprod.azurecr.io/uniassist-backend:v1.0.0 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3

# Deploy Frontend Container App
az containerapp create \
  --name uniassist-frontend \
  --resource-group rg-uniassist-prod \
  --environment ca-env-uniassist \
  --image acruniassistprod.azurecr.io/uniassist-frontend:v1.0.0 \
  --target-port 80 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 2
```
