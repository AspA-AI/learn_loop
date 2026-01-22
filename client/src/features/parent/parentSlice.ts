import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi } from '../../services/api';

interface ChildStat {
  child_id: string;
  name: string;
  mastery_count: number;
  mastery_percent: number;
  total_sessions: number;
  total_hours: number;
}

interface ParentInsight {
  summary: string;
  achievements: string[];
  challenges: string[];
  recommended_next_steps: string[];
  children_stats: ChildStat[];
  overall_mastery: number;
  total_sessions: number;
  total_hours: number;
}

interface CurriculumDoc {
  id: string;
  file_name: string;
  file_size?: number;
  created_at: string;
  children: { child_id: string }[];
}

interface ParentState {
  insights: ParentInsight | null;
  curriculum: CurriculumDoc[];
  isLoading: boolean;
  error: string | null;
  currentView: 'insights' | 'children' | 'curriculum' | 'reports' | 'settings';
}

const initialState: ParentState = {
  insights: null,
  curriculum: [],
  isLoading: false,
  error: null,
  currentView: 'insights',
};

export const fetchInsights = createAsyncThunk('parent/fetchInsights', async (week?: string) => {
  return await learningApi.getParentInsights(week || '');
});

export const fetchCurriculum = createAsyncThunk('parent/fetchCurriculum', async () => {
  return await learningApi.getCurriculum();
});

export const uploadDocument = createAsyncThunk(
  'parent/uploadDocument', 
  async ({ file, childIds }: { file: File, childIds: string[] }) => {
    return await learningApi.uploadCurriculum(file, childIds);
  }
);

const parentSlice = createSlice({
  name: 'parent',
  initialState,
  reducers: {
    setInsights: (state, action: PayloadAction<ParentInsight>) => {
      state.insights = action.payload;
    },
    setParentLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setParentError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setView: (state, action: PayloadAction<ParentState['currentView']>) => {
      state.currentView = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInsights.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchInsights.fulfilled, (state, action) => {
        state.insights = action.payload;
        state.isLoading = false;
      })
      .addCase(fetchInsights.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch insights';
      })
      .addCase(fetchCurriculum.fulfilled, (state, action) => {
        state.curriculum = action.payload;
      })
      .addCase(uploadDocument.fulfilled, (state) => {
        // Optimistically add or just refresh
        state.isLoading = false;
      })
      .addCase(uploadDocument.pending, (state) => {
        state.isLoading = true;
      });
  }
});

export const { setInsights, setParentLoading, setParentError, setView } = parentSlice.actions;
export default parentSlice.reducer;

