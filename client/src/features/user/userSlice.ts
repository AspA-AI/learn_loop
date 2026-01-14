import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi, type ChildCreate, type ChildUpdate } from '../../services/api';

interface ChildProfile {
  id: string;
  name: string;
  age_level: 6 | 8 | 10;
  avatar: string;
  learningCode: string;
  target_topic?: string;
}

interface UserState {
  role: 'parent' | 'child' | null;
  currentChild: ChildProfile | null;
  profiles: ChildProfile[];
  isAuthenticated: boolean;
  isLoading: boolean;
  loginError: string | null;
}

const initialState: UserState = {
  role: null,
  currentChild: null,
  profiles: [],
  isAuthenticated: false,
  isLoading: false,
  loginError: null,
};

export const fetchChildren = createAsyncThunk('user/fetchChildren', async () => {
  return await learningApi.getChildren();
});

export const addChild = createAsyncThunk('user/addChild', async (data: ChildCreate) => {
  return await learningApi.createChild(data);
});

export const pinTopic = createAsyncThunk('user/pinTopic', async ({ childId, topic }: { childId: string, topic: string }) => {
  return await learningApi.updateChild(childId, { target_topic: topic });
});

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setRole: (state, action: PayloadAction<UserState['role']>) => {
      state.role = action.payload;
      state.isAuthenticated = true;
    },
    loginWithCode: (state, action: PayloadAction<string>) => {
      // For now, we search local state, later this should be an API call
      const child = state.profiles.find(p => p.learningCode === action.payload.toUpperCase());
      if (child) {
        state.currentChild = child;
        state.role = 'child';
        state.isAuthenticated = true;
        state.loginError = null;
      } else {
        state.loginError = 'Invalid Learning Code. Please check with your parent!';
      }
    },
    logout: (state) => {
      state.role = null;
      state.currentChild = null;
      state.isAuthenticated = false;
      state.loginError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChildren.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchChildren.fulfilled, (state, action) => {
        state.isLoading = false;
        // Map backend names to local structure if needed
        state.profiles = action.payload.map((p: any) => ({
          ...p,
          avatar: p.name === 'Leo' ? '🦁' : p.name === 'Mia' ? '🐱' : '👤',
          learningCode: p.learning_code // Normalize naming
        }));
      })
      .addCase(addChild.fulfilled, (state, action) => {
        const p = action.payload;
        state.profiles.push({
          ...p,
          avatar: '👤',
          learningCode: p.learning_code
        });
      })
      .addCase(pinTopic.fulfilled, (state, action) => {
        const updated = action.payload;
        const index = state.profiles.findIndex(p => p.id === updated.id);
        if (index !== -1) {
          state.profiles[index].target_topic = updated.target_topic;
        }
      });
  },
});

export const { setRole, loginWithCode, logout } = userSlice.actions;
export default userSlice.reducer;
