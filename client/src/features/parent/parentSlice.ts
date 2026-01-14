import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi } from '../../services/api';

interface ParentInsight {
  summary: string;
  achievements: string[];
  challenges: string[];
  recommended_next_steps: string[];
}

interface CurriculumDoc {
  id: string;
  file_name: string;
  created_at: string;
  children: { child_id: string }[];
}

interface ParentState {
  insights: ParentInsight | null;
  curriculum: CurriculumDoc[];
  isLoading: boolean;
  error: string | null;
  currentView: 'insights' | 'children' | 'curriculum' | 'settings';
}

const initialState: ParentState = {
  insights: null,
  curriculum: [],
  isLoading: false,
  error: null,
  currentView: 'insights',
};

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
      .addCase(fetchCurriculum.fulfilled, (state, action) => {
        state.curriculum = action.payload;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
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

