import React, { useEffect } from 'react';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from './store';
import { useAppSelector, useAppDispatch } from './hooks/store';
import { logout, checkAuth } from './features/user/userSlice';
import { clearLearningState } from './features/learning/learningSlice';
import LandingPage from './LandingPage';
import Sidebar from './components/Sidebar';
import ChatContainer from './features/learning/ChatContainer';
import ParentDashboard from './features/parent/ParentDashboard';
import { LogOut } from 'lucide-react';
import './index.css';

const queryClient = new QueryClient();

// Main Layout component that handles the internal view
const DashboardLayout: React.FC = () => {
  const dispatch = useAppDispatch();
  const { role } = useAppSelector((state) => state.user);

  const handleLogout = () => {
    dispatch(logout());
    dispatch(clearLearningState());
  };

  // For children, full-screen chat with minimal logout button
  if (role === 'child') {
    return (
      <div className="h-screen w-full bg-gradient-to-br from-slate-50 via-indigo-50/30 to-purple-50/30 overflow-hidden relative">
        {/* Minimal top bar for logout */}
        <div className="absolute top-4 right-4 z-50">
          <button
            onClick={handleLogout}
            className="glass rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white/80 transition-all shadow-lg flex items-center gap-2"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
        <ChatContainer />
      </div>
    );
  }

  // For parents, show sidebar and dashboard
  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8 lg:p-12">
        <div className="max-w-6xl mx-auto h-full">
          <ParentDashboard />
        </div>
      </main>
    </div>
  );
};

const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAppSelector((state) => state.user);

  useEffect(() => {
    // Check if user has a valid token on app load
    dispatch(checkAuth());
  }, [dispatch]);

  return isAuthenticated ? <DashboardLayout /> : <LandingPage />;
};

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <AppContent />
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
