import React, { useEffect, useMemo, useRef, useState } from 'react';
import { MessageCircle, X, Send, ChevronDown, ChevronUp } from 'lucide-react';
import { learningApi } from '../../services/api';
import { useAppDispatch, useAppSelector } from '../../hooks/store';
import { fetchChildren } from '../user/userSlice';

type AdvisorMsg = {
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
};

type ChildSessionRow = {
  session_id: string;
  concept: string;
  created_at: string;
  ended_at?: string | null;
};

const formatDate = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return iso;
  }
};

const bubbleClass = (role: AdvisorMsg['role']) =>
  role === 'user'
    ? 'bg-indigo-600 text-white ml-auto'
    : 'bg-white/80 text-slate-800 mr-auto border border-white/60';

const ParentAdvisorWidget: React.FC = () => {
  const dispatch = useAppDispatch();
  const { profiles, role } = useAppSelector((s) => s.user);

  const [open, setOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChildSessionRow[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const [focusSessionId, setFocusSessionId] = useState<string | null>(null);
  const [chatId, setChatId] = useState<string | null>(null);
  const [conversationHistory, setConversationHistory] = useState<Array<{ id: string; child_id: string; created_at: string; focus_session_id?: string | null; children?: { id: string; name: string; age_level: number } | null; message_count: number }>>([]);
  const [conversationHistoryLoading, setConversationHistoryLoading] = useState(false);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [viewingHistory, setViewingHistory] = useState(false);

  const [messages, setMessages] = useState<AdvisorMsg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [noteToast, setNoteToast] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  const children = useMemo(() => profiles || [], [profiles]);

  useEffect(() => {
    if (role === 'parent' && children.length === 0) {
      dispatch(fetchChildren());
    }
  }, [role, children.length, dispatch]);

  useEffect(() => {
    if (!selectedChildId && children.length > 0) {
      setSelectedChildId(children[0].id);
    }
  }, [children, selectedChildId]);

  useEffect(() => {
    if (!open) return;
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [open, messages.length]);

  // Load sessions for selected child when widget opens or child changes
  useEffect(() => {
    const run = async () => {
      if (!open || !selectedChildId) return;
      setSessionsLoading(true);
      try {
        const res = await learningApi.getChildSessions(selectedChildId);
        setSessions(res.sessions || []);
      } catch {
        setSessions([]);
      } finally {
        setSessionsLoading(false);
      }
    };
    run();
  }, [open, selectedChildId]);

  // Load conversation history when widget opens
  useEffect(() => {
    const run = async () => {
      if (!open) return;
      setConversationHistoryLoading(true);
      try {
        const res = await learningApi.listAdvisorChats(selectedChildId || undefined);
        setConversationHistory(res.chats || []);
      } catch {
        setConversationHistory([]);
      } finally {
        setConversationHistoryLoading(false);
      }
    };
    run();
  }, [open, selectedChildId]);

  // Start / restart chat whenever selected child or focus session changes (explicit reset)
  // OR load a selected conversation from history
  useEffect(() => {
    const run = async () => {
      if (!open || !selectedChildId) return;
      
      // If viewing a conversation from history, load it instead of starting new
      if (selectedConversationId && viewingHistory) {
        try {
          const res = await learningApi.getAdvisorChat(selectedConversationId);
          setChatId(res.chat.id);
          setMessages((res.messages || []).map((m) => ({ role: m.role, content: m.content, created_at: m.created_at })));
          setFocusSessionId(res.chat.focus_session_id || null);
        } catch {
          setChatId(null);
          setMessages([{ role: 'assistant', content: 'Unable to load conversation. Please try again.' }]);
        }
        return;
      }
      
      // Otherwise start a new chat
      try {
        // Start chat only when child is selected / widget opens. Session focus changes should not reset chat.
        const res = await learningApi.startAdvisorChat(selectedChildId, null);
        setChatId(res.chat_id);
        setMessages((res.messages || []).map((m) => ({ role: m.role, content: m.content, created_at: m.created_at })));
        setViewingHistory(false);
        setSelectedConversationId(null);
      } catch {
        setChatId(null);
        setMessages([{ role: 'assistant', content: 'Unable to start advisor chat right now. Please try again.' }]);
      }
    };
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, selectedChildId, selectedConversationId, viewingHistory]);

  // Update focus session in-place (same child, same chat)
  useEffect(() => {
    const run = async () => {
      if (!open || !chatId) return;
      try {
        await learningApi.updateAdvisorChatFocus(chatId, focusSessionId);
        if (focusSessionId) {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `Okay — I’ll use the selected session as context (${focusSessionId.slice(0, 8)}…).` },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: 'Okay — we’ll discuss overall progress (no specific session selected).' },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'I couldn’t switch the session context right now. Please try again.' },
        ]);
      }
    };
    run();
  }, [open, chatId, focusSessionId]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || !chatId || sending) return;

    setInput('');
    setSending(true);

    // Optimistic UI
    setMessages((prev) => [...prev, { role: 'user', content: text }]);

    try {
      const res = await learningApi.sendAdvisorMessage(chatId, text);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.assistant_message }]);
      if (res.appended_notes?.length) {
        setNoteToast(`Saved ${res.appended_notes.length} new guidance note(s) for this child.`);
        window.setTimeout(() => setNoteToast(null), 4000);
      }
      
      // Refresh conversation history to update message counts
      try {
        const historyRes = await learningApi.listAdvisorChats(selectedChildId || undefined);
        setConversationHistory(historyRes.chats || []);
      } catch {
        // Silently fail - not critical
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry—something went wrong sending that. Please try again.' },
      ]);
    } finally {
      setSending(false);
    }
  };

  if (role !== 'parent') return null;

  return (
    <div className="fixed bottom-5 right-5 z-[60]">
      {!open ? (
        <button
          onClick={() => setOpen(true)}
          className="rounded-full shadow-xl bg-indigo-600 hover:bg-indigo-700 text-white w-14 h-14 flex items-center justify-center transition"
          aria-label="Open Advisor Chat"
        >
          <MessageCircle size={22} />
        </button>
      ) : (
        <div className="w-[900px] max-w-[92vw] h-[640px] max-h-[80vh] rounded-2xl overflow-hidden shadow-2xl border border-white/40 bg-white/60 backdrop-blur-xl">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/40 bg-white/40">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center">
                <MessageCircle size={18} />
              </div>
              <div className="leading-tight">
                <div className="font-semibold text-slate-800">Advisor Agent</div>
                <div className="text-xs text-slate-600">
                  {viewingHistory ? 'Viewing previous conversation' : 'Child-scoped chat'}
                  {focusSessionId ? ` • Discussing session ${focusSessionId.slice(0, 8)}…` : ''}
                </div>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="p-2 rounded-xl hover:bg-white/60 transition text-slate-700"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>

          {/* Body */}
          <div className="flex h-[calc(100%-56px)]">
            {/* Sidebar */}
            <div className={`border-r border-white/40 bg-white/35 ${sidebarOpen ? 'w-72' : 'w-14'} transition-all`}>
              <div className="flex items-center justify-between p-3">
                <div className={`text-xs font-semibold text-slate-700 ${sidebarOpen ? 'opacity-100' : 'opacity-0'} transition`}>
                  Children & Sessions
                </div>
                <button
                  onClick={() => setSidebarOpen((v) => !v)}
                  className="p-2 rounded-xl hover:bg-white/60 transition text-slate-700"
                  aria-label="Toggle sidebar"
                >
                  {sidebarOpen ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                </button>
              </div>

              {sidebarOpen && (
                <div className="px-3 pb-3 space-y-4 overflow-y-auto h-[calc(100%-52px)]">
                  {/* Children */}
                  <div>
                    <div className="text-[11px] font-semibold text-slate-600 mb-2">Select child</div>
                    <div className="space-y-1">
                      {children.map((c: any) => (
                        <button
                          key={c.id}
                          onClick={() => {
                            setFocusSessionId(null);
                            setSelectedChildId(c.id);
                            setViewingHistory(false);
                            setSelectedConversationId(null);
                          }}
                          className={[
                            'w-full text-left px-3 py-2 rounded-xl transition border',
                            selectedChildId === c.id
                              ? 'bg-indigo-600 text-white border-indigo-600'
                              : 'bg-white/70 text-slate-800 border-white/60 hover:bg-white',
                          ].join(' ')}
                        >
                          <div className="text-sm font-semibold truncate">{c.name}</div>
                          <div className={`text-[11px] ${selectedChildId === c.id ? 'text-indigo-100' : 'text-slate-500'}`}>
                            Age {c.age_level} • {c.learningCode}
                          </div>
                        </button>
                      ))}
                      {children.length === 0 && (
                        <div className="text-xs text-slate-600 bg-white/60 rounded-xl p-3 border border-white/60">
                          No children found yet.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Previous Conversations */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-[11px] font-semibold text-slate-600">Previous Conversations</div>
                      {conversationHistoryLoading && <div className="text-[11px] text-slate-500">Loading…</div>}
                    </div>
                    <button
                      onClick={() => {
                        setViewingHistory(false);
                        setSelectedConversationId(null);
                        setFocusSessionId(null);
                      }}
                      className={[
                        'w-full text-left px-3 py-2 rounded-xl border transition mb-2',
                        !viewingHistory
                          ? 'bg-violet-600 text-white border-violet-600'
                          : 'bg-white/70 text-slate-800 border-white/60 hover:bg-white',
                      ].join(' ')}
                    >
                      <div className="text-sm font-semibold">New Conversation</div>
                      <div className={`text-[11px] ${!viewingHistory ? 'text-violet-100' : 'text-slate-500'}`}>
                        Start a fresh discussion
                      </div>
                    </button>
                    <div className="space-y-1 max-h-[200px] overflow-y-auto">
                      {conversationHistory.map((conv) => {
                        const childName = conv.children?.name || 'Unknown';
                        const dateStr = formatDate(conv.created_at);
                        return (
                          <button
                            key={conv.id}
                            onClick={() => {
                              setSelectedConversationId(conv.id);
                              setViewingHistory(true);
                            }}
                            className={[
                              'w-full text-left px-3 py-2 rounded-xl transition border',
                              selectedConversationId === conv.id && viewingHistory
                                ? 'bg-violet-600 text-white border-violet-600'
                                : 'bg-white/70 text-slate-800 border-white/60 hover:bg-white',
                            ].join(' ')}
                          >
                            <div className="text-sm font-semibold truncate">{dateStr}</div>
                            <div className={`text-[11px] ${selectedConversationId === conv.id && viewingHistory ? 'text-violet-100' : 'text-slate-500'}`}>
                              {childName} • {conv.message_count} messages
                            </div>
                          </button>
                        );
                      })}
                      {!conversationHistoryLoading && conversationHistory.length === 0 && (
                        <div className="text-xs text-slate-600 bg-white/60 rounded-xl p-3 border border-white/60">
                          No previous conversations yet.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sessions */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-[11px] font-semibold text-slate-600">Discuss a specific session</div>
                      {sessionsLoading && <div className="text-[11px] text-slate-500">Loading…</div>}
                    </div>

                    <button
                      onClick={() => setFocusSessionId(null)}
                      className={[
                        'w-full text-left px-3 py-2 rounded-xl border transition mb-2',
                        !focusSessionId
                          ? 'bg-slate-900 text-white border-slate-900'
                          : 'bg-white/70 text-slate-800 border-white/60 hover:bg-white',
                      ].join(' ')}
                    >
                      <div className="text-sm font-semibold">No specific session</div>
                      <div className={`text-[11px] ${!focusSessionId ? 'text-slate-200' : 'text-slate-500'}`}>
                        General discussion about progress & strategy
                      </div>
                    </button>

                    <div className="space-y-1 max-h-[150px] overflow-y-auto">
                      {(sessions || []).map((s) => (
                        <button
                          key={s.session_id}
                          onClick={() => setFocusSessionId(s.session_id)}
                          className={[
                            'w-full text-left px-3 py-2 rounded-xl transition border',
                            focusSessionId === s.session_id
                              ? 'bg-indigo-600 text-white border-indigo-600'
                              : 'bg-white/70 text-slate-800 border-white/60 hover:bg-white',
                          ].join(' ')}
                        >
                          <div className="text-sm font-semibold truncate">{s.concept}</div>
                          <div className={`text-[11px] ${focusSessionId === s.session_id ? 'text-indigo-100' : 'text-slate-500'}`}>
                            {formatDate(s.created_at)}
                          </div>
                        </button>
                      ))}
                      {selectedChildId && !sessionsLoading && sessions.length === 0 && (
                        <div className="text-xs text-slate-600 bg-white/60 rounded-xl p-3 border border-white/60">
                          No completed sessions yet for this child.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Chat */}
            <div className="flex-1 flex flex-col bg-gradient-to-br from-white/50 to-indigo-50/30">
              {noteToast && (
                <div className="px-4 pt-3">
                  <div className="text-xs bg-violet-600 text-white rounded-xl px-3 py-2 shadow">
                    {noteToast}
                  </div>
                </div>
              )}

              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
                {messages.map((m, idx) => (
                  <div key={idx} className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${bubbleClass(m.role)}`}>
                    <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                  </div>
                ))}
                {sending && (
                  <div className="max-w-[75%] rounded-2xl px-4 py-3 shadow-sm bg-white/80 text-slate-800 mr-auto border border-white/60">
                    <div className="text-sm">Thinking…</div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              <div className="border-t border-white/40 p-3 bg-white/35">
                <div className="flex items-end gap-2">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder="Ask about progress, goals, tone, pacing, or a specific session…"
                    className="flex-1 min-h-[44px] max-h-[120px] resize-none rounded-xl border border-white/60 bg-white/80 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-400/60"
                  />
                  <button
                    onClick={handleSend}
                    disabled={!chatId || sending || !input.trim()}
                    className="h-[44px] px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:text-slate-600 text-white font-semibold text-sm flex items-center gap-2 transition"
                  >
                    <Send size={16} />
                    Send
                  </button>
                </div>
                <div className="mt-2 text-[11px] text-slate-500">
                  Switching child or session resets this chat context (by design) so notes attach correctly.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ParentAdvisorWidget;


