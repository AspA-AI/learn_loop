-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables to ensure clean schema update
DROP TABLE IF EXISTS public.interactions CASCADE;
DROP TABLE IF EXISTS public.parent_guidance_notes CASCADE;
DROP TABLE IF EXISTS public.parent_advisor_messages CASCADE;
DROP TABLE IF EXISTS public.parent_advisor_chats CASCADE;
DROP TABLE IF EXISTS public.formal_reports CASCADE;
DROP TABLE IF EXISTS public.sessions CASCADE;
DROP TABLE IF EXISTS public.child_topics CASCADE;
DROP TABLE IF EXISTS public.child_curriculum CASCADE;
DROP TABLE IF EXISTS public.curriculum_documents CASCADE;
DROP TABLE IF EXISTS public.subject_documents CASCADE;
DROP TABLE IF EXISTS public.children CASCADE;
DROP TABLE IF EXISTS public.parents CASCADE;

-- Table for Parents (User Accounts)
CREATE TABLE public.parents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- Hashed password (use bcrypt or similar)
    name TEXT,
    preferred_language TEXT DEFAULT 'English', -- One of: English, German, French, Portuguese, Spanish, Italian, Turkish
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Children Profiles (Managed by Parents)
CREATE TABLE public.children (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES public.parents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age_level INTEGER NOT NULL, -- Any age (removed restriction to allow flexibility)
    learning_code TEXT UNIQUE NOT NULL, -- e.g. LEO-123
    target_topic TEXT, -- The current concept the parent wants them to study
    -- Optional Learning Profile Fields (for personalization)
    learning_style TEXT, -- e.g., 'visual', 'auditory', 'kinesthetic', 'reading/writing'
    interests TEXT[], -- Array of interests/hobbies
    reading_level TEXT, -- e.g., 'beginner', 'intermediate', 'advanced'
    attention_span TEXT, -- e.g., 'short', 'medium', 'long'
    strengths TEXT[], -- Array of academic strengths
    learning_language TEXT DEFAULT 'English', -- One of: English, German, French, Portuguese, Spanish, Italian, Turkish
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Curriculum Documents
CREATE TABLE public.curriculum_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL,
    file_name TEXT NOT NULL,
    storage_path TEXT, -- Path in Supabase Storage (e.g., "curriculum/{parent_id}/{file_name}")
    file_size INTEGER, -- File size in bytes
    weaviate_collection_id TEXT, -- Reference to the collection in Weaviate
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Child Topics (Multiple topics per child, one active at a time)
CREATE TABLE public.child_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    subject TEXT NOT NULL DEFAULT 'General', -- e.g. Math, Science, Language
    topic TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE, -- Only one topic can be active per child
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, subject, topic) -- Prevent duplicate topics for same child in same subject
);

-- Table for Subject Documents (Documents uploaded per subject)
CREATE TABLE public.subject_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL, -- File size in bytes
    storage_path TEXT, -- Path in Supabase Storage
    weaviate_collection_id TEXT, -- Reference to Weaviate collection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, subject, file_name) -- Prevent duplicate files per subject
);

-- Many-to-Many relationship between Children and Curriculum
CREATE TABLE public.child_curriculum (
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.curriculum_documents(id) ON DELETE CASCADE,
    PRIMARY KEY (child_id, document_id)
);

-- Table for Learning Sessions
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    concept TEXT NOT NULL,
    age_level INTEGER NOT NULL,
    status TEXT DEFAULT 'active',
    evaluation_report JSONB, -- Stores the final evaluation report when session ends
    metrics JSONB, -- Stores {accuracy, confidence, persistence, expression} (1-10)
    academic_summary TEXT, -- Exactly 3 sentences for periodic reporting
    duration_seconds INTEGER, -- Actual session duration in seconds (tracked from frontend)
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Formal Reports (Generated for parents/inspectors)
CREATE TABLE public.formal_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES public.parents(id) ON DELETE CASCADE,
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL, -- 'weekly', 'monthly', 'custom'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    content TEXT NOT NULL, -- The formal narrative content
    metrics_summary JSONB, -- Averaged metrics for the period
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Chat Interactions
CREATE TABLE public.interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    transcribed_text TEXT, -- If voice input was used
    understanding_state TEXT, -- 'understood', 'partial', 'confused'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Parent Advisor Chat Sessions (per-child)
CREATE TABLE public.parent_advisor_chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES public.parents(id) ON DELETE CASCADE,
    child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
    focus_session_id UUID REFERENCES public.sessions(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Parent Advisor Chat Messages
CREATE TABLE public.parent_advisor_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id UUID NOT NULL REFERENCES public.parent_advisor_chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user' | 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Parent Guidance Notes (append-only; used to steer future child sessions)
CREATE TABLE public.parent_guidance_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES public.parents(id) ON DELETE CASCADE,
    child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    source_chat_id UUID REFERENCES public.parent_advisor_chats(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_parents_email ON public.parents(email);
CREATE INDEX idx_children_parent_id ON public.children(parent_id);
CREATE INDEX idx_children_learning_code ON public.children(learning_code);
CREATE INDEX idx_child_topics_child_id ON public.child_topics(child_id);
CREATE INDEX idx_child_topics_active ON public.child_topics(child_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_sessions_child_id ON public.sessions(child_id);
CREATE INDEX idx_sessions_concept ON public.sessions(concept);
CREATE INDEX idx_subject_documents_child_subject ON public.subject_documents(child_id, subject);
CREATE INDEX idx_curriculum_documents_parent_id ON public.curriculum_documents(parent_id);
CREATE INDEX idx_child_curriculum_child_id ON public.child_curriculum(child_id);
CREATE INDEX idx_child_curriculum_document_id ON public.child_curriculum(document_id);

CREATE INDEX idx_parent_advisor_chats_parent_child ON public.parent_advisor_chats(parent_id, child_id);
CREATE INDEX idx_parent_advisor_messages_chat_id ON public.parent_advisor_messages(chat_id, created_at);
CREATE INDEX idx_parent_guidance_notes_child_created ON public.parent_guidance_notes(child_id, created_at DESC);
