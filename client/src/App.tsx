import React from 'react';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from './store';
import { useAppSelector } from './hooks/store';
import LandingPage from './LandingPage';
import Sidebar from './components/Sidebar';
import ChatContainer from './features/learning/ChatContainer';
import ParentDashboard from './features/parent/ParentDashboard';
import './index.css';

const queryClient = new QueryClient();

// Main Layout component that handles the internal view
const DashboardLayout: React.FC = () => {
  const { role } = useAppSelector((state) => state.user);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8 lg:p-12">
        <div className="max-w-6xl mx-auto h-full">
          {role === 'child' ? <ChatContainer /> : <ParentDashboard />}
        </div>
      </main>
    </div>
  );
};

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAppSelector((state) => state.user);

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
