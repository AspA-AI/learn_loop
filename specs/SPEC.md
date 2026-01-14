# Learn Loop - Main Specification

## 1. Project Overview

### 1.1 Purpose
Learn Loop is a parent-led, cognitively aware AI learning companion. Designed for homeschoolers and active parents, it allows adults to curate their child's educational journey by pinning target topics and uploading specific curriculum documents that ground the AI's explanations.

### 1.2 Key Features
- **Mission Control (Parent Hub)**: Parents set the "Target Topic" and "Age Level" for their children, ensuring the AI stays on the desired lesson plan.
- **Learning Code Entry**: Children access their personalized workspace via a unique 6-character code (e.g., `LEO-782`), removing the need for child-managed passwords.
- **Homeschool Grounding (RAG)**: Parents can upload curriculum PDFs or lesson plans. The AI retrieves context *only* from the documents assigned to that specific child.
- **Age-Adaptive Framing**: Explanations are dynamically adjusted for ages 6, 8, and 10 based on the parent's profile settings.
- **Insight Timeline**: Parents receive "Aha! Moment" reports, detailing exactly when and how their child understood a concept.

## 2. Homeschooling Architecture

### 2.1 The Parent-Child Link
1. **Parent** registers an account and creates a **Child Profile**.
2. **System** generates a unique **Learning Code**.
3. **Parent** pins a **Target Topic** (e.g., "The Solar System") and uploads **Curriculum Documents**.
4. **Child** enters the **Learning Code** on the homepage.
5. **Learn Loop** retrieves the pinned topic and assigned curriculum, starting a session automatically.

### 2.2 Data Isolation
- Curriculum documents are scoped to the `parent_id` and assigned to specific `child_id`s. 
- The AI's RAG (Retrieval Augmented Generation) is strictly filtered to only see the assigned child's curriculum.

## 3. System Architecture

### 3.1 High-Level Architecture
```
┌───────────────────┐       ┌─────────────────────────┐
│   Frontend UI     │       │     Backend (FastAPI)   │
│ (React/TypeScript)│ ◄────►│ (Python/OpenAI Agents)  │
└─────────┬─────────┘       └────────────┬────────────┘
          │                              │
          ▼                              ▼
    ┌───────────┐           ┌─────────────────────────┐
    │ Parent Hub│           │    Supabase (Auth/DB)   │
    │ & Kids App│           │ (Children/Curriculum)   │
    └───────────┘           └────────────┬────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │    Weaviate Vector DB   │
                            │ (Curriculum / Metadata) │
                            └─────────────────────────┘
```

## 4. User Experience & Dashboard Structure

### 4.1 Entry & Authentication
- **Dual Entrance**: The landing page is split into a **Student Access** (Access via Learning Code) and a **Parent Portal** (Access via Email/Password).
- **Learning Codes**: Instead of usernames/passwords, children use a unique, parent-generated **Learning Code** (e.g., `LEO-782`). This ensures privacy and ease of access.
- **Parent-Led Registration**: Parents register their children within the Parent Hub, which generates the unique codes.

### 4.2 The Student Workspace (Professional & Focused)
- **Minimalist Sidebar**: Clean navigation focused on "Current Adventures" and "Past Discoveries."
- **Progress Gauge**: Replaces the "Knowledge Tree" with a sophisticated, data-driven visualization of understanding levels.
- **Voice/Text Toggle**: Integrated dual-mode interaction in a clean, high-contrast chat interface.

### 4.3 The Parent Hub (Strategic Insights)
- **Profile Management**: Parents can create, edit, and view the unique Learning Codes for each of their children.
- **The "Aha!" Timeline**: A visual feed of specific breakthroughs, using professional typography and structured layouts.
- **Curriculum Alignment**: View exactly which academic standards the AI is currently addressing.

## 5. Visual Identity & UI Design

### 5.1 Palette & Typography
- **Primary Color**: **Emerald Green** (`#064e3b`) - represents growth, stability, and intelligence.
- **Secondary Color**: **Crisp White** (`#ffffff`) - for maximum focus and readability.
- **Accent Color**: **Slate Gray** (`#64748b`) - for supportive UI elements and borders.
- **Typography**: Clean, professional Sans-Serif (e.g., Inter or Geist) with clear hierarchical spacing.

### 5.2 Interaction Design
- **Motion**: Subtle fades and scale transitions instead of "bouncy" animations.
- **Cards**: Structured, white cards with soft shadows and thin, sophisticated borders.
- **Icons**: Minimalist line icons (Lucide-React) in professional tones.

## 6. Interaction Flow & Assessment

1.  **Selection**: User (child/parent) selects age level and a concept.
2.  **Initial Explanation**: The **Explainer Agent** generates a short, age-appropriate micro-lesson.
3.  **Child Feedback**: The child responds or asks a question.
4.  **Assessment**: The **Evaluator Agent** classifies the child's response into:
    - `understood`: Move to deeper detail or related concept.
    - `partial`: Re-explain the missing part using a new analogy.
    - `confused`: Reset with a simpler framing or different cognitive level.
5.  **Iteration**: The loop continues until the concept is marked as `understood` or the session ends.

## 5. Responsible AI & Safety
- **Non-Diagnostic**: The system strictly avoids medical or psychological advice.
- **Academic Focus**: Guardrails ensure the conversation remains on the educational topic.
- **Data Privacy**: No PII of the child should be sent to the LLM; session data is anonymized.
- **Grounding**: RAG ensures that facts are sourced from verified educational content in Weaviate.

