-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for Children Profiles (Managed by Parents)
CREATE TABLE IF NOT EXISTS public.children (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL, -- Link to the parent (Supabase Auth ID)
    name TEXT NOT NULL,
    age_level INTEGER NOT NULL CHECK (age_level IN (6, 8, 10)),
    learning_code TEXT UNIQUE NOT NULL, -- e.g. LEO-123
    target_topic TEXT, -- The current concept the parent wants them to study
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Curriculum Documents
CREATE TABLE IF NOT EXISTS public.curriculum_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL,
    file_name TEXT NOT NULL,
    weaviate_collection_id TEXT, -- Reference to the collection in Weaviate
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-Many relationship between Children and Curriculum
CREATE TABLE IF NOT EXISTS public.child_curriculum (
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.curriculum_documents(id) ON DELETE CASCADE,
    PRIMARY KEY (child_id, document_id)
);

-- Table for Learning Sessions
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID REFERENCES public.children(id) ON DELETE CASCADE,
    concept TEXT NOT NULL,
    age_level INTEGER NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for Chat Interactions
CREATE TABLE IF NOT EXISTS public.interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    transcribed_text TEXT, -- If voice input was used
    understanding_state TEXT, -- 'understood', 'partial', 'confused'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for learning_code lookup
CREATE INDEX IF NOT EXISTS idx_children_learning_code ON public.children(learning_code);
