import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useAppSelector, useAppDispatch } from '../../hooks/store';
import { submitInteraction, endSession, clearLearningState, addMessage, startQuiz, submitQuizAnswer, cancelQuiz } from './learningSlice';
import { logout } from '../user/userSlice';
import ProgressGauge from './ProgressGauge';
import { Mic, Send, Sparkles, BookOpen, Square, CheckCircle, X, Rocket, Star, Brain, Zap, Award, Lightbulb, MessageCircle, Volume2 } from 'lucide-react';
import { learningApi } from '../../services/api';
// COMMENTED OUT: Visual exercise component (keeping for future implementation)
// import TenFramesExercise from '../../components/visual/TenFramesExercise';

const ChatContainer: React.FC = () => {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { sessionId, messages, understandingState, canEndSession, canTakeQuiz, isLoading, isEnding, concept, localizedConcept, conversationPhase, quiz, evaluationReport } = useAppSelector((state) => state.learning);
  const [inputText, setInputText] = useState('');
  const [quizAnswer, setQuizAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // TTS (assistant message playback)
  const ttsUrlByIndexRef = useRef<Record<number, string>>({});
  const [ttsLoadingByIndex, setTtsLoadingByIndex] = useState<Record<number, boolean>>({});
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      try {
        if (currentAudioRef.current) currentAudioRef.current.pause();
      } catch {}
      for (const url of Object.values(ttsUrlByIndexRef.current)) {
        try {
          URL.revokeObjectURL(url);
        } catch {}
      }
    };
  }, []);

  const playAssistantAudio = async (messageIndex: number, text: string) => {
    if (!sessionId) return;
    if (!text?.trim()) return;

    const existingUrl = ttsUrlByIndexRef.current[messageIndex];
    if (existingUrl) {
      try {
        if (currentAudioRef.current) currentAudioRef.current.pause();
      } catch {}
      const a = new Audio(existingUrl);
      currentAudioRef.current = a;
      void a.play();
      return;
    }

    setTtsLoadingByIndex((s) => ({ ...s, [messageIndex]: true }));
    try {
      const blob = await learningApi.tts(sessionId, text, 'alloy');
      const url = URL.createObjectURL(blob);
      ttsUrlByIndexRef.current[messageIndex] = url;

      try {
        if (currentAudioRef.current) currentAudioRef.current.pause();
      } catch {}
      const a = new Audio(url);
      currentAudioRef.current = a;
      void a.play();
    } catch (e) {
      // silently ignore; TTS is an optional convenience
    } finally {
      setTtsLoadingByIndex((s) => ({ ...s, [messageIndex]: false }));
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading, quiz.active]);

  const handleEndSession = async () => {
    try {
      const result = await dispatch(endSession());
      
      if (endSession.fulfilled.match(result)) {
        // No extra chat messages. End the session and return to landing page after a short delay.
        setTimeout(() => {
          dispatch(clearLearningState());
          dispatch(logout());
        }, 5000);
      } else {
        throw new Error('Failed to end session');
      }
    } catch (error) {
      // Keep UI minimal; rely on existing error handling state if needed.
    }
  };

  const handleSend = () => {
    if (inputText.trim()) {
      dispatch(submitInteraction({ message: inputText }));
      setInputText('');
    }
  };

  const handleStartQuiz = async () => {
    try {
      const result = await dispatch(startQuiz(5));
      if (startQuiz.rejected.match(result)) {
        dispatch(addMessage({
          role: 'assistant',
          content: t('child.quiz_start_error'),
          type: 'text'
        }));
      }
    } catch (error) {
      console.error('Error starting quiz:', error);
    }
  };

  const handleSubmitQuizAnswer = () => {
    if (quizAnswer.trim()) {
      dispatch(addMessage({
        role: 'user',
        content: `${t('child.question')} ${quiz.questionNumber}: ${quizAnswer}`,
        type: 'text'
      }));
      dispatch(submitQuizAnswer(quizAnswer));
      setQuizAnswer('');
    }
  };

  const handleCancelQuiz = () => {
    dispatch(cancelQuiz());
    setQuizAnswer('');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        dispatch(submitInteraction({ audio: audioFile }));
      };

      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const getUnderstandingEmoji = () => {
    switch (understandingState) {
      case 'understood': return '🎯';
      case 'partial': return '💡';
      case 'confused': return '🤔';
      default: return '🌟';
    }
  };

  return (
    <div className="flex flex-col h-full relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-indigo-200/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-200/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative z-10 flex flex-col h-full space-y-6 p-6 lg:p-8">
        {/* Creative Header */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between glass rounded-3xl p-6 shadow-soft"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white text-2xl font-black shadow-lg shadow-indigo-500/30">
              <Brain size={28} />
            </div>
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-500 uppercase tracking-wider mb-1">
                <Sparkles size={12} /> {t('child.learning_adventure')}
              </div>
              <h2 className="text-3xl font-black gradient-text">
                {localizedConcept || t('child.getting_ready')}
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-3 glass rounded-2xl px-4 py-2 border border-indigo-200">
            <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
            <span className="text-sm font-bold text-slate-700">{t('child.ai_active')}</span>
          </div>
        </motion.header>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
          {/* Main Chat Area */}
          <div className="lg:col-span-3 flex flex-col glass rounded-3xl shadow-soft overflow-hidden border border-white/50">
            <div 
              ref={chatContainerRef}
              className="flex-1 p-6 overflow-y-auto space-y-4 bg-gradient-to-b from-white/50 to-slate-50/30"
            >
              <AnimatePresence initial={false}>
                {messages.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="h-full flex flex-col items-center justify-center text-center"
                  >
                    <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center text-5xl mb-6 shadow-lg border-2 border-indigo-200">
                      <Rocket size={48} className="text-indigo-600" />
                    </div>
                    <p className="text-lg font-bold text-slate-600 mb-2">{t('child.ready_explore')}</p>
                    <p className="text-sm text-slate-500">{t('child.adventure_begin')}!</p>
                  </motion.div>
                ) : (
                  messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 20, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.role === 'assistant' ? (
                        <div className="flex items-start gap-3 max-w-[85%]">
                          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white shadow-lg flex-shrink-0">
                            <Brain size={18} />
                          </div>
                          <div className="bg-white rounded-3xl rounded-tl-none p-5 shadow-lg border-2 border-indigo-100 relative">
                            <div className="absolute -top-2 -left-2 w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center">
                              <Star size={12} className="text-indigo-500 fill-indigo-500" />
                            </div>
                            <p className="text-base leading-relaxed font-medium text-slate-800">{msg.content}</p>
                            
                            {/* COMMENTED OUT: Visual exercise rendering (keeping for future implementation) */}
                            {/* {msg.type === 'visual_exercise' && msg.visualExercise && (
                              <div className="mt-4">
                                {(() => {
                                  console.log('🎨 [RENDER] Visual exercise detected:', msg.visualExercise);
                                  if (msg.visualExercise.exercise_type === 'ten_frames' && msg.visualExercise.data?.frames) {
                                    return (
                                      <TenFramesExercise
                                        frames={msg.visualExercise.data.frames}
                                        instruction={msg.visualExercise.instruction || 'Complete the equations'}
                                        onComplete={(answers) => {
                                          console.log('Visual exercise completed:', answers);
                                        }}
                                      />
                                    );
                                  } else {
                                    // Fallback: show exercise data for unsupported types
                                    return (
                                      <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-4">
                                        <p className="text-sm font-bold text-yellow-800 mb-2">
                                          Visual Exercise: {msg.visualExercise.exercise_type || 'unknown'}
                                        </p>
                                        <p className="text-xs text-yellow-700">
                                          {msg.visualExercise.instruction || 'Complete the exercise'}
                                        </p>
                                        <pre className="text-xs mt-2 text-yellow-600 overflow-auto">
                                          {JSON.stringify(msg.visualExercise.data, null, 2)}
                                        </pre>
                                      </div>
                                    );
                                  }
                                })()}
                              </div>
                            )} */}
                            
                            <div className="mt-3 flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => playAssistantAudio(idx, msg.content)}
                                disabled={!sessionId || !!ttsLoadingByIndex[idx]}
                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold hover:bg-indigo-100 disabled:opacity-50"
                                title={t('child.listen')}
                              >
                                <Volume2 size={14} />
                                {ttsLoadingByIndex[idx] ? t('child.loading_audio') : t('child.listen')}
                              </button>
                            </div>
                            {msg.transcribedText && (
                              <div className="mt-3 pt-3 border-t border-indigo-100 text-xs font-semibold text-indigo-600 flex items-center gap-2">
                                <Mic size={12} /> {t('child.voice')}: "{msg.transcribedText}"
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-start gap-3 max-w-[85%] flex-row-reverse">
                          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white shadow-lg flex-shrink-0">
                            <MessageCircle size={18} />
                          </div>
                          <div className="bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 rounded-3xl rounded-tr-none p-5 shadow-lg text-white relative">
                            <div className="absolute -top-2 -right-2 w-6 h-6 bg-white/30 rounded-full flex items-center justify-center backdrop-blur-sm">
                              <Zap size={12} className="text-white" />
                            </div>
                            <p className="text-base leading-relaxed font-medium">{msg.content}</p>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
              
              {isLoading && !isEnding && !quiz.active && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="flex items-center gap-3 bg-white rounded-3xl rounded-tl-none p-4 shadow-lg border-2 border-indigo-100">
                    <div className="flex gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce [animation-delay:0.2s]" />
                      <div className="w-2 h-2 rounded-full bg-pink-500 animate-bounce [animation-delay:0.4s]" />
                    </div>
                    <span className="text-sm font-semibold text-slate-600">{t('child.thinking')}</span>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Creative Input Area */}
            <div className="p-6 bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 border-t-2 border-indigo-100 space-y-4">
              {conversationPhase === "greeting" && !quiz.active && !quiz.completed && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  className="bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent" />
                  <div className="relative z-10 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center mx-auto mb-4 border-2 border-white/30">
                      <Rocket size={32} />
                    </div>
                    <p className="font-bold mb-4 text-xl">{t('child.ready_to_start')}</p>
                    <button
                      onClick={() => dispatch(submitInteraction({ message: "ready", displayMessage: t('child.ready_message') }))}
                      disabled={isLoading}
                      className="px-8 py-4 bg-white text-indigo-600 rounded-2xl font-black hover:scale-105 transition-transform shadow-xl disabled:opacity-50 disabled:cursor-not-allowed text-lg"
                    >
                      {t('child.lets_go')}
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Quiz Active UI */}
              {quiz.active && !quiz.completed && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 rounded-3xl p-6 text-white shadow-lg space-y-4 relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16" />
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                          <BookOpen size={20} />
                        </div>
                      <span className="font-bold text-lg">{t('child.practice_quiz')}</span>
                    </div>
                    <button
                      onClick={handleCancelQuiz}
                      disabled={isLoading}
                      className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 backdrop-blur-sm flex items-center justify-center transition-all disabled:opacity-50"
                    >
                      <X size={16} />
                    </button>
                  </div>
                  <div className="bg-white/20 backdrop-blur-sm p-4 rounded-2xl border border-white/30">
                    <div className="text-xs font-bold uppercase tracking-wider mb-2 opacity-90">
                      {t('child.question')} {quiz.questionNumber} {t('child.of')} {quiz.totalQuestions}
                    </div>
                    <p className="text-lg font-semibold mb-4">{quiz.question}</p>
                    <div className="flex gap-3">
                      <textarea
                        value={quizAnswer}
                        onChange={(e) => setQuizAnswer(e.target.value)}
                        placeholder={t('child.type_answer')}
                        disabled={isLoading}
                        className="flex-1 min-h-[48px] max-h-[140px] resize-none px-4 py-3 rounded-xl bg-white/90 border-2 border-white text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-white disabled:opacity-50 font-semibold leading-relaxed"
                      />
                      <button
                        onClick={handleSubmitQuizAnswer}
                        disabled={!quizAnswer.trim() || isLoading}
                        className="px-6 h-12 bg-white text-indigo-700 rounded-xl font-black hover:scale-105 transition-transform shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {t('common.submit')}
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Quiz Completed UI */}
            {quiz.completed && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 rounded-3xl p-6 text-white shadow-lg space-y-4 relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full -mr-20 -mt-20" />
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center border-2 border-white/30">
                      <Award size={24} />
                    </div>
                    <span className="font-black text-2xl">{t('child.quiz_complete')}! 🎉</span>
                  </div>
                  <div className="bg-white/20 backdrop-blur-sm p-4 rounded-2xl border border-white/30 mb-4">
                    <p className="text-2xl font-black mb-1">{t('child.you_scored')} {quiz.percentage}%!</p>
                    <p className="text-sm opacity-90">{t('child.amazing_work')} {concept}!</p>
                  </div>
                  <div className="flex gap-3">
                    {canTakeQuiz && (
                      <button
                        onClick={handleStartQuiz}
                        disabled={isLoading}
                        className="flex-1 h-12 bg-white text-indigo-700 rounded-xl font-black hover:scale-105 transition-transform shadow-lg disabled:opacity-50"
                      >
                        {t('child.another_quiz')}
                      </button>
                    )}
                    <button
                      onClick={handleEndSession}
                      disabled={isLoading || isEnding}
                      className="flex-1 h-12 bg-white/20 hover:bg-white/25 border border-white/30 backdrop-blur-sm text-white rounded-xl font-black hover:scale-105 transition-transform shadow-lg disabled:opacity-50"
                    >
                      {t('common.finish')}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* End Session Options */}
            {!quiz.active && !quiz.completed && canEndSession && !isEnding && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-3xl p-6 text-white shadow-lg space-y-4 relative overflow-hidden ${
                  understandingState === 'understood'
                    ? 'bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500'
                    : understandingState === 'partial'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                    : 'bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500'
                }`}
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16" />
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-3">
                    {understandingState === 'understood' ? (
                      <>
                        <CheckCircle size={24} />
                        <span className="font-black text-xl">{t('child.mastered_this')}! 🎯</span>
                      </>
                    ) : understandingState === 'partial' ? (
                      <>
                        <Lightbulb size={24} />
                        <span className="font-black text-xl">{t('child.great_progress')}! 💡</span>
                      </>
                    ) : (
                      <>
                        <Star size={24} />
                        <span className="font-black text-xl">{t('child.awesome_effort')}! 🌟</span>
                      </>
                    )}
                  </div>
                  <p className="text-sm opacity-90 mb-4">
                    {understandingState === 'understood'
                      ? t('child.what_next')
                      : understandingState === 'partial'
                      ? t('child.keep_practicing')
                      : t('child.take_break')}
                  </p>
                  <div className="flex gap-3">
                    {canTakeQuiz && understandingState === 'understood' && (
                      <button
                        onClick={handleStartQuiz}
                        disabled={isLoading}
                        className="flex-1 h-12 bg-white text-indigo-700 rounded-xl font-black hover:scale-105 transition-transform shadow-lg disabled:opacity-50"
                      >
                        {t('child.practice_quiz')}
                      </button>
                    )}
                    <button
                      onClick={handleEndSession}
                      disabled={isLoading}
                      className={`flex-1 h-12 rounded-xl font-black hover:scale-105 transition-transform shadow-lg disabled:opacity-50 border-2 border-white/30 ${
                        understandingState === 'understood'
                          ? 'bg-violet-600 text-white'
                          : understandingState === 'partial'
                          ? 'bg-amber-600 text-white'
                          : 'bg-indigo-600 text-white'
                      }`}
                    >
                      {t('child.end_session')}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {isEnding && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 rounded-3xl p-4 text-white text-center font-bold flex items-center justify-center gap-3 shadow-lg"
              >
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                <span>{t('child.creating_summary')}...</span>
              </motion.div>
            )}

              {conversationPhase !== "greeting" && !quiz.active && !quiz.completed && !isEnding && (
                <div className="flex gap-3">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isEnding || isLoading}
                    className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg transition-all ${
                      isRecording
                        ? 'bg-gradient-to-br from-red-500 to-pink-600 text-white animate-pulse border-2 border-red-300'
                        : 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white hover:from-indigo-600 hover:to-purple-700 border-2 border-indigo-300'
                    } disabled:opacity-50`}
                  >
                    {isRecording ? <Square size={24} fill="currentColor" /> : <Mic size={24} />}
                  </motion.button>
                  <div className="flex-1 relative">
                    <textarea
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder={isRecording ? t('child.recording') : t('child.type_message')}
                      disabled={isRecording || isLoading || isEnding}
                      className="w-full min-h-[56px] max-h-[160px] resize-none pl-6 pr-16 py-4 rounded-2xl border-2 border-indigo-200 focus:border-indigo-500 outline-none text-base font-semibold transition-all shadow-lg bg-white disabled:opacity-50 placeholder:text-slate-400 leading-relaxed"
                    />
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={handleSend}
                      disabled={!inputText.trim() || isLoading || isEnding}
                      className="absolute right-2 top-2 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center shadow-lg hover:shadow-glow transition-all disabled:opacity-50"
                    >
                      <Send size={18} />
                    </motion.button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar - Progress & Tips */}
          <div className="lg:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass rounded-3xl p-6 shadow-soft border border-white/50"
            >
              <div className="flex items-center gap-2 mb-4">
                <div className="text-2xl">{getUnderstandingEmoji()}</div>
                <h4 className="text-sm font-black text-slate-800 uppercase tracking-wider">
                  {understandingState ? t(`child.${understandingState}`) : t('child.progress')}
                </h4>
              </div>
              <ProgressGauge 
                state={understandingState} 
                masteryPercent={evaluationReport?.mastery_percent ?? null}
              />
            </motion.div>

            {/* Always-available Actions */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.05 }}
              className="bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-12 -mt-12" />
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-9 h-9 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/25">
                    <CheckCircle size={18} className="text-white" />
                  </div>
                  <h4 className="text-sm font-black uppercase tracking-wider">{t('child.actions')}</h4>
                </div>

                <div className="space-y-3">
                  <button
                    onClick={handleStartQuiz}
                    disabled={isLoading || isEnding || quiz.active}
                    className="w-full h-12 rounded-2xl font-black shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-white text-indigo-700 hover:bg-white/90"
                  >
                    {t('child.practice_quiz')}
                  </button>
                  <button
                    onClick={handleEndSession}
                    disabled={isEnding}
                    className="w-full h-12 rounded-2xl font-black shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-white/20 hover:bg-white/25 border border-white/30 backdrop-blur-sm"
                  >
                    {t('child.end_session')}
                  </button>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-12 -mt-12" />
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb size={20} />
                  <h4 className="text-sm font-black uppercase tracking-wider">{t('child.quick_tip')}</h4>
                </div>
                <p className="text-sm font-medium leading-relaxed text-white/90">
                  {t('child.tip_content')} 🧠
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="glass rounded-3xl p-6 shadow-soft border border-white/50"
            >
              <div className="flex items-center gap-2 mb-3">
                <BookOpen size={18} className="text-indigo-600" />
                <h4 className="text-sm font-black text-slate-800 uppercase tracking-wider">{t('child.topic')}</h4>
              </div>
              <p className="text-base font-bold text-slate-700">{localizedConcept || t('common.loading')}</p>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
