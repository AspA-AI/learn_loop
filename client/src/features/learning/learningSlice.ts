import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi, type StartSessionParams } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'audio';
  transcribedText?: string;
}

interface LearningState {
  sessionId: string | null;
  childName: string | null;
  ageLevel: 6 | 8 | 10;
  concept: string | null;
  messages: Message[];
  understandingState: 'understood' | 'partial' | 'confused' | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: LearningState = {
  sessionId: null,
  childName: null,
  ageLevel: 8,
  concept: null,
  messages: [],
  understandingState: null,
  isLoading: false,
  error: null,
};

export const startLearningSession = createAsyncThunk(
  'learning/startSession',
  async (params: StartSessionParams, { rejectWithValue }) => {
    try {
      return await learningApi.startSession(params);
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to start session');
    }
  }
);

export const submitInteraction = createAsyncThunk(
  'learning/submitInteraction',
  async (params: { message?: string; audio?: File }, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { learning: LearningState };
      if (!state.learning.sessionId) throw new Error('No active session');
      
      return await learningApi.interact({
        sessionId: state.learning.sessionId,
        ...params
      });
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to send message');
    }
  }
);

const learningSlice = createSlice({
  name: 'learning',
  initialState,
  reducers: {
    setSession: (state, action: PayloadAction<{ id: string; concept: string; initialExplanation: string }>) => {
      state.sessionId = action.payload.id;
      state.concept = action.payload.concept;
      state.messages = [{ role: 'assistant', content: action.payload.initialExplanation, type: 'text' }];
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },
    setUnderstanding: (state, action: PayloadAction<LearningState['understandingState']>) => {
      state.understandingState = action.payload;
    },
    setAgeLevel: (state, action: PayloadAction<LearningState['ageLevel']>) => {
      state.ageLevel = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearLearningState: (state) => {
      state.sessionId = null;
      state.childName = null;
      state.messages = [];
      state.concept = null;
      state.understandingState = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(startLearningSession.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(startLearningSession.fulfilled, (state, action) => {
        state.isLoading = false;
        state.sessionId = action.payload.session_id;
        state.childName = action.payload.child_name;
        state.concept = action.payload.concept;
        state.ageLevel = action.payload.age_level;
        state.messages = [{ 
          role: 'assistant', 
          content: action.payload.initial_explanation, 
          type: 'text' 
        }];
      })
      .addCase(startLearningSession.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(submitInteraction.pending, (state, action) => {
        state.isLoading = true;
        if (action.meta.arg.message) {
          state.messages.push({
            role: 'user',
            content: action.meta.arg.message,
            type: 'text'
          });
        }
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.isLoading = false;
        state.understandingState = action.payload.understanding_state;
        state.messages.push({
          role: 'assistant',
          content: action.payload.agent_response,
          type: 'text',
          transcribedText: action.payload.transcribed_text
        });
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  }
});

export const { setSession, addMessage, setUnderstanding, setAgeLevel, setLoading, setError, clearLearningState } = learningSlice.actions;
export default learningSlice.reducer;
