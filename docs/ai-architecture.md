# UniAssist AI — Agentic AI & RAG Architecture

## 1. Core Principles

The UniAssist AI Agent operates under strict academic and privacy requirements:
1. **Zero Hallucination:** The agent must never invent regulations, policies, dates, fees, or personal records. If an answer cannot be grounded in official documents, it must explicitly state that information was not found and direct the student to the appropriate administrative office.
2. **Tool vs Knowledge Routing:**
   - **University Regulations/Policies:** Routed to Azure AI Search / Foundry IQ (e.g. attendance criteria, hostel rules, scholarship deadlines).
   - **Student Transactional Data:** Routed to secure database tools via authenticated student context (e.g. "What is my current attendance?").
   - **Hybrid Reasoning:** Synthesizes tool outputs with policy regulations (e.g. "Am I eligible for exams?" -> fetch student attendance: 82% -> fetch exam policy: 75% -> synthesize: Eligible -> cite Attendance By-Laws).
3. **Cross-Student Security Boundary:** Tools only receive the verified `student_id` extracted from the server-validated JWT session, never from user prompt text.

---

## 2. Decision Matrix

```mermaid
graph TD
    A[Student Query] --> B{Intent Classifier}
    B -->|Policy Question| C[Azure AI Search RAG]
    B -->|Personal Data Question| D[Secure Student Database Tool]
    B -->|Eligibility / Combined Query| E[Execute Tool + Query RAG]
    B -->|General Polite Greeting| F[Conversational Guard]
    
    C --> G[Format Answer with Document Citation]
    D --> H[Format Answer with Verified Student Record]
    E --> I[Synthesize Decision with Document Citation]
    F --> J[Polite Guidance Response]
```

---

## 3. Azure AI Search / Foundry IQ Indexing Pipeline

```mermaid
sequenceDiagram
    participant Admin as University Admin
    participant Blob as Azure Blob Storage
    participant Chunker as Document Processing Pipeline
    participant Search as Azure AI Search (Foundry IQ)
    participant Agent as UniAssist AI Agent

    Admin->>Blob: Upload PDF/DOCX (e.g. Academic_Calendar_2026-27.pdf)
    Blob->>Chunker: Trigger Extraction & Semantic Chunking
    Chunker->>Search: Generate Embeddings (text-embedding-3-small) & Upsert Index
    Note over Search: Index contains chunks with source metadata, category, and timestamps
    Agent->>Search: Hybrid Vector + Semantic Query
    Search-->>Agent: Top K Ranked Chunks with Metadata
    Agent-->>Admin: Verified grounded answer with [Academic Calendar 2026-27]
```
