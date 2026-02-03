import React, { useEffect, useRef } from 'react';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { store } from './store';
import { useAppSelector, useAppDispatch } from './hooks/store';
import { logout, checkAuth } from './features/user/userSlice';
import { clearLearningState } from './features/learning/learningSlice';
import LandingPage from './LandingPage';
import Sidebar from './components/Sidebar';
import ChatContainer from './features/learning/ChatContainer';
import ParentDashboard from './features/parent/ParentDashboard';
import ParentAdvisorWidget from './features/parent/ParentAdvisorWidget';
import { LogOut } from 'lucide-react';
import './index.css';

const queryClient = new QueryClient();

// Main Layout component that handles the internal view
const DashboardLayout: React.FC = () => {
  const dispatch = useAppDispatch();
  const { i18n, t } = useTranslation();
  const { role, currentChild } = useAppSelector((state) => state.user);
  const { learningLanguage, sessionId } = useAppSelector((state) => state.learning);
  const lastAppliedChildLang = useRef<string | null>(null);

  // Sync i18n language with child's learning language if in child role
  // Priority: learningLanguage from session > currentChild.learning_language
  // This MUST override parent language when child logs in
  useEffect(() => {
    // For children, use learning language from session state or child profile
    const childLanguage = learningLanguage || currentChild?.learning_language;
    
    // If we have a session (sessionId exists), we're in child mode even if role isn't set yet
    const isChildMode = role === 'child' || (sessionId && childLanguage);
    
    if (!isChildMode || !childLanguage) {
      console.log(`🌍 [UI] Child language sync skipped - isChildMode: ${isChildMode}, childLanguage: ${childLanguage}, role: ${role}, sessionId: ${sessionId}`);
      return;
    }

    const langCode = {
      English: 'en',
      German: 'de',
      French: 'fr',
      Portuguese: 'pt',
      Spanish: 'es',
      Italian: 'it',
      Turkish: 'tr',
    }[childLanguage] || 'en';

    const currentLang = i18n.resolvedLanguage || i18n.language;
    const alreadyApplied = lastAppliedChildLang.current === langCode;
    const matchesCurrent = currentLang?.startsWith(langCode);

    console.log(`🌍 [UI] Child language sync check - childLanguage: ${childLanguage}, langCode: ${langCode}, currentLang: ${currentLang}, alreadyApplied: ${alreadyApplied}, matchesCurrent: ${matchesCurrent}`);

    // Force language change if it doesn't match - ALWAYS override parent language for children
    if (!matchesCurrent) {
      lastAppliedChildLang.current = langCode;
      i18n.changeLanguage(langCode).then(() => {
        console.log(`🌍 [UI] ✅ Language successfully changed to ${langCode} (${childLanguage})`);
      }).catch((err) => {
        console.error(`🌍 [UI] ❌ Failed to change language:`, err);
      });
    } else if (!alreadyApplied) {
      // Update ref even if language already matches
      lastAppliedChildLang.current = langCode;
      console.log(`🌍 [UI] Language already set to ${langCode}, updating ref`);
    }
  }, [role, currentChild?.learning_language, learningLanguage, i18n, sessionId]);

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
            <span>{t('nav.sign_out')}</span>
          </button>
        </div>
        <ChatContainer />
      </div>
    );
  }

  // For parents, show sidebar and dashboard
  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8 lg:p-12">
        <div className="max-w-6xl mx-auto h-full">
          <ParentDashboard />
        </div>
      </main>
      <ParentAdvisorWidget />
    </div>
  );
};

const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const { i18n } = useTranslation();
  const { isAuthenticated, parentProfile, role } = useAppSelector((state) => state.user);
  const lastAppliedParentLang = useRef<string | null>(null);

  useEffect(() => {
    // Check if user has a valid token on app load
    dispatch(checkAuth());
  }, [dispatch]);

  // Handle parent preferred language on initial load
  // BUT: Don't override if a child is logged in (child language takes priority)
  useEffect(() => {
    // Skip if child is logged in - child language sync will handle it
    if (role === 'child') {
      lastAppliedParentLang.current = null; // Clear parent lang ref when child logs in
      return;
    }
    
    if (!isAuthenticated || !parentProfile?.preferred_language) {
      // Clear parent lang ref when logged out
      if (!isAuthenticated) {
        lastAppliedParentLang.current = null;
      }
      return;
    }

    const langCode = {
      English: 'en',
      German: 'de',
      French: 'fr',
      Portuguese: 'pt',
      Spanish: 'es',
      Italian: 'it',
      Turkish: 'tr',
    }[parentProfile.preferred_language] || 'en';

    const currentLang = i18n.resolvedLanguage || i18n.language;
    const alreadyApplied = lastAppliedParentLang.current === langCode;
    const matchesCurrent = currentLang?.startsWith(langCode);

    if (!alreadyApplied && !matchesCurrent) {
      lastAppliedParentLang.current = langCode;
      i18n.changeLanguage(langCode);
      console.log(`🌍 [UI] Parent language changed to ${langCode}`);
    }
  }, [isAuthenticated, parentProfile?.preferred_language, i18n, role]);

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
