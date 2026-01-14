import { configureStore } from '@reduxjs/toolkit';
import learningReducer from '../features/learning/learningSlice';
import parentReducer from '../features/parent/parentSlice';
import userReducer from '../features/user/userSlice';

export const store = configureStore({
  reducer: {
    learning: learningReducer,
    parent: parentReducer,
    user: userReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

