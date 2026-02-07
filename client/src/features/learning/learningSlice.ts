import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi, type StartSessionParams } from '../../services/api';
import { setCurrentChildFromSession } from '../user/userSlice';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'audio'; // COMMENTED OUT: 'visual_exercise' (keeping for future implementation)
  transcribedText?: string;
  // COMMENTED OUT: Visual exercise feature (keeping for future implementation)
  // visualExercise?: {
  //   exercise_type: string;
  //   instruction: string;
  //   data: any;
  // };
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
  localizedConcept: string | null;
  learningLanguage: string | null;
  messages: Message[];
  understandingState: 'understood' | 'partial' | 'confused' | 'procedural' | null;
  canEndSession: boolean;
  canTakeQuiz: boolean;
  isLoading: boolean;
  error: string | null;
  isEnding: boolean;
  conversationPhase: string | null; // "greeting", "story_explanation", "story_quiz", "academic_explanation", "academic_quiz", "ongoing"
  quiz: QuizState;
  sessionStartTime: number | null; // Timestamp when session started (for duration tracking)
  evaluationReport: {
    mastery_percent: number | null;
  } | null; // Evaluation results shown to child after session ends
}

const initialState: LearningState = {
  sessionId: null,
  childName: null,
  ageLevel: 8,
  concept: null,
  localizedConcept: null,
  learningLanguage: null,
  messages: [],
  understandingState: null,
  canEndSession: false,
  canTakeQuiz: false,
  isLoading: false,
  error: null,
  isEnding: false,
  conversationPhase: null,
  sessionStartTime: null,
  evaluationReport: null,
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
  async (params: StartSessionParams, { rejectWithValue, dispatch }) => {
    try {
      const response = await learningApi.startSession(params);
      console.log('🌍 [SESSION START] Response:', { 
        child_id: response.child_id, 
        learning_code: response.learning_code, 
        learning_language: response.learning_language,
        child_name: response.child_name 
      });
      // Also set currentChild in user slice so learning_language is available immediately
      if (response.child_id && response.learning_code && response.learning_language) {
        console.log('🌍 [SESSION START] Dispatching setCurrentChildFromSession');
        dispatch(setCurrentChildFromSession({
          id: String(response.child_id), // Ensure it's a string
          child_name: response.child_name,
          learning_language: response.learning_language,
          learning_code: response.learning_code,
          age_level: response.age_level,
        }));
      } else {
        console.warn('🌍 [SESSION START] Missing required fields:', {
          has_child_id: !!response.child_id,
          has_learning_code: !!response.learning_code,
          has_learning_language: !!response.learning_language,
        });
      }
      return response;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to start session');
    }
  }
);

export const submitInteraction = createAsyncThunk(
  'learning/submitInteraction',
  async (params: { message?: string; audio?: File; displayMessage?: string }, { getState, rejectWithValue }) => {
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
      
      // Calculate duration from start time
      const durationSeconds = state.learning.sessionStartTime 
        ? Math.floor((Date.now() - state.learning.sessionStartTime) / 1000)
        : undefined;
      
      return await learningApi.endSession(state.learning.sessionId, durationSeconds);
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
      state.learningLanguage = null;
      state.canEndSession = false;
      state.canTakeQuiz = false;
      state.isLoading = false;
      state.isEnding = false;
      state.sessionStartTime = null;
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
        state.localizedConcept = action.payload.localized_concept || action.payload.concept;
        state.ageLevel = action.payload.age_level;
        state.conversationPhase = action.payload.conversation_phase || null;
        state.learningLanguage = action.payload.learning_language || null;
        state.sessionStartTime = Date.now(); // Track session start time
        state.understandingState = null;
        state.evaluationReport = null; // Clear previous session's evaluation - no grading until session ends
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
        const displayMessage = action.meta.arg.displayMessage || action.meta.arg.message;
        if (displayMessage) {
          state.messages.push({
            role: 'user',
            content: displayMessage,
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
        
        // COMMENTED OUT: Visual exercise handling (keeping for future implementation)
        // // Check if response includes visual exercise
        // const hasVisualExercise = action.payload.visual_exercise !== null && action.payload.visual_exercise !== undefined;
        // 
        // if (hasVisualExercise) {
        //   console.log('🎨 [FRONTEND] Visual exercise received:', action.payload.visual_exercise);
        // }
        
        state.messages.push({
          role: 'assistant',
          content: action.payload.agent_response,
          type: 'text', // COMMENTED OUT: hasVisualExercise ? 'visual_exercise' : 'text'
          transcribedText: action.payload.transcribed_text
          // COMMENTED OUT: visualExercise: action.payload.visual_exercise || undefined
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
      .addCase(endSession.fulfilled, (state, action) => {
        state.isEnding = false;
        // Extract evaluation results for child display
        const evaluationReport = action.payload?.evaluation_report;
        if (evaluationReport) {
          const masteryPercent = evaluationReport.mastery_percent ?? null;
          
          state.evaluationReport = {
            mastery_percent: masteryPercent,
          };
        }
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
