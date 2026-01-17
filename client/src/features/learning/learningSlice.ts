import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi, type StartSessionParams } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'audio';
  transcribedText?: string;
}

interface QuizState {
  active: boolean;
  question: string | null;
  questionNumber: number | null;
  totalQuestions: number | null;
  answers: string[];
  scores: number[];
  completed: boolean;
  totalScore: number | null;
  percentage: number | null;
}

interface LearningState {
  sessionId: string | null;
  childName: string | null;
  ageLevel: 6 | 8 | 10;
  concept: string | null;
  messages: Message[];
  understandingState: 'understood' | 'partial' | 'confused' | null;
  canEndSession: boolean;
  canTakeQuiz: boolean;
  isLoading: boolean;
  error: string | null;
  isEnding: boolean;
  conversationPhase: string | null; // "greeting", "story_explanation", "story_quiz", "academic_explanation", "academic_quiz", "ongoing"
  quiz: QuizState;
}

const initialState: LearningState = {
  sessionId: null,
  childName: null,
  ageLevel: 8,
  concept: null,
  messages: [],
  understandingState: null,
  canEndSession: false,
  canTakeQuiz: false,
  isLoading: false,
  error: null,
  isEnding: false,
  conversationPhase: null,
  quiz: {
    active: false,
    question: null,
    questionNumber: null,
    totalQuestions: null,
    answers: [],
    scores: [],
    completed: false,
    totalScore: null,
    percentage: null,
  },
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

export const endSession = createAsyncThunk(
  'learning/endSession',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { learning: LearningState };
      if (!state.learning.sessionId) throw new Error('No active session');
      
      return await learningApi.endSession(state.learning.sessionId);
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to end session');
    }
  }
);

export const startQuiz = createAsyncThunk(
  'learning/startQuiz',
  async (numQuestions: number = 5, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { learning: LearningState };
      if (!state.learning.sessionId) throw new Error('No active session');
      
      return await learningApi.startQuiz(state.learning.sessionId, numQuestions);
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to start quiz');
    }
  }
);

export const submitQuizAnswer = createAsyncThunk(
  'learning/submitQuizAnswer',
  async (answer: string, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { learning: LearningState };
      if (!state.learning.sessionId) throw new Error('No active session');
      
      return await learningApi.submitQuizAnswer(state.learning.sessionId, answer);
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to submit answer');
    }
  }
);

export const cancelQuiz = createAsyncThunk(
  'learning/cancelQuiz',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { learning: LearningState };
      if (!state.learning.sessionId) throw new Error('No active session');
      
      return await learningApi.cancelQuiz(state.learning.sessionId);
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to cancel quiz');
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
      state.conversationPhase = null;
      state.canEndSession = false;
      state.canTakeQuiz = false;
      state.isLoading = false;
      state.isEnding = false;
      state.quiz = initialState.quiz;
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
        state.conversationPhase = action.payload.conversation_phase || null;
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
        
        // If it was an audio interaction, add the user's transcribed message first
        if (action.meta.arg.audio && action.payload.transcribed_text) {
          state.messages.push({
            role: 'user',
            content: action.payload.transcribed_text,
            type: 'text'
          });
        }

        state.understandingState = action.payload.understanding_state;
        state.canEndSession = action.payload.can_end_session || false;
        state.canTakeQuiz = action.payload.can_take_quiz || false;
        state.conversationPhase = action.payload.conversation_phase || state.conversationPhase;
        
        // Update quiz state if quiz is active
        if (action.payload.quiz_active) {
          state.quiz.active = true;
          state.quiz.question = action.payload.quiz_question || null;
          state.quiz.questionNumber = action.payload.quiz_question_number || null;
          state.quiz.totalQuestions = action.payload.quiz_total_questions || null;
        }
        
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
      })
      .addCase(endSession.pending, (state) => {
        state.isEnding = true;
        state.error = null;
      })
      .addCase(endSession.fulfilled, (state) => {
        state.isEnding = false;
        // Session ended - could redirect or show success message
      })
      .addCase(endSession.rejected, (state, action) => {
        state.isEnding = false;
        state.error = action.payload as string;
      })
      .addCase(startQuiz.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(startQuiz.fulfilled, (state, action) => {
        state.isLoading = false;
        state.quiz.active = true;
        state.quiz.question = action.payload.question;
        state.quiz.questionNumber = action.payload.question_number;
        state.quiz.totalQuestions = action.payload.total_questions;
        state.quiz.completed = false;
        state.quiz.answers = [];
        state.quiz.scores = [];
        
        // Add quiz start message
        if (action.payload.message) {
          state.messages.push({
            role: 'assistant',
            content: action.payload.message,
            type: 'text',
          });
        }
      })
      .addCase(startQuiz.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(submitQuizAnswer.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(submitQuizAnswer.fulfilled, (state, action) => {
        state.isLoading = false;
        
        // Store answer and score
        if (state.quiz.answers.length < (state.quiz.questionNumber || 0)) {
          state.quiz.answers.push(action.payload.feedback || '');
          state.quiz.scores.push(action.payload.score || 0);
        }
        
        if (action.payload.quiz_completed) {
          state.quiz.completed = true;
          state.quiz.active = false;
          state.quiz.totalScore = action.payload.total_score;
          state.quiz.percentage = action.payload.percentage;
          state.canEndSession = action.payload.can_end_session;
          state.canTakeQuiz = action.payload.can_take_another_quiz;
          
          // Add completion message (already saved to DB by backend)
          if (action.payload.message) {
            state.messages.push({
              role: 'assistant',
              content: action.payload.message,
              type: 'text',
            });
          }
        } else {
          // Move to next question
          state.quiz.question = action.payload.next_question;
          state.quiz.questionNumber = action.payload.question_number;
          
          // Add feedback and next question message (already saved to DB by backend)
          if (action.payload.message) {
            state.messages.push({
              role: 'assistant',
              content: action.payload.message,
              type: 'text',
            });
          }
        }
      })
      .addCase(submitQuizAnswer.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(cancelQuiz.fulfilled, (state) => {
        state.quiz = initialState.quiz;
      });
  }
});

export const { setSession, addMessage, setUnderstanding, setAgeLevel, setLoading, setError, clearLearningState } = learningSlice.actions;
export default learningSlice.reducer;
