import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { learningApi, authApi, type ChildCreate, type ChildUpdate, type ParentLogin, type ParentRegister } from '../../services/api';

interface ChildProfile {
  id: string;
  name: string;
  age_level: 6 | 8 | 10;
  avatar: string;
  learningCode: string;
  target_topic?: string;
  learning_language?: string;
}

interface ParentProfile {
  id: string;
  email: string;
  name?: string;
  preferred_language?: string;
}

interface UserState {
  role: 'parent' | 'child' | null;
  currentChild: ChildProfile | null;
  profiles: ChildProfile[];
  parentProfile: ParentProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginError: string | null;
}

const initialState: UserState = {
  role: null,
  currentChild: null,
  profiles: [],
  parentProfile: null,
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

export const parentLogin = createAsyncThunk('user/parentLogin', async (data: ParentLogin, { rejectWithValue }) => {
  try {
    return await authApi.login(data);
  } catch (error: any) {
    // Extract error message from axios error response
    const errorMessage = error?.response?.data?.detail || 
                        error?.message || 
                        'Login failed. Please check your email and password.';
    return rejectWithValue(errorMessage);
  }
});

export const parentRegister = createAsyncThunk('user/parentRegister', async (data: ParentRegister, { rejectWithValue }) => {
  try {
    return await authApi.register(data);
  } catch (error: any) {
    // Extract error message from axios error response
    const errorMessage = error?.response?.data?.detail || 
                        error?.message || 
                        'Registration failed. Please try again.';
    return rejectWithValue(errorMessage);
  }
});

export const checkAuth = createAsyncThunk('user/checkAuth', async () => {
  if (authApi.isAuthenticated()) {
    // If token exists, fetch profile to ensure it's still valid
    try {
      const profile = await authApi.getProfile();
      return profile;
    } catch (error) {
      authApi.logout();
      return null;
    }
  }
  return null;
});

export const updateParentProfile = createAsyncThunk('user/updateParentProfile', async (data: { name?: string; preferred_language?: string }) => {
  return await learningApi.updateParentProfile(data);
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
      authApi.logout();
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
      })
      .addCase(parentLogin.pending, (state) => {
        state.isLoading = true;
        state.loginError = null;
      })
      .addCase(parentLogin.fulfilled, (state, action) => {
        state.isLoading = false;
        state.role = 'parent';
        state.isAuthenticated = true;
        state.loginError = null;
        state.parentProfile = {
          id: action.payload.parent_id,
          email: action.payload.email,
          preferred_language: action.payload.preferred_language
        };
      })
      .addCase(parentLogin.rejected, (state, action) => {
        state.isLoading = false;
        // Error message is now in action.payload (from rejectWithValue)
        state.loginError = (action.payload as string) || 'Login failed. Please check your email and password.';
      })
      .addCase(parentRegister.pending, (state) => {
        state.isLoading = true;
        state.loginError = null;
      })
      .addCase(parentRegister.fulfilled, (state, action) => {
        state.isLoading = false;
        state.role = 'parent';
        state.isAuthenticated = true;
        state.loginError = null;
        state.parentProfile = {
          id: action.payload.parent_id,
          email: action.payload.email,
          preferred_language: action.payload.preferred_language
        };
      })
      .addCase(parentRegister.rejected, (state, action) => {
        state.isLoading = false;
        // Error message is now in action.payload (from rejectWithValue)
        state.loginError = (action.payload as string) || 'Registration failed. Please try again.';
      })
      .addCase(checkAuth.fulfilled, (state, action) => {
        if (action.payload) {
          state.isAuthenticated = true;
          state.role = 'parent';
          state.parentProfile = action.payload;
        }
      })
      .addCase(updateParentProfile.fulfilled, (state, action) => {
        if (state.parentProfile) {
          state.parentProfile = {
            ...state.parentProfile,
            ...action.payload
          };
        }
      });
  },
});

export const { setRole, loginWithCode, logout } = userSlice.actions;
export default userSlice.reducer;
