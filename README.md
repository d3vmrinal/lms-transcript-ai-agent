# AI-Powered LMS Knowledge Retrieval System

## Overview

This project is an end-to-end pipeline for transforming LMS course content into a searchable knowledge base.

The system automates lecture extraction, transcript processing, chunking, embedding generation, vector storage, and semantic retrieval.

Current architecture:

```text
LMS
↓
Playwright Automation
↓
Transcript Extraction
↓
Structured JSON Storage
↓
Cleaning Pipeline
↓
Chunking
↓
Embeddings
↓
ChromaDB
↓
Semantic Retrieval
```

---

## Objectives

Traditional LMS platforms store large amounts of educational content but provide limited search and retrieval capabilities.

This project aims to create an AI-powered learning assistant capable of:

* Extracting lecture content automatically
* Structuring and validating extracted data
* Building a searchable vector knowledge base
* Retrieving relevant lecture information semantically
* Supporting future chatbot-based learning interfaces

---

## Current Features

### LMS Extraction Engine

* Automated LMS navigation using Playwright
* Session persistence
* Nested lecture traversal
* Iframe handling
* Transcript extraction
* Structured JSON generation
* Resume-safe extraction

### Validation and Auditing

* Metadata generation
* Content verification
* Module-level extraction reports
* Coverage auditing

### Cleaning Pipeline

* Schema validation
* Empty-content filtering
* Non-lecture filtering
* Transcript preparation

### Embedding Pipeline

* Transcript chunking
* Lecture ordering via lecture_id
* Embedding generation using Sentence Transformers
* ChromaDB integration

### Retrieval Layer

* Semantic similarity search
* Top-k chunk retrieval
* Foundation for Retrieval-Augmented Generation (RAG)

---

## Repository Structure

```text
lms_bot.py
    LMS extraction engine

module_tree.py
    Extraction auditing and reporting

clean_pipeline.py
    Transcript cleaning and validation

sm_chunk_pipeline.py
st_chunk_pipeline.py
    Chunk generation pipelines

embedder.py
    Embedding generation

chroma_db.py
    ChromaDB management

query.py
    Semantic retrieval interface
```

---

## Technology Stack

* Python
* Playwright
* Sentence Transformers
* ChromaDB
* Scikit-learn

---

## Future Work

### Phase 1

* Extraction stabilization
* Enhanced validation
* Improved reporting

### Phase 2

* Centralized storage layer

### Phase 3

* Advanced vector indexing

### Phase 4

* Retrieval-Augmented Generation (RAG)

### Phase 5

* Streamlit/React chat interface

### Phase 6

* Multi-user learning assistant platform

---

## Status

Current Stage:
Knowledge Ingestion + Retrieval Infrastructure

Next Stage:
Conversational AI Layer
