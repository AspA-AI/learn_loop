import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppSelector, useAppDispatch } from '../../hooks/store';
import { fetchChildren, addChild, pinTopic } from '../user/userSlice';
import { fetchInsights, fetchCurriculum, uploadDocument } from './parentSlice';
import { 
  Plus, 
  Key, 
  TrendingUp, 
  Award, 
  Clock, 
  UserPlus,
  ArrowRight,
  BookOpen,
  Settings,
  ShieldCheck,
  Bell,
  Users,
  Target,
  Check,
  Upload,
  FileText,
  X,
  Calendar,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  Trash2,
  CheckCircle2,
  Copy
} from 'lucide-react';
import { learningApi } from '../../services/api';

const GrowthInsights: React.FC = () => {
  const dispatch = useAppDispatch();
  const { insights, isLoading } = useAppSelector((state) => state.parent);
  const { profiles } = useAppSelector((state) => state.user);

  useEffect(() => {
    dispatch(fetchInsights());
  }, [dispatch]);

  if (isLoading) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div className="glass rounded-3xl p-12 shadow-soft text-center">
          <p className="text-slate-600 font-semibold">Loading insights...</p>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="space-y-8 animate-fade-in">
        <div className="glass rounded-3xl p-12 shadow-soft text-center">
          <p className="text-slate-600 font-semibold">No insights available yet. Start a learning session to see progress!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <header>
        <div className="flex items-center gap-2 text-xs font-bold text-indigo-500 uppercase tracking-wider mb-3">
          <TrendingUp size={14} /> Analytics Overview
        </div>
        <h2 className="text-4xl font-black text-slate-800 tracking-tight">Growth Insights</h2>
      </header>

      {/* Learning Summary for Each Child */}
      {insights.children_stats && insights.children_stats.length > 0 ? (
        <div className="space-y-6">
          {insights.children_stats.map((childStat: any) => {
            const childProfile = profiles.find(p => p.id === childStat.child_id);
            const childName = childProfile?.name || 'Child';
            
            return (
              <motion.div
                key={childStat.child_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass rounded-3xl p-8 shadow-soft hover:shadow-glow transition-all"
              >
                <h3 className="text-2xl font-black text-slate-800 mb-4">Learning Summary for {childName}</h3>
                {childStat.latest_report?.summary ? (
                  <p className="text-base font-medium text-slate-600 leading-relaxed mb-6">{childStat.latest_report.summary}</p>
                ) : (
                  <p className="text-base font-medium text-slate-600 leading-relaxed mb-6">
                    {childName} has completed {childStat.total_sessions} learning session{childStat.total_sessions !== 1 ? 's' : ''} 
                    {childStat.total_sessions > 0 ? ` with an average mastery of ${childStat.mastery_percent}%.` : '.'}
                  </p>
                )}
                
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-5 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100">
                    <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-2">Mastery</p>
                    <p className="text-3xl font-black text-indigo-600">{childStat.mastery_percent}%</p>
                  </div>
                  <div className="p-5 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border border-purple-100">
                    <p className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-2">Sessions</p>
                    <p className="text-3xl font-black text-purple-600">{childStat.total_sessions}</p>
                  </div>
                  <div className="p-5 bg-gradient-to-br from-pink-50 to-indigo-50 rounded-2xl border border-pink-100">
                    <p className="text-xs font-bold text-pink-600 uppercase tracking-wider mb-2">Hours</p>
                    <p className="text-3xl font-black text-pink-600">{childStat.total_hours}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <div className="glass rounded-3xl p-8 shadow-soft">
          <h3 className="text-2xl font-black text-slate-800 mb-4">Learning Summary</h3>
          <p className="text-base font-medium text-slate-600 leading-relaxed mb-6">{insights.summary}</p>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="p-5 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100">
              <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-2">Overall Mastery</p>
              <p className="text-3xl font-black text-indigo-600">{insights.overall_mastery}%</p>
            </div>
            <div className="p-5 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border border-purple-100">
              <p className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-2">Total Sessions</p>
              <p className="text-3xl font-black text-purple-600">{insights.total_sessions}</p>
            </div>
            <div className="p-5 bg-gradient-to-br from-pink-50 to-indigo-50 rounded-2xl border border-pink-100">
              <p className="text-xs font-bold text-pink-600 uppercase tracking-wider mb-2">Learning Hours</p>
              <p className="text-3xl font-black text-pink-600">{insights.total_hours}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ChildrenManagement: React.FC = () => {
  const dispatch = useAppDispatch();
  const { profiles, isLoading } = useAppSelector((state) => state.user);
  const { insights } = useAppSelector((state) => state.parent);
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newAge, setNewAge] = useState<6 | 8 | 10>(8);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [loadingEvaluations, setLoadingEvaluations] = useState(false);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [sessionChat, setSessionChat] = useState<any>(null);
  const [loadingChat, setLoadingChat] = useState(false);
  const [viewMode, setViewMode] = useState<'sessions' | 'evaluations' | null>(null);
  
  // Topic management state
  const [childTopics, setChildTopics] = useState<Record<string, any[]>>({});
  const [loadingTopics, setLoadingTopics] = useState<Record<string, boolean>>({});
  const [addingTopic, setAddingTopic] = useState<Record<string, boolean>>({});
  const [addingTopicLoading, setAddingTopicLoading] = useState<Record<string, boolean>>({});
  const [newTopic, setNewTopic] = useState<Record<string, string>>({});
  
  // Copy to clipboard state
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Get stats for each child from insights
  const getChildStats = (childId: string) => {
    if (!insights) return { mastery: 0, hours: 0 };
    const stat = insights.children_stats.find(s => s.child_id === childId);
    return stat ? { mastery: stat.mastery_percent, hours: stat.total_hours } : { mastery: 0, hours: 0 };
  };

  const handleAddChild = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName.trim()) {
      dispatch(addChild({ name: newName, age_level: newAge }));
      setNewName('');
      setIsAdding(false);
    }
  };

  // Load topics for a child
  const loadChildTopics = async (childId: string) => {
    setLoadingTopics(prev => ({ ...prev, [childId]: true }));
    try {
      const topics = await learningApi.getChildTopics(childId);
      setChildTopics(prev => ({ ...prev, [childId]: topics }));
    } catch (error) {
      console.error('Error loading topics:', error);
      setChildTopics(prev => ({ ...prev, [childId]: [] }));
    } finally {
      setLoadingTopics(prev => ({ ...prev, [childId]: false }));
    }
  };

  // Add a new topic
  const handleAddTopic = async (childId: string) => {
    const topicName = newTopic[childId]?.trim();
    if (!topicName) return;
    
    setAddingTopicLoading(prev => ({ ...prev, [childId]: true }));
    try {
      const hasTopics = childTopics[childId] && childTopics[childId].length > 0;
      await learningApi.addChildTopic(childId, topicName, !hasTopics); // Set as active if it's the first topic
      setNewTopic(prev => ({ ...prev, [childId]: '' }));
      setAddingTopic(prev => ({ ...prev, [childId]: false }));
      await loadChildTopics(childId); // Reload topics
    } catch (error: any) {
      console.error('Error adding topic:', error);
      alert(error.response?.data?.detail || 'Failed to add topic');
    } finally {
      setAddingTopicLoading(prev => ({ ...prev, [childId]: false }));
    }
  };

  // Set a topic as active
  const handleActivateTopic = async (childId: string, topicId: string) => {
    try {
      await learningApi.activateTopic(childId, topicId);
      await loadChildTopics(childId); // Reload topics
    } catch (error: any) {
      console.error('Error activating topic:', error);
      alert(error.response?.data?.detail || 'Failed to activate topic');
    }
  };

  // Remove a topic
  const handleRemoveTopic = async (childId: string, topicId: string) => {
    if (!confirm('Are you sure you want to remove this topic? This can only be done if the topic has no sessions.')) {
      return;
    }
    
    try {
      await learningApi.removeChildTopic(childId, topicId);
      await loadChildTopics(childId); // Reload topics
    } catch (error: any) {
      console.error('Error removing topic:', error);
      alert(error.response?.data?.detail || 'Failed to remove topic');
    }
  };

  // Load topics when child card is expanded
  useEffect(() => {
    profiles.forEach(profile => {
      if (!childTopics[profile.id]) {
        loadChildTopics(profile.id);
      }
    });
  }, [profiles]);

  // Copy learning code to clipboard
  const handleCopyCode = async (code: string, childId: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(childId);
      // Reset the copied state after 2 seconds
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = code;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        setCopiedCode(childId);
        setTimeout(() => setCopiedCode(null), 2000);
      } catch (fallbackErr) {
        console.error('Fallback copy failed:', fallbackErr);
      }
      document.body.removeChild(textArea);
    }
  };

  const handleViewSessions = async (childId: string) => {
    setSelectedChildId(childId);
    setViewMode('sessions');
    setLoadingSessions(true);
    try {
      const sessionsData = await learningApi.getChildSessions(childId);
      setSessions(sessionsData.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleViewEvaluations = async (childId: string) => {
    setSelectedChildId(childId);
    setViewMode('evaluations');
    setLoadingEvaluations(true);
    try {
      const evaluationsData = await learningApi.getChildEvaluations(childId);
      setEvaluations(evaluationsData.evaluations || []);
    } catch (error) {
      console.error('Error fetching evaluations:', error);
      setEvaluations([]);
    } finally {
      setLoadingEvaluations(false);
    }
  };

  const handleViewSessionChat = async (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setLoadingChat(true);
    try {
      const chatData = await learningApi.getSessionChat(sessionId);
      setSessionChat(chatData);
    } catch (error) {
      console.error('Error fetching session chat:', error);
      setSessionChat(null);
    } finally {
      setLoadingChat(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-500 uppercase tracking-wider mb-3">
            <Users size={14} /> Profile Management
          </div>
          <h2 className="text-4xl font-black text-slate-800 tracking-tight">Your Children</h2>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-6 py-3 rounded-xl font-bold shadow-lg hover:shadow-glow transition-all"
        >
          <UserPlus size={18} /> Add Child
        </button>
      </header>

      {/* Add Child Form */}
      {isAdding && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-3xl p-8 shadow-soft mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-black text-slate-800">Register a New Child</h3>
            <button
              onClick={() => setIsAdding(false)}
              className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-all"
            >
              <X size={20} className="text-slate-600" />
            </button>
          </div>
          <form onSubmit={handleAddChild} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Child's Name</label>
              <input 
                type="text" 
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                placeholder="e.g. Leo"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Age Level</label>
              <select 
                value={newAge}
                onChange={(e) => setNewAge(Number(e.target.value) as any)}
                className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
              >
                <option value={6}>Age 6 (Early Explorer)</option>
                <option value={8}>Age 8 (Junior Discoverer)</option>
                <option value={10}>Age 10 (Advanced Learner)</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <button type="submit" className="flex-1 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-bold shadow-lg hover:shadow-glow transition-all">Create</button>
              <button type="button" onClick={() => setIsAdding(false)} className="h-12 px-6 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-all">Cancel</button>
            </div>
          </form>
        </motion.div>
      )}

      <div className="space-y-6">
        {profiles.map((profile) => {
          const isExpanded = selectedChildId === profile.id;
          const showSessions = isExpanded && viewMode === 'sessions';
          const showEvaluations = isExpanded && viewMode === 'evaluations';
          const showChat = isExpanded && selectedSessionId;
          
          return (
            <div key={profile.id} className="space-y-4">
              <motion.div
                whileHover={{ scale: 1.01 }}
                className="glass rounded-3xl p-6 shadow-soft hover:shadow-glow transition-all"
              >
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-lg">
                      {profile.name[0]}
                    </div>
                    <div>
                      <h3 className="text-2xl font-black text-slate-800">{profile.name}</h3>
                      <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mt-1">
                        Age {profile.age_level} • <span className="text-indigo-600">Level {profile.age_level === 6 ? 'I' : profile.age_level === 8 ? 'II' : 'III'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-indigo-50 text-indigo-700 px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 border border-indigo-200 group hover:bg-indigo-100 transition-all cursor-pointer"
                       onClick={() => handleCopyCode(profile.learningCode, profile.id)}
                       title="Click to copy learning code">
                    <Key size={14} /> 
                    <span className="font-mono">{profile.learningCode}</span>
                    {copiedCode === profile.id ? (
                      <Check size={14} className="text-emerald-600" />
                    ) : (
                      <Copy size={14} className="text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    )}
                  </div>
                </div>

                {/* Topics Management Section */}
                <div className="mb-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-indigo-600">
                      <Target size={14} /> 
                      <span className="text-xs font-bold uppercase tracking-wider">Learning Topics</span>
                    </div>
                    <button
                      onClick={() => {
                        setAddingTopic(prev => ({ ...prev, [profile.id]: !prev[profile.id] }));
                        setNewTopic(prev => ({ ...prev, [profile.id]: '' }));
                      }}
                      className="text-xs font-bold text-indigo-600 hover:text-indigo-700 transition-colors flex items-center gap-1"
                    >
                      <Plus size={14} /> Add Topic
                    </button>
                  </div>

                  {/* Add Topic Form */}
                  {addingTopic[profile.id] && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="flex gap-2 p-3 bg-indigo-50 rounded-xl border border-indigo-200"
                    >
                      <input
                        type="text"
                        value={newTopic[profile.id] || ''}
                        onChange={(e) => setNewTopic(prev => ({ ...prev, [profile.id]: e.target.value }))}
                        placeholder="Enter new topic..."
                        className="flex-1 h-10 px-4 rounded-lg border-2 border-indigo-200 focus:border-indigo-500 outline-none font-semibold text-sm bg-white"
                        onKeyPress={(e) => e.key === 'Enter' && handleAddTopic(profile.id)}
                        autoFocus
                      />
                      <button
                        onClick={() => handleAddTopic(profile.id)}
                        disabled={addingTopicLoading[profile.id] || !newTopic[profile.id]?.trim()}
                        className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg flex items-center justify-center shadow-lg hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {addingTopicLoading[profile.id] ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Check size={18} />
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setAddingTopic(prev => ({ ...prev, [profile.id]: false }));
                          setNewTopic(prev => ({ ...prev, [profile.id]: '' }));
                        }}
                        className="w-10 h-10 bg-slate-100 text-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-200 transition-all"
                      >
                        <X size={18} />
                      </button>
                    </motion.div>
                  )}

                  {/* Topics List */}
                  {loadingTopics[profile.id] ? (
                    <div className="text-center py-4 text-slate-500 text-sm">Loading topics...</div>
                  ) : childTopics[profile.id] && childTopics[profile.id].length > 0 ? (
                    <div className="space-y-2">
                      {childTopics[profile.id].map((topic: any) => (
                        <div
                          key={topic.id}
                          className={`flex items-center justify-between p-3 rounded-xl border-2 transition-all ${
                            topic.is_active
                              ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-indigo-400 shadow-lg'
                              : 'bg-white border-slate-200 text-slate-700'
                          }`}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            {topic.is_active && <CheckCircle2 size={16} className="text-white" />}
                            <span className={`font-bold ${topic.is_active ? 'text-white' : 'text-slate-800'}`}>
                              {topic.topic}
                            </span>
                            {topic.is_active && (
                              <span className="text-xs bg-white/20 px-2 py-1 rounded-lg font-semibold">
                                Active
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {!topic.is_active && (
                              <button
                                onClick={() => handleActivateTopic(profile.id, topic.id)}
                                className="px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold hover:bg-indigo-200 transition-all"
                              >
                                Set Active
                              </button>
                            )}
                            <button
                              onClick={() => handleRemoveTopic(profile.id, topic.id)}
                              className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-all"
                              title="Remove topic (only if no sessions)"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-slate-500 text-sm bg-slate-50 rounded-xl border border-slate-200">
                      No topics yet. Add a topic to get started!
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 text-center">
                    <Award size={16} className="mx-auto mb-2 text-indigo-600" />
                    <p className="text-2xl font-black text-indigo-600">{getChildStats(profile.id).mastery}%</p>
                    <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Mastery</p>
                  </div>
                  <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border border-purple-100 text-center">
                    <Clock size={16} className="mx-auto mb-2 text-purple-600" />
                    <p className="text-2xl font-black text-purple-600">{getChildStats(profile.id).hours}</p>
                    <p className="text-xs font-bold text-purple-600 uppercase tracking-wider">Hours</p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button 
                    onClick={() => {
                      if (isExpanded && viewMode === 'sessions') {
                        setSelectedChildId(null);
                        setViewMode(null);
                        setSessions([]);
                      } else {
                        handleViewSessions(profile.id);
                      }
                    }}
                    className={`flex-1 h-12 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${
                      showSessions
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg'
                        : 'bg-white border-2 border-indigo-200 text-indigo-600 hover:bg-indigo-50'
                    }`}
                  >
                    <Calendar size={16} /> Sessions
                  </button>
                  <button 
                    onClick={() => {
                      if (isExpanded && viewMode === 'evaluations') {
                        setSelectedChildId(null);
                        setViewMode(null);
                        setEvaluations([]);
                      } else {
                        handleViewEvaluations(profile.id);
                      }
                    }}
                    className={`flex-1 h-12 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${
                      showEvaluations
                        ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg'
                        : 'bg-white border-2 border-purple-200 text-purple-600 hover:bg-purple-50'
                    }`}
                  >
                    <Award size={16} /> Reports
                  </button>
                </div>
              </motion.div>

              {/* Inline Sessions View */}
              {showSessions && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass rounded-3xl p-6 shadow-soft mt-4"
                >
                  <div className="flex items-center justify-between mb-6">
                    <h4 className="text-xl font-black text-slate-800">
                      {profile.name}'s Learning Sessions
                    </h4>
                    <button
                      onClick={() => { setSelectedChildId(null); setViewMode(null); setSessions([]); }}
                      className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-all"
                    >
                      <X size={16} className="text-slate-600" />
                    </button>
                  </div>
                  
                  {loadingSessions ? (
                    <div className="text-center py-12">
                      <p className="text-slate-600 font-semibold">Loading sessions...</p>
                    </div>
                  ) : sessions.length === 0 ? (
                    <div className="text-center py-12 bg-slate-50 rounded-2xl">
                      <p className="text-slate-600 font-semibold">No sessions yet. Start a learning session to see history!</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {(() => {
                        // Group sessions by topic
                        const groupedByTopic: Record<string, any[]> = {};
                        sessions.forEach((session: any) => {
                          const topic = session.concept || 'Unknown Topic';
                          if (!groupedByTopic[topic]) {
                            groupedByTopic[topic] = [];
                          }
                          groupedByTopic[topic].push(session);
                        });

                        return Object.entries(groupedByTopic).map(([topic, topicSessions]) => (
                          <div key={topic} className="space-y-3">
                            <div className="flex items-center gap-3 mb-3">
                              <h5 className="text-lg font-black text-indigo-600">{topic}</h5>
                              <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold">
                                {topicSessions.length} {topicSessions.length === 1 ? 'session' : 'sessions'}
                              </span>
                            </div>
                            <div className="space-y-2 pl-4 border-l-2 border-indigo-200">
                              {topicSessions.map((session) => {
                                const sessionId = session.id || session.session_id;
                                return (
                                <motion.div
                                  key={sessionId}
                                  whileHover={{ scale: 1.01 }}
                                  onClick={() => handleViewSessionChat(sessionId)}
                                  className="bg-white p-4 rounded-xl border-2 border-slate-200 hover:border-indigo-300 cursor-pointer transition-all"
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                      <div className="flex items-center gap-3 mb-2">
                                        <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                                          session.status === 'completed' 
                                            ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' 
                                            : 'bg-blue-100 text-blue-700 border border-blue-200'
                                        }`}>
                                          {session.status === 'completed' ? 'Completed' : 'Active'}
                                        </span>
                                      </div>
                                      <p className="text-sm text-slate-600">
                                        {new Date(session.created_at).toLocaleDateString()} 
                                        {session.ended_at && ` • Ended: ${new Date(session.ended_at).toLocaleDateString()}`}
                                      </p>
                                    </div>
                                    <ArrowRight size={20} className="text-slate-400" />
                                  </div>
                                </motion.div>
                                );
                              })}
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  )}
                </motion.div>
              )}

              {/* Inline Session Chat View */}
              {showChat && sessionChat && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass rounded-3xl p-6 shadow-soft mt-4"
                >
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h4 className="text-xl font-black text-slate-800">Chat Conversation</h4>
                      <p className="text-sm text-slate-600 mt-1">
                        {sessionChat.concept} • {new Date(sessionChat.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={() => { setSelectedSessionId(null); setSessionChat(null); }}
                      className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-all"
                    >
                      <X size={16} className="text-slate-600" />
                    </button>
                  </div>
                  
                  <div className="max-h-96 overflow-y-auto space-y-4 bg-slate-50 rounded-2xl p-4">
                    {loadingChat ? (
                      <div className="text-center py-12">
                        <p className="text-slate-600 font-semibold">Loading chat...</p>
                      </div>
                    ) : (!sessionChat.interactions || sessionChat.interactions.length === 0) ? (
                      <div className="text-center py-12">
                        <p className="text-slate-600 font-semibold">No messages in this session.</p>
                      </div>
                    ) : (
                      (sessionChat.interactions || []).map((interaction: any, idx: number) => (
                        <div
                          key={idx}
                          className={`flex ${interaction.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[80%] p-4 rounded-2xl ${
                              interaction.role === 'user'
                                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-tr-none'
                                : 'bg-white text-slate-800 rounded-tl-none border-2 border-slate-200'
                            }`}
                          >
                            <p className="text-sm leading-relaxed font-medium">{interaction.content}</p>
                            {interaction.transcribed_text && (
                              <div className="mt-2 pt-2 border-t border-white/20 text-xs opacity-80">
                                Voice: "{interaction.transcribed_text}"
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </motion.div>
              )}

              {/* Inline Evaluations View */}
              {showEvaluations && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="glass rounded-3xl p-6 shadow-soft mt-4"
                >
                  <div className="flex items-center justify-between mb-6">
                    <h4 className="text-xl font-black text-slate-800">
                      {profile.name}'s Evaluation Reports
                    </h4>
                    <button
                      onClick={() => { setSelectedChildId(null); setViewMode(null); setEvaluations([]); }}
                      className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-all"
                    >
                      <X size={16} className="text-slate-600" />
                    </button>
                  </div>
                  
                  {loadingEvaluations ? (
                    <div className="text-center py-12">
                      <p className="text-slate-600 font-semibold">Loading evaluations...</p>
                    </div>
                  ) : evaluations.length === 0 ? (
                    <div className="text-center py-12 bg-slate-50 rounded-2xl">
                      <p className="text-slate-600 font-semibold">No completed sessions yet. Start a learning session to see evaluations!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {evaluations.map((evaluationItem, idx) => {
                        const report = evaluationItem.evaluation_report;
                        const masteryLevel = report?.concept_mastery_level || 'beginner';
                        const masteryColors: Record<string, string> = {
                          beginner: 'bg-yellow-100 text-yellow-800 border-yellow-200',
                          developing: 'bg-blue-100 text-blue-800 border-blue-200',
                          proficient: 'bg-green-100 text-green-800 border-green-200',
                          mastered: 'bg-emerald-100 text-emerald-800 border-emerald-200'
                        };

                        return (
                          <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white border-2 border-slate-200 rounded-2xl p-6 space-y-4 hover:shadow-lg transition-all"
                          >
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="flex items-center gap-3 mb-2">
                                  <BookOpen size={18} className="text-indigo-600" />
                                  <h5 className="text-xl font-black text-slate-800">{report?.concept || evaluationItem.concept || 'Unknown Concept'}</h5>
                                </div>
                                <div className="flex items-center gap-4 text-sm text-slate-600">
                                  <div className="flex items-center gap-2">
                                    <Calendar size={14} />
                                    {evaluationItem.ended_at ? new Date(evaluationItem.ended_at).toLocaleDateString() : 'Date unknown'}
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Award size={14} />
                                    {report?.mastery_percent || 0}% Mastery
                                  </div>
                                </div>
                              </div>
                              <div className={`px-3 py-1 rounded-lg border font-bold text-xs uppercase tracking-wider ${masteryColors[masteryLevel] || masteryColors.beginner}`}>
                                {masteryLevel}
                              </div>
                            </div>

                            {report?.summary && (
                              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                <p className="text-slate-700 font-medium leading-relaxed">{report.summary}</p>
                              </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {report?.achievements && report.achievements.length > 0 && (
                                <div className="space-y-2">
                                  <div className="flex items-center gap-2 text-emerald-600">
                                    <CheckCircle size={14} />
                                    <h6 className="text-xs font-bold uppercase tracking-wider">Achievements</h6>
                                  </div>
                                  <ul className="space-y-1">
                                    {report.achievements.map((achievement: string, i: number) => (
                                      <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                                        <span className="text-emerald-600 mt-1">•</span>
                                        <span>{achievement}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {report?.challenges && report.challenges.length > 0 && (
                                <div className="space-y-2">
                                  <div className="flex items-center gap-2 text-orange-600">
                                    <AlertCircle size={14} />
                                    <h6 className="text-xs font-bold uppercase tracking-wider">Areas to Improve</h6>
                                  </div>
                                  <ul className="space-y-1">
                                    {report.challenges.map((challenge: string, i: number) => (
                                      <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                                        <span className="text-orange-600 mt-1">•</span>
                                        <span>{challenge}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>

                            {report?.recommended_next_steps && report.recommended_next_steps.length > 0 && (
                              <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100 space-y-2">
                                <div className="flex items-center gap-2 text-indigo-600">
                                  <Lightbulb size={14} />
                                  <h6 className="text-xs font-bold uppercase tracking-wider">Recommended Next Steps</h6>
                                </div>
                                <ul className="space-y-1">
                                  {report.recommended_next_steps.map((step: string, i: number) => (
                                    <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                                      <span className="text-indigo-600 mt-1">→</span>
                                      <span>{step}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </motion.div>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          );
        })}
        
        {!isAdding && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={() => setIsAdding(true)}
            className="group glass border-2 border-dashed border-slate-300 p-12 rounded-3xl flex flex-col items-center justify-center gap-4 hover:border-indigo-400 hover:bg-indigo-50/50 transition-all min-h-[200px] w-full"
          >
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-white group-hover:shadow-glow transition-all">
              <Plus size={28} />
            </div>
            <p className="font-bold text-slate-600 group-hover:text-indigo-600">Register New Child</p>
          </motion.button>
        )}
      </div>
    </div>
  );
};

const CurriculumExplorer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { profiles } = useAppSelector((state) => state.user);
  const { curriculum, isLoading } = useAppSelector((state) => state.parent);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [assignedChildIds, setAssignedChildIds] = useState<string[]>([]);

  useEffect(() => {
    dispatch(fetchCurriculum());
  }, [dispatch]);

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile && assignedChildIds.length > 0) {
      dispatch(uploadDocument({ file: selectedFile, childIds: assignedChildIds }))
        .then(() => {
          setSelectedFile(null);
          setAssignedChildIds([]);
          dispatch(fetchCurriculum());
        });
    }
  };

  const toggleChild = (id: string) => {
    setAssignedChildIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-10 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-secondary mb-2">
            <BookOpen size={12} /> Resource Center
          </div>
          <h2 className="text-4xl font-black text-primary tracking-tight">Curriculum Alignment</h2>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Form */}
        <div className="lg:col-span-1 bg-white p-8 rounded-[2.5rem] shadow-sm border border-border">
          <h3 className="text-xl font-black text-primary mb-6 flex items-center gap-2">
            <Upload size={20} className="text-secondary" /> Upload Document
          </h3>
          
          <form onSubmit={handleUpload} className="space-y-6">
            <div className="border-2 border-dashed border-border rounded-2xl p-8 text-center hover:border-secondary transition-all cursor-pointer relative">
              <input 
                type="file" 
                className="absolute inset-0 opacity-0 cursor-pointer" 
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <div className="space-y-2">
                <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center mx-auto text-muted-foreground">
                  <FileText size={24} />
                </div>
                <p className="text-sm font-bold text-primary">
                  {selectedFile ? selectedFile.name : 'Click to select PDF or Text'}
                </p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-black">Max 10MB</p>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground px-1">
                Assign to Children {assignedChildIds.length > 0 && `(${assignedChildIds.length} selected)`}
              </label>
              {profiles.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No children registered yet. Add a child first!</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {profiles.map(p => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => toggleChild(p.id)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                        assignedChildIds.includes(p.id) 
                          ? 'bg-secondary text-white border-secondary shadow-md' 
                          : 'bg-white text-muted-foreground border-border hover:bg-muted'
                      }`}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              )}
              {selectedFile && assignedChildIds.length === 0 && (
                <p className="text-xs text-amber-600 font-bold">⚠️ Please select at least one child to assign this curriculum to.</p>
              )}
            </div>

            <button
              type="submit"
              disabled={!selectedFile || assignedChildIds.length === 0 || isLoading}
              className="w-full h-14 bg-primary text-white rounded-xl font-black shadow-lg hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : selectedFile && assignedChildIds.length === 0 ? 'Select Children First' : 'Upload & Ground AI'}
            </button>
          </form>
        </div>

        {/* Document List */}
        <div className="lg:col-span-2 bg-white p-8 rounded-[2.5rem] shadow-sm border border-border">
          <h3 className="text-xl font-black text-primary mb-6">Grounded Knowledge Base</h3>
          <div className="space-y-4">
            {curriculum.length === 0 ? (
              <div className="text-center py-20 opacity-30">
                <FileText size={48} className="mx-auto mb-4" />
                <p className="font-black uppercase tracking-widest text-sm">No documents grounded yet</p>
              </div>
            ) : (
              curriculum.map(doc => (
                <div key={doc.id} className="p-5 bg-muted/30 rounded-2xl border border-border/50 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-secondary border border-border shadow-sm">
                      <FileText size={20} />
                    </div>
                    <div>
                      <p className="font-black text-primary leading-none mb-1">{doc.file_name}</p>
                      <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">
                        Grounded for: {doc.children?.map(c => profiles.find(p => p.id === c.child_id)?.name).filter(Boolean).join(', ') || 'Nobody'}
                      </p>
                    </div>
                  </div>
                  <button className="p-2 text-muted-foreground hover:text-red-500 transition-colors">
                    <X size={18} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const PortalSettings: React.FC = () => {
  return (
    <div className="space-y-10 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-secondary mb-2">
            <Settings size={12} /> Preferences
          </div>
          <h2 className="text-4xl font-black text-primary tracking-tight">Portal Settings</h2>
        </div>
      </header>

      <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-border space-y-8">
        <div className="flex items-center justify-between p-6 bg-muted/30 rounded-2xl">
          <div>
            <p className="font-bold text-primary">Email Notifications</p>
            <p className="text-sm text-muted-foreground">Receive weekly growth summaries</p>
          </div>
          <div className="w-12 h-6 bg-secondary rounded-full relative cursor-pointer">
            <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
          </div>
        </div>
        
        <div className="flex items-center justify-between p-6 bg-muted/30 rounded-2xl">
          <div>
            <p className="font-bold text-primary">AI Grounding Strictness</p>
            <p className="text-sm text-muted-foreground">Level of adherence to curriculum</p>
          </div>
          <div className="flex gap-2">
            {['Flexible', 'Standard', 'Strict'].map((level) => (
              <button key={level} className={`px-4 py-2 rounded-lg text-xs font-bold ${level === 'Standard' ? 'bg-primary text-white' : 'bg-white border border-border text-muted-foreground'}`}>
                {level}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 border-t border-border mt-8 flex justify-end">
          <button className="flex items-center gap-2 text-red-500 font-bold hover:bg-red-50 p-3 rounded-xl transition-all">
            <ShieldCheck size={18} /> Reset Learning Memories
          </button>
        </div>
      </div>
    </div>
  );
};

const ParentDashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { currentView } = useAppSelector((state) => state.parent);

  useEffect(() => {
    dispatch(fetchChildren());
    dispatch(fetchInsights());
  }, [dispatch]);

  const renderView = () => {
    switch (currentView) {
      case 'insights': return <GrowthInsights />;
      case 'children': return <ChildrenManagement />;
      case 'curriculum': return <CurriculumExplorer />;
      case 'settings': return <PortalSettings />;
      default: return <GrowthInsights />;
    }
  };

  return (
    <div className="h-full">
      {renderView()}
    </div>
  );
};

export default ParentDashboard;
