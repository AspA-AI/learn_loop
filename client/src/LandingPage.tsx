import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppDispatch, useAppSelector } from './hooks/store';
import { setRole } from './features/user/userSlice';
import { startLearningSession, setError } from './features/learning/learningSlice';
import { Sparkles, ShieldCheck, BookOpen, Key, Loader2, ArrowRight } from 'lucide-react';

const LandingPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { error: sessionError, isLoading: isSessionLoading, sessionId, concept } = useAppSelector((state) => state.learning);
  const { isAuthenticated, role } = useAppSelector((state) => state.user);
  const [studentCode, setStudentCode] = useState('');

  const handleStudentLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (studentCode.trim()) {
      dispatch(startLearningSession({ learning_code: studentCode }));
    }
  };

  // Clear error when user starts typing again
  useEffect(() => {
    if (studentCode) {
      dispatch(setError(null));
    }
  }, [studentCode, dispatch]);

  // If a session starts successfully, we automatically mark as authenticated/child
  useEffect(() => {
    if (sessionId) {
      dispatch(setRole('child'));
    }
  }, [sessionId, dispatch]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center font-sans">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-16"
      >
        <div className="w-20 h-20 bg-primary rounded-2xl flex items-center justify-center text-white text-3xl font-black mx-auto mb-8 shadow-2xl">
          LL
        </div>
        <h1 className="text-4xl font-black text-primary tracking-tight mb-3">
          LEARN<span className="text-secondary">LOOP</span>
        </h1>
        <p className="text-muted-foreground font-semibold tracking-wide uppercase text-xs">
          Professional Learning Companion
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 w-full max-w-3xl">
        {/* Student Entrance */}
        <div className="bg-white p-10 rounded-[2rem] shadow-sm border border-border flex flex-col items-center text-left">
          <div className="w-12 h-12 bg-secondary/10 rounded-xl flex items-center justify-center text-secondary mb-6">
            <BookOpen size={24} />
          </div>
          <h2 className="text-2xl font-black text-foreground mb-2">Student Access</h2>
          <p className="text-sm text-muted-foreground mb-8 font-medium">Enter your Learning Code to continue your adventure.</p>
          
          <form onSubmit={handleStudentLogin} className="w-full space-y-4">
            <div className="relative">
              <Key className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <input 
                type="text"
                placeholder="Code (e.g. LEO-782)"
                value={studentCode}
                onChange={(e) => setStudentCode(e.target.value)}
                disabled={isSessionLoading}
                className={`w-full h-14 pl-12 pr-4 rounded-xl border ${sessionError ? 'border-red-500' : 'border-border'} bg-muted/50 focus:border-secondary outline-none font-bold text-lg transition-all disabled:opacity-50`}
              />
            </div>
            {sessionError && (
              <motion.p 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-red-600 text-xs font-bold px-2 flex items-center gap-1"
              >
                ⚠️ {sessionError}
              </motion.p>
            )}
            <button
              type="submit"
              disabled={isSessionLoading}
              className="w-full h-14 bg-secondary text-white rounded-xl font-black shadow-lg hover:bg-secondary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 group"
            >
              {isSessionLoading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>Start Learning <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>
              )}
            </button>
          </form>
        </div>

        {/* Parent Portal Entrance */}
        <div className="bg-primary p-10 rounded-[2rem] shadow-sm flex flex-col items-start text-left text-white">
          <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center text-white mb-6">
            <ShieldCheck size={24} />
          </div>
          <h2 className="text-2xl font-black mb-2">Parent Portal</h2>
          <p className="text-sm text-white/70 mb-10 font-medium">Manage child profiles, view insights, and generate access codes.</p>
          
          <div className="mt-auto w-full space-y-4">
            <button
              onClick={() => dispatch(setRole('parent'))}
              className="w-full h-14 bg-white text-primary rounded-xl font-bold shadow-md hover:bg-white/90 transition-all"
            >
              Sign In to Dashboard
            </button>
            <p className="text-center text-xs text-white/50 font-bold">Secure Professional Access</p>
          </div>
        </div>
      </div>

      <div className="mt-20 flex gap-8 text-muted-foreground font-bold text-[10px] uppercase tracking-[0.2em]">
        <span className="flex items-center gap-2"><Sparkles size={14} className="text-secondary" /> Age-Adaptive</span>
        <span className="flex items-center gap-2"><Sparkles size={14} className="text-secondary" /> Grounded RAG</span>
        <span className="flex items-center gap-2"><Sparkles size={14} className="text-secondary" /> Privacy First</span>
      </div>
    </div>
  );
};

export default LandingPage;
