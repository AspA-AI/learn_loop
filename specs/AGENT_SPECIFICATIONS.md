# Learn Loop - Agent Specifications

## 1. Overview
Learn Loop uses a multi-agent approach to handle the complex task of age-appropriate explanation and child comprehension assessment.

---

## 2. Explainer Agent

### 2.1 Purpose
Generates age-appropriate, micro-learning content grounded in the selected concept and student age.

### 2.2 System Prompt Strategy
- **Role**: A world-class educator specialized in child development for ages 6-10.
- **Constraints**:
  - Max 3 sentences per explanation.
  - No complex jargon without an immediate analogy.
  - Stay strictly within the current topic.
- **Cognitive Framing**:
  - **Age 6**: Use "Magical/Physical" framing. (e.g., "The wind is like a big giant blowing on the trees.")
  - **Age 8**: Use "Cause-and-Effect" framing. (e.g., "The wind moves because the air gets warm and wants to spread out.")
  - **Age 10**: Use "Systemic/Scientific" framing. (e.g., "Wind is caused by differences in air pressure between warm and cold areas.")

---

## 3. Evaluator Agent

### 3.1 Purpose
Analyzes the child's response to determine their level of understanding without using formal tests.

### 3.2 Classification Logic
The agent outputs one of the following states:
1. **`understood`**: The child correctly applies the concept or explains it in their own words.
2. **`partial`**: The child has the right idea but misses a key component or has a slight misconception.
3. **`confused`**: The child expresses frustration, asks an unrelated question, or fundamentally misunderstands the analogy.

### 3.3 Prompt Strategy
- **Input**: Current Concept + Current Analogy + Child's Message.
- **Output**: JSON object with `state` and `reasoning`.

---

## 4. Insight Agent

### 4.1 Purpose
Aggregates session logs into structured, professional reports for parents.

### 4.2 Responsibilities
- **Summarization**: Convert raw chat logs into a narrative of the child's curiosity.
- **Highlighting**: Identify specific "Aha!" moments.
- **Guidance**: Provide offline activities that reinforce what the child learned.

---

## 5. RAG Integration (Weaviate)

### 5.1 Hybrid Retrieval Strategy
The system follows a **"Curriculum-First, Internal-Knowledge-Second"** logic:
1.  **Retrieve**: Search Weaviate for specific concept alignment and analogies.
2.  **Evaluate**: If relevant results are found (above a similarity threshold), the **Explainer Agent** is strictly grounded in these materials.
3.  **Fallback**: If no results are found (e.g., empty vector store, no uploaded docs), the **Explainer Agent** uses its internal pre-trained knowledge while maintaining the defined age-appropriate cognitive framing.

### 5.2 Content Grounding (When available)
Before the **Explainer Agent** speaks, the system queries Weaviate for:
1.  **Curriculum Alignment**: How should "Gravity" be taught according to the standard for a 2nd grader?
2.  **Safety Guardrails**: Are there any sensitive topics to avoid for this concept?

### 5.3 Schema for Weaviate
- **Collection**: `EducationalContent`
- **Properties**: `concept`, `age_range`, `explanation_text`, `analogy_pool`, `source_citation`.

