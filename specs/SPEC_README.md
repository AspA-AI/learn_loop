# Learn Loop - Specification Documents

## Overview

This directory contains the complete specification for **Learn Loop**, an age-adaptive AI learning assistant. The platform is designed to provide cognitively appropriate explanations for academic concepts, track child understanding, and provide insights to parents.

## Specification Documents

### 1. [SPEC.md](./SPEC.md) - Main Specification
**Purpose**: Comprehensive overview of the system architecture, core concepts, and high-level requirements.

**Contents**:
- System purpose and key features
- Cognitive level definitions (Ages 6, 8, 10)
- High-level architecture (FastAPI, React, Weaviate)
- Understanding classification logic
- Safety and responsible AI alignment

---

### 2. [API_CONTRACTS.md](./API_CONTRACTS.md) - API Contracts
**Purpose**: Detailed technical specifications for backend endpoints.

**Contents**:
- Request/Response schemas for session management
- Interactive learning loop endpoints
- Parent insight retrieval
- WebSocket events for real-time interaction (if applicable)

---

### 3. [AGENT_SPECIFICATIONS.md](./AGENT_SPECIFICATIONS.md) - Agent Specifications
**Purpose**: Detailed logic and prompting strategies for the AI agents.

**Contents**:
- **Explainer Agent**: Age-appropriate framing and analogy selection
- **Evaluator Agent**: Interaction-based understanding assessment
- **Insight Agent**: Parent-facing summary generation

---

### 4. [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Implementation Plan
**Purpose**: Step-by-step roadmap for building the MVP.

**Contents**:
- 5-phase execution strategy
- Task breakdown and priorities
- Technology stack details
- Success criteria for each phase

## Quick Start for Developers

1.  **Understand the Core**: Read [SPEC.md](./SPEC.md) to understand how "cognitive framing" works.
2.  **Backend Setup**: Follow [API_CONTRACTS.md](./API_CONTRACTS.md) to implement the FastAPI routes.
3.  **Agent Logic**: Refer to [AGENT_SPECIFICATIONS.md](./AGENT_SPECIFICATIONS.md) when building the LLM integration.
4.  **Follow the Roadmap**: Use [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) to track progress.

