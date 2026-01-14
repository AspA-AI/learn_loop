import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppSelector, useAppDispatch } from '../../hooks/store';
import { submitInteraction } from './learningSlice';
import ProgressGauge from './ProgressGauge';
import { Mic, Send, Sparkles, BookOpen, Square } from 'lucide-react';

const ChatContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { messages, understandingState, isLoading, concept } = useAppSelector((state) => state.learning);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsAdding] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const handleSend = () => {
    if (inputText.trim()) {
      dispatch(submitInteraction({ message: inputText }));
      setInputText('');
    }
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
      setIsAdding(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current) {
      mediaRecorder.current.stop();
      setIsAdding(false);
      // Stop all tracks to release microphone
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  return (
    <div className="flex flex-col h-full space-y-8 animate-fade-in font-sans">
      {/* Header Info */}
      <header className="flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-secondary">
            <Sparkles size={12} /> Live Adventure
          </div>
          <h2 className="text-3xl font-black text-primary tracking-tight">
            {concept || 'Initializing Discovery...'}
          </h2>
        </div>
        <div className="bg-white px-5 py-3 rounded-2xl border border-border shadow-sm flex items-center gap-3">
          <div className="w-8 h-8 bg-secondary/10 rounded-lg flex items-center justify-center text-secondary">
            <BookOpen size={18} />
          </div>
          <span className="text-sm font-bold text-primary">Curriculum Grounded</span>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-8 min-h-0">
        {/* Main Chat Area */}
        <div className="lg:col-span-3 flex flex-col bg-white rounded-[2rem] shadow-sm border border-border overflow-hidden">
          <div className="flex-1 p-8 overflow-y-auto space-y-8">
            <AnimatePresence initial={false}>
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-40">
                  <div className="w-16 h-16 bg-muted rounded-2xl mb-6 flex items-center justify-center text-2xl">
                    🔭
                  </div>
                  <p className="text-sm font-bold uppercase tracking-widest">Waiting for discovery to start...</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] p-6 rounded-2xl ${
                      msg.role === 'user' 
                        ? 'bg-primary text-white rounded-tr-none' 
                        : 'bg-muted/50 text-primary rounded-tl-none border border-border'
                    }`}>
                      <p className="text-lg leading-relaxed font-medium">{msg.content}</p>
                      {msg.transcribedText && (
                        <div className="mt-3 pt-3 border-t border-white/10 text-xs font-bold uppercase tracking-widest opacity-60 flex items-center gap-2">
                          <Mic size={12} /> Voice Captured: "{msg.transcribedText}"
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted/50 p-4 rounded-2xl rounded-tl-none flex gap-1.5 border border-border">
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce [animation-delay:0.2s]" />
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
              </div>
            )}
          </div>

          {/* Input Interface */}
          <div className="p-6 bg-muted/30 border-t border-border">
            <div className="flex gap-4">
              <button 
                onClick={isRecording ? stopRecording : startRecording}
                className={`w-14 h-14 rounded-xl border transition-all flex items-center justify-center shadow-sm ${
                  isRecording 
                    ? 'bg-red-500 border-red-600 text-white animate-pulse' 
                    : 'bg-white border-border text-primary hover:text-secondary hover:border-secondary'
                }`}
              >
                {isRecording ? <Square size={24} fill="currentColor" /> : <Mic size={24} />}
              </button>
              <div className="flex-1 relative">
                <input 
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder={isRecording ? "Recording..." : "Ask a question or share what you know..."}
                  disabled={isRecording || isLoading}
                  className="w-full h-14 pl-6 pr-14 rounded-xl border border-border focus:border-primary outline-none text-lg font-medium transition-all shadow-sm disabled:opacity-50"
                />
                <button 
                  onClick={handleSend}
                  disabled={!inputText.trim() || isLoading}
                  className="absolute right-2 top-2 w-10 h-10 rounded-lg bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-all shadow-md disabled:opacity-50"
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Info Panel */}
        <div className="lg:col-span-1 space-y-8">
          <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-border">
            <ProgressGauge state={understandingState} />
          </div>

          <div className="bg-primary p-8 rounded-[2rem] shadow-lg text-white space-y-4">
            <h4 className="text-xs font-black uppercase tracking-[0.2em] text-secondary">Quick Tips</h4>
            <p className="text-sm font-medium leading-relaxed text-white/70">
              Try explaining it in your own words! This helps build stronger connections in your brain.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
