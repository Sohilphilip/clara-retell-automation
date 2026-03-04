# Clara AI Retell Automation

## Overview

This project implements an automated pipeline for converting contractor call transcripts into structured configuration artifacts used to configure AI voice agents.

The system processes two types of transcripts:

1. **Demo Call Transcript** – Initial discovery conversation with a contractor.
2. **Onboarding Call Transcript** – Follow-up conversation that contains updates or corrections.

From these transcripts, the system automatically generates:

* **Account Memo v1**
* **Agent Specification v1**
* **Account Memo v2 (after onboarding updates)**
* **Agent Specification v2**
* **Changelog describing configuration differences**

The pipeline uses a **local LLM (Ollama)** to extract structured data from transcripts and combines it with rule-based extraction to improve reliability.
Automation is orchestrated using **n8n**, and processing is triggered automatically when transcripts are uploaded.

The goal is to simulate an internal automation system that prepares configuration data for AI voice agents based on customer discovery calls.

---

## Architecture

The system follows a modular pipeline architecture.

```
Transcript Upload
        │
        ▼
Dataset Folder
        │
        ▼
n8n Workflow Trigger
        │
        ▼
FastAPI Endpoint
        │
        ▼
Batch Runner
        │
        ▼
Extraction Pipeline
        │
        ▼
Account Memo JSON
        │
        ▼
Agent Specification JSON
        │
        ▼
Versioning + Changelog
```

### Key Components

**FastAPI**

* Exposes API endpoints to trigger batch processing.

**n8n**

* Automates workflow execution when new transcripts appear.

**Extraction Engine**

* Uses Ollama LLM + rule-based logic to extract structured fields.

**Schema Validation**

* Ensures outputs match predefined JSON schemas.

**Versioning System**

* Applies onboarding updates and generates changelogs.

---

## Pipeline Design

### Pipeline A – Demo Call Processing

Purpose: Generate initial configuration.

```
Demo Transcript
      │
      ▼
Account Memo v1
      │
      ▼
Agent Spec v1
```

Outputs:

```
outputs/accounts/<account_id>/v1/account_memo.json
outputs/accounts/<account_id>/v1/agent_spec.json
```

---

### Pipeline B – Onboarding Update Processing

Purpose: Update the configuration after onboarding.

```
Onboarding Transcript
        │
        ▼
Extract Updates
        │
        ▼
Apply Patch
        │
        ▼
Account Memo v2
        │
        ▼
Agent Spec v2
        │
        ▼
Changelog
```

Outputs:

```
outputs/accounts/<account_id>/v2/account_memo.json
outputs/accounts/<account_id>/v2/agent_spec.json
outputs/accounts/<account_id>/changes.md
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Sohilphilip/clara-retell-automation
cd clara-retell-automation
```

---

### 2. Install Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Key dependencies include:

* fastapi
* uvicorn
* requests
* jsonschema
* python-docx
* PyPDF2

---

### 3. Start Required Services (Docker)

The project uses Docker to run supporting services such as **n8n automation**.

Start the containers:

```bash
docker compose up -d
```

Verify that containers are running:

```bash
docker ps
```

---

### 4. Install and Run Ollama

Download and install Ollama:

[https://ollama.com](https://ollama.com)

Pull the required model:

```bash
ollama pull qwen2.5:7b
```

Start the model locally:

```bash
ollama run qwen2.5:7b
```

This enables local LLM inference used for transcript extraction.

---

### 5. Start the API Server

Open a new terminal and run:

```bash
uvicorn scripts.api:app --reload --port 8000
```

The API will be available at:

```
http://127.0.0.1:8000
```

Interactive API documentation:

```
http://127.0.0.1:8000/docs
```

---

### 6. Start the Web Dashboard

Open another terminal and run:

```bash
cd webapp
python app.py
```

The web interface allows users to:

* upload transcripts
* trigger pipeline execution
* monitor processing logs
* view generated outputs

---

## Running the Pipeline

Once all services are running:

1. Upload demo transcripts through the **web interface**
2. The **n8n workflow detects new transcripts**
3. The **API triggers batch processing**
4. **Account Memo v1 and Agent Spec v1** are generated
5. Upload onboarding transcripts to generate **v2 updates**

The pipeline processes transcripts stored in:

```
dataset/demo_calls/
dataset/onboarding_calls/
```

---

## Dataset Structure

Place transcripts in the following directories:

```
dataset/
    demo_calls/
        bens_demo.txt
        example_demo.txt

    onboarding_calls/
        bens_onboarding.txt
        example_onboarding.txt
```

Supported transcript formats:

* `.txt`
* `.docx`
* `.pdf`

---

## Output Structure

Generated outputs are stored under:

```
outputs/
    accounts/
        <account_id>/
            v1/
                account_memo.json
                agent_spec.json

            v2/
                account_memo.json
                agent_spec.json

            changes.md
```

### Account Memo

Contains structured operational configuration such as:

* company information
* services offered
* routing rules
* integrations
* operational notes

### Agent Spec

Contains configuration required for AI voice agent behavior.

---

## Limitations

1. **LLM Extraction Accuracy**

   * Local models may miss some information in long conversational transcripts.

2. **Transcript Noise**

   * Sales discussion and product demos introduce irrelevant content.

3. **Context Window Limits**

   * Long transcripts may exceed model context limits.

4. **Rule-Based Heuristics**

   * Some fallback logic relies on keyword detection.

Despite these limitations, the pipeline reliably generates structured configuration artifacts.

---

## Future Improvements

Potential enhancements include:

* Use larger local models (e.g., Qwen 14B)
* Add transcript summarization before extraction
* Implement semantic service classification
* Add diff visualization in the UI
* Improve routing rule extraction
* Add automated evaluation metrics for extraction quality

---

## Summary

This project demonstrates an end-to-end automation system that converts contractor call transcripts into structured AI agent configuration artifacts.

Key capabilities include:

* automated transcript ingestion
* structured data extraction
* schema validation
* configuration versioning
* changelog generation
* workflow automation

The system is designed to simulate a scalable internal tool used to prepare AI voice agent configurations from customer discovery calls.

