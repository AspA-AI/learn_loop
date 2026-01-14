# Learn Loop - Implementation Plan

## Phase 1: Foundation (The "Static" Loop)
**Goal**: Establish the basic interactive capability for age-appropriate explanations.

- [ ] **Backend (FastAPI)**:
    - Set up project structure and poetry/pip environment.
    - Implement `POST /api/v1/sessions/start`.
    - Create basic OpenAI integration with hardcoded "Age 6/8/10" system prompts.
- [ ] **Frontend (React)**:
    - Scaffold Next.js/React app with Tailwind CSS.
    - Build a "Kid-Safe" UI: large text, simple buttons, high contrast.
    - Implement basic chat window for displaying AI explanations.
- [ ] **Milestone**: User can pick "Age 6" and "Rain" and get a 2-sentence explanation.

## Phase 2: The Assessment Engine (The "Loop")
**Goal**: Make the AI react to the child's understanding state.

- [ ] **Agent Logic**:
    - Implement the **Evaluator Agent** for understanding classification.
    - Add state management to the session (tracking the `understanding_state`).
- [ ] **Adaptive Feedback**:
    - Update the **Explainer Agent** to use a "secondary analogy" if the first one results in `partial` or `confused`.
- [ ] **Milestone**: If a child says "I don't get it", the AI automatically tries a simpler explanation.

## Phase 3: Memory & RAG (The "Grounded" Assistant)
**Goal**: Ensure factual accuracy and curriculum alignment using Weaviate.

- [ ] **Infrastructure**:
    - Set up a local/cloud Weaviate instance.
    - Create the `EducationalContent` collection.
- [ ] **RAG Pipeline**:
    - Ingest sample curriculum data for 5 key concepts (Gravity, Rain, Solar System, Plants, Fractions).
    - Implement the retrieval step in the backend before the LLM call.
- [ ] **Milestone**: Explanations use specific analogies retrieved from the knowledge base rather than just LLM internal weights.

## Phase 4: Parent Insights (The "Observer")
**Goal**: Provide value to the parent through data aggregation.

- [ ] **Data Persistence**:
    - Set up a **Supabase (PostgreSQL)** project.
    - Define schemas for `profiles`, `sessions`, and `learning_interactions`.
- [ ] **Insight Generation**:
    - Implement the **Insight Agent** to run a background task once a week.
    - Build the Parent Dashboard UI in React.
- [ ] **Milestone**: Parent can log in and see a summary of their child's "Aha!" moments.

## Phase 5: Safety, Polish & Performance
**Goal**: Finalize for pilot testing.

- [ ] **Safety Layer**:
    - Add OpenAI Moderation API for every input/output.
    - Implement a "Topic Jail" to prevent the AI from talking about non-academic subjects.
- [ ] **Performance**:
    - Add streaming support (WebSockets or SSE) for faster UI response.
    - Optimize token usage by refining prompts.
- [ ] **Milestone**: A fully functional, safe, and responsive prototype ready for a user demo.

