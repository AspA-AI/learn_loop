import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useAppDispatch, useAppSelector } from './hooks/store';
import { parentLogin, parentRegister, setRole } from './features/user/userSlice';
import { startLearningSession, setError } from './features/learning/learningSlice';
import { Sparkles, ShieldCheck, BookOpen, Key, Loader2, ArrowRight, GraduationCap, Mail, Lock, User } from 'lucide-react';

const LandingPage: React.FC = () => {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { error: sessionError, isLoading: isSessionLoading, sessionId } = useAppSelector((state) => state.learning);
  const { isLoading: isAuthLoading, loginError } = useAppSelector((state) => state.user);
  const [studentCode, setStudentCode] = useState('');
  const [showParentLogin, setShowParentLogin] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [parentEmail, setParentEmail] = useState('');
  const [parentPassword, setParentPassword] = useState('');
  const [parentName, setParentName] = useState('');

  const handleStudentLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (studentCode.trim()) {
      dispatch(startLearningSession({ learning_code: studentCode }));
    }
  };

  const handleParentAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!parentEmail.trim() || !parentPassword.trim()) return;
    
    if (isRegistering) {
      if (!parentName.trim()) return;
      dispatch(parentRegister({ email: parentEmail, password: parentPassword, name: parentName }));
    } else {
      dispatch(parentLogin({ email: parentEmail, password: parentPassword }));
    }
  };

  useEffect(() => {
    if (studentCode) {
      dispatch(setError(null));
    }
  }, [studentCode, dispatch]);

  useEffect(() => {
    if (sessionId) {
      dispatch(setRole('child'));
    }
  }, [sessionId, dispatch]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50/30 to-purple-50/30 flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-indigo-200/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-12 relative z-10"
      >
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-2xl font-black shadow-lg shadow-indigo-500/30">
            <GraduationCap size={32} />
          </div>
          <h1 className="text-5xl font-black tracking-tight">
            <span className="gradient-text">{t('landing.learn')}</span>
            <span className="text-slate-800">{t('landing.loop')}</span>
          </h1>
        </div>
        <p className="text-slate-600 font-semibold text-center">
          {t('landing.subtitle')}
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl relative z-10">
        {/* Student Entrance */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-3xl p-8 shadow-soft hover:shadow-glow transition-all duration-300"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-white shadow-lg">
              <BookOpen size={28} />
            </div>
            <div>
              <h2 className="text-2xl font-black text-slate-800">{t('landing.student_access')}</h2>
              <p className="text-sm text-slate-600 font-medium">{t('landing.student_id_prompt')}</p>
            </div>
          </div>
          
          <form onSubmit={handleStudentLogin} className="space-y-5">
            <div className="relative">
              <Key className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <input 
                type="text"
                placeholder={t('landing.learning_code_placeholder')}
                value={studentCode}
                onChange={(e) => setStudentCode(e.target.value)}
                disabled={isSessionLoading}
                className={`w-full h-14 pl-12 pr-4 rounded-xl border-2 ${
                  sessionError 
                    ? 'border-error focus:border-error' 
                    : 'border-slate-200 focus:border-indigo-500'
                } bg-white/80 focus:bg-white outline-none font-semibold text-slate-800 transition-all disabled:opacity-50 placeholder:text-slate-400`}
              />
            </div>
            {sessionError && (
              <motion.p 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-error text-sm font-semibold px-2 flex items-center gap-2"
              >
                ⚠️ {sessionError}
              </motion.p>
            )}
            <button
              type="submit"
              disabled={isSessionLoading || !studentCode.trim()}
              className="w-full h-14 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-bold shadow-lg hover:shadow-glow transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {isSessionLoading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>
                  {t('landing.start_learning')} 
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* Parent Portal Entrance */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-3xl p-8 shadow-soft hover:shadow-glow-purple transition-all duration-300 text-white relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center text-white shadow-lg border border-white/20">
                <ShieldCheck size={28} />
              </div>
              <div>
                <h2 className="text-2xl font-black">{t('landing.parent_portal')}</h2>
                <p className="text-sm text-white/80 font-medium">{t('landing.parent_subtitle')}</p>
              </div>
            </div>
            
            <AnimatePresence mode="wait">
              {!showParentLogin ? (
                <motion.div
                  key="button"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-4"
                >
                  <button
                    onClick={() => setShowParentLogin(true)}
                    className="w-full h-14 bg-white text-indigo-600 rounded-xl font-bold shadow-lg hover:bg-white/90 transition-all"
                  >
                    {t('landing.login_register')}
                  </button>
                  <p className="text-center text-xs text-white/60 font-semibold">{t('landing.secure_private')}</p>
                </motion.div>
              ) : (
                <motion.form
                  key="form"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  onSubmit={handleParentAuth}
                  className="space-y-4"
                >
                  {isRegistering && (
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 text-white/60" size={18} />
                      <input
                        type="text"
                        placeholder={t('landing.full_name_placeholder')}
                        value={parentName}
                        onChange={(e) => setParentName(e.target.value)}
                        className="w-full h-12 pl-12 pr-4 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 text-white placeholder:text-white/60 font-semibold outline-none focus:bg-white/30 focus:border-white/50 transition-all"
                      />
                    </div>
                  )}
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-white/60" size={18} />
                    <input
                      type="email"
                      placeholder={t('landing.email')}
                      value={parentEmail}
                      onChange={(e) => setParentEmail(e.target.value)}
                      required
                      className="w-full h-12 pl-12 pr-4 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 text-white placeholder:text-white/60 font-semibold outline-none focus:bg-white/30 focus:border-white/50 transition-all"
                    />
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-white/60" size={18} />
                    <input
                      type="password"
                      placeholder={t('landing.password')}
                      value={parentPassword}
                      onChange={(e) => setParentPassword(e.target.value)}
                      required
                      className="w-full h-12 pl-12 pr-4 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 text-white placeholder:text-white/60 font-semibold outline-none focus:bg-white/30 focus:border-white/50 transition-all"
                    />
                  </div>
                  {isRegistering && (
                    <p className="text-white/70 text-xs px-2 font-medium">
                      {t('landing.password_hint')}
                    </p>
                  )}
                  {loginError && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-200 text-sm font-semibold px-2"
                    >
                      ⚠️ {loginError}
                    </motion.p>
                  )}
                  <button
                    type="submit"
                    disabled={isAuthLoading || !parentEmail.trim() || !parentPassword.trim()}
                    className="w-full h-12 bg-white text-indigo-600 rounded-xl font-bold shadow-lg hover:bg-white/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isAuthLoading ? (
                      <Loader2 className="animate-spin" size={18} />
                    ) : (
                      isRegistering ? t('landing.register') : t('landing.login')
                    )}
                  </button>
                  <div className="flex items-center justify-between text-xs">
                    <button
                      type="button"
                      onClick={() => setIsRegistering(!isRegistering)}
                      className="text-white/80 hover:text-white font-semibold underline"
                    >
                      {isRegistering ? t('landing.have_account') : t('landing.no_account')}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowParentLogin(false);
                        setParentEmail('');
                        setParentPassword('');
                        setParentName('');
                      }}
                      className="text-white/60 hover:text-white/80 font-semibold"
                    >
                      {t('landing.cancel')}
                    </button>
                  </div>
                </motion.form>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mt-12 flex flex-wrap gap-6 justify-center text-slate-600 font-semibold text-sm relative z-10"
      >
        <span className="flex items-center gap-2 px-4 py-2 glass rounded-full">
          <Sparkles size={16} className="text-indigo-500" /> {t('landing.feature_age_adaptive')}
        </span>
        <span className="flex items-center gap-2 px-4 py-2 glass rounded-full">
          <Sparkles size={16} className="text-purple-500" /> {t('landing.feature_curriculum_grounded')}
        </span>
        <span className="flex items-center gap-2 px-4 py-2 glass rounded-full">
          <Sparkles size={16} className="text-pink-500" /> {t('landing.feature_privacy_first')}
        </span>
      </motion.div>
    </div>
  );
};

export default LandingPage;
