import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  Copy,
  Edit2
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
  const [newLearningStyle, setNewLearningStyle] = useState<string>('');
  const [newReadingLevel, setNewReadingLevel] = useState<string>('');
  const [newAttentionSpan, setNewAttentionSpan] = useState<string>('');
  const [newInterests, setNewInterests] = useState<string>('');
  const [newStrengths, setNewStrengths] = useState<string>('');
  
  // Edit state
  const [editingChildId, setEditingChildId] = useState<string | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [editAge, setEditAge] = useState<6 | 8 | 10>(8);
  const [editLearningStyle, setEditLearningStyle] = useState<string>('');
  const [editReadingLevel, setEditReadingLevel] = useState<string>('');
  const [editAttentionSpan, setEditAttentionSpan] = useState<string>('');
  const [editInterests, setEditInterests] = useState<string>('');
  const [editStrengths, setEditStrengths] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState(false);
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
  const [childSubjects, setChildSubjects] = useState<Record<string, string[]>>({});
  const [loadingTopics, setLoadingTopics] = useState<Record<string, boolean>>({});
  const [expandedSubjects, setExpandedSubjects] = useState<Record<string, Set<string>>>({}); // childId -> Set of expanded subject names
  const [addingTopic, setAddingTopic] = useState<Record<string, string>>({}); // childId -> subject name where adding topic
  const [addingSubject, setAddingSubject] = useState<Record<string, boolean>>({});
  const [addingTopicLoading, setAddingTopicLoading] = useState<Record<string, boolean>>({});
  const [addingSubjectLoading, setAddingSubjectLoading] = useState<Record<string, boolean>>({});
  const [newTopic, setNewTopic] = useState<Record<string, string>>({});
  const [newSubjectName, setNewSubjectName] = useState<Record<string, string>>({});
  const [uploadingDocument, setUploadingDocument] = useState<Record<string, boolean>>({});
  const [subjectDocuments, setSubjectDocuments] = useState<Record<string, Record<string, any[]>>>({}); // childId -> subject -> documents
  const [selectedTopicForUpload, setSelectedTopicForUpload] = useState<Record<string, string>>({}); // childId -> topic name
  
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
      const interestsArray = newInterests.split(',').map(i => i.trim()).filter(i => i.length > 0);
      const strengthsArray = newStrengths.split(',').map(s => s.trim()).filter(s => s.length > 0);
      
      dispatch(addChild({ 
        name: newName, 
        age_level: newAge,
        learning_style: newLearningStyle || undefined,
        reading_level: newReadingLevel || undefined,
        attention_span: newAttentionSpan || undefined,
        interests: interestsArray.length > 0 ? interestsArray : undefined,
        strengths: strengthsArray.length > 0 ? strengthsArray : undefined
      }));
      setNewName('');
      setNewAge(8);
      setNewLearningStyle('');
      setNewReadingLevel('');
      setNewAttentionSpan('');
      setNewInterests('');
      setNewStrengths('');
      setIsAdding(false);
    }
  };

  const handleStartEdit = (child: any) => {
    setEditingChildId(child.id);
    setEditName(child.name);
    setEditAge(child.age_level as 6 | 8 | 10);
    setEditLearningStyle(child.learning_style || '');
    setEditReadingLevel(child.reading_level || '');
    setEditAttentionSpan(child.attention_span || '');
    setEditInterests(Array.isArray(child.interests) ? child.interests.join(', ') : '');
    setEditStrengths(Array.isArray(child.strengths) ? child.strengths.join(', ') : '');
  };

  const handleCancelEdit = () => {
    setEditingChildId(null);
    setEditName('');
    setEditAge(8);
    setEditLearningStyle('');
    setEditReadingLevel('');
    setEditAttentionSpan('');
    setEditInterests('');
    setEditStrengths('');
  };

  const handleUpdateChild = async (e: React.FormEvent, childId: string) => {
    e.preventDefault();
    if (!editName.trim()) return;
    
    setIsUpdating(true);
    try {
      const interestsArray = editInterests.split(',').map(i => i.trim()).filter(i => i.length > 0);
      const strengthsArray = editStrengths.split(',').map(s => s.trim()).filter(s => s.length > 0);
      
      await learningApi.updateChild(childId, {
        name: editName,
        age_level: editAge,
        learning_style: editLearningStyle || undefined,
        reading_level: editReadingLevel || undefined,
        attention_span: editAttentionSpan || undefined,
        interests: interestsArray.length > 0 ? interestsArray : undefined,
        strengths: strengthsArray.length > 0 ? strengthsArray : undefined
      });
      
      // Refresh children list
      dispatch(fetchChildren());
      handleCancelEdit();
    } catch (error: any) {
      console.error('Error updating child:', error);
      alert(error.response?.data?.detail || 'Failed to update child');
    } finally {
      setIsUpdating(false);
    }
  };

  // Load topics for a child
  const loadChildTopics = async (childId: string) => {
    setLoadingTopics(prev => ({ ...prev, [childId]: true }));
    try {
      const topics = await learningApi.getChildTopics(childId);
      setChildTopics(prev => ({ ...prev, [childId]: topics }));
      // Also load subjects
      const subjects = await learningApi.getChildSubjects(childId);
      setChildSubjects(prev => ({ ...prev, [childId]: subjects }));
    } catch (error) {
      console.error('Error loading topics:', error);
      setChildTopics(prev => ({ ...prev, [childId]: [] }));
    } finally {
      setLoadingTopics(prev => ({ ...prev, [childId]: false }));
    }
  };

  // Add a new subject (creates a placeholder topic to establish the subject)
  const handleAddSubject = async (childId: string) => {
    const subjectName = newSubjectName[childId]?.trim();
    if (!subjectName) return;
    
    setAddingSubjectLoading(prev => ({ ...prev, [childId]: true }));
    try {
      // Create a topic with the same name as the subject to establish the subject
      // The user can then add more topics to this subject
      const hasTopics = childTopics[childId] && childTopics[childId].length > 0;
      await learningApi.addChildTopic(childId, subjectName, subjectName, !hasTopics);
      setNewSubjectName(prev => ({ ...prev, [childId]: '' }));
      setAddingSubject(prev => ({ ...prev, [childId]: false }));
      await loadChildTopics(childId);
    } catch (error: any) {
      console.error('Error adding subject:', error);
      alert(error.response?.data?.detail || 'Failed to add subject');
    } finally {
      setAddingSubjectLoading(prev => ({ ...prev, [childId]: false }));
    }
  };

  // Toggle subject expansion
  const toggleSubject = (childId: string, subjectName: string) => {
    setExpandedSubjects(prev => {
      const childExpanded = prev[childId] || new Set();
      const newSet = new Set(childExpanded);
      if (newSet.has(subjectName)) {
        newSet.delete(subjectName);
      } else {
        newSet.add(subjectName);
      }
      return { ...prev, [childId]: newSet };
    });
  };

  // Add a new topic
  const handleAddTopic = async (childId: string, subjectName: string) => {
    const topicName = newTopic[childId]?.trim();
    if (!topicName) return;
    
    setAddingTopicLoading(prev => ({ ...prev, [childId]: true }));
    try {
      const hasTopics = childTopics[childId] && childTopics[childId].length > 0;
      await learningApi.addChildTopic(childId, topicName, subjectName, !hasTopics);
      setNewTopic(prev => ({ ...prev, [childId]: '' }));
      setAddingTopic(prev => ({ ...prev, [childId]: '' }));
      await loadChildTopics(childId);
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

  // Load subject documents
  const loadSubjectDocuments = async (childId: string, subject: string) => {
    try {
      const response = await learningApi.getSubjectDocuments(childId, subject);
      setSubjectDocuments(prev => ({
        ...prev,
        [childId]: {
          ...(prev[childId] || {}),
          [subject]: response.documents || []
        }
      }));
    } catch (error) {
      console.error('Error loading subject documents:', error);
    }
  };

  // Handle document upload
  const handleUploadDocument = async (childId: string, subject: string, file: File, topic: string) => {
    if (file.size > 10 * 1024 * 1024) {
      alert('File size exceeds 10MB limit');
      return;
    }

    setUploadingDocument(prev => ({ ...prev, [`${childId}-${subject}`]: true }));
    try {
      await learningApi.uploadSubjectDocument(childId, subject, topic, file);
      await loadSubjectDocuments(childId, subject);
      setSelectedTopicForUpload(prev => ({ ...prev, [`${childId}-${subject}`]: '' }));
      alert('Document uploaded and processed successfully!');
    } catch (error: any) {
      console.error('Error uploading document:', error);
      alert(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploadingDocument(prev => ({ ...prev, [`${childId}-${subject}`]: false }));
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
    setSelectedSessionId(null);
    setSessionChat(null);
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
    setSelectedSessionId(null);
    setSessionChat(null);
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
    setSessionChat(null);
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
          <form onSubmit={handleAddChild} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Child's Name *</label>
                <input 
                  type="text" 
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                  className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                  placeholder="e.g. Leo"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Age Level *</label>
                <select 
                  value={newAge}
                  onChange={(e) => setNewAge(Number(e.target.value) as any)}
                  required
                  className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                >
                  <option value={6}>Age 6 (Early Explorer)</option>
                  <option value={8}>Age 8 (Junior Discoverer)</option>
                  <option value={10}>Age 10 (Advanced Learner)</option>
                </select>
              </div>
            </div>

            {/* Learning Profile */}
            <div className="space-y-4 p-4 bg-indigo-50 rounded-xl border border-indigo-200">
              <h4 className="text-sm font-black text-indigo-600 uppercase tracking-wider">Learning Profile (Optional)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Learning Style</label>
                  <select 
                    value={newLearningStyle}
                    onChange={(e) => setNewLearningStyle(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                  >
                    <option value="">Select learning style...</option>
                    <option value="visual">Visual</option>
                    <option value="auditory">Auditory</option>
                    <option value="kinesthetic">Kinesthetic</option>
                    <option value="reading/writing">Reading/Writing</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Reading Level</label>
                  <select 
                    value={newReadingLevel}
                    onChange={(e) => setNewReadingLevel(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                  >
                    <option value="">Select reading level...</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Attention Span</label>
                  <select 
                    value={newAttentionSpan}
                    onChange={(e) => setNewAttentionSpan(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                  >
                    <option value="">Select attention span...</option>
                    <option value="short">Short (5-10 min)</option>
                    <option value="medium">Medium (10-20 min)</option>
                    <option value="long">Long (20+ min)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Interests</label>
                  <input 
                    type="text" 
                    value={newInterests}
                    onChange={(e) => setNewInterests(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                    placeholder="e.g. dinosaurs, space, art (comma-separated)"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Academic Strengths</label>
                  <input 
                    type="text" 
                    value={newStrengths}
                    onChange={(e) => setNewStrengths(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                    placeholder="e.g. math, problem-solving, creativity (comma-separated)"
                  />
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex items-center justify-end gap-3">
              <button type="button" onClick={() => {
                setIsAdding(false);
                setNewName('');
                setNewAge(8);
                setNewLearningStyle('');
                setNewReadingLevel('');
                setNewAttentionSpan('');
                setNewInterests('');
                setNewStrengths('');
              }} className="h-12 px-6 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-all">Cancel</button>
              <button type="submit" className="h-12 px-8 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-bold shadow-lg hover:shadow-glow transition-all">Create Child</button>
            </div>
          </form>
        </motion.div>
      )}

      <div className="space-y-6">
        {profiles.map((profile) => {
          const isExpanded = selectedChildId === profile.id;
          const showSessions = isExpanded && viewMode === 'sessions' && !selectedSessionId;
          const showEvaluations = isExpanded && viewMode === 'evaluations';
          const showChat = isExpanded && selectedSessionId && viewMode === 'sessions';
          
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
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleStartEdit(profile)}
                      className="p-2 bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 transition-all"
                      title="Edit child details"
                    >
                      <Edit2 size={16} />
                    </button>
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
                </div>

                {/* Edit Form */}
                {editingChildId === profile.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mb-6 p-6 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border-2 border-indigo-200"
                  >
                    <h4 className="text-lg font-black text-slate-800 mb-4 flex items-center gap-2">
                      <Edit2 size={18} className="text-indigo-600" />
                      Edit Child Details
                    </h4>
                    <form onSubmit={(e) => handleUpdateChild(e, profile.id)} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Name</label>
                          <input 
                            type="text" 
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Age Level</label>
                          <select 
                            value={editAge}
                            onChange={(e) => setEditAge(parseInt(e.target.value) as 6 | 8 | 10)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                          >
                            <option value={6}>Age 6 (Level I)</option>
                            <option value={8}>Age 8 (Level II)</option>
                            <option value={10}>Age 10 (Level III)</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Learning Style</label>
                          <select 
                            value={editLearningStyle}
                            onChange={(e) => setEditLearningStyle(e.target.value)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                          >
                            <option value="">Select learning style</option>
                            <option value="visual">Visual</option>
                            <option value="auditory">Auditory</option>
                            <option value="kinesthetic">Kinesthetic</option>
                            <option value="reading/writing">Reading/Writing</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Reading Level</label>
                          <select 
                            value={editReadingLevel}
                            onChange={(e) => setEditReadingLevel(e.target.value)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                          >
                            <option value="">Select reading level</option>
                            <option value="beginner">Beginner</option>
                            <option value="intermediate">Intermediate</option>
                            <option value="advanced">Advanced</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Attention Span</label>
                          <select 
                            value={editAttentionSpan}
                            onChange={(e) => setEditAttentionSpan(e.target.value)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                          >
                            <option value="">Select attention span</option>
                            <option value="short">Short (5-10 min)</option>
                            <option value="medium">Medium (10-20 min)</option>
                            <option value="long">Long (20+ min)</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Interests</label>
                          <input 
                            type="text" 
                            value={editInterests}
                            onChange={(e) => setEditInterests(e.target.value)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                            placeholder="e.g. dinosaurs, space, art (comma-separated)"
                          />
                        </div>
                        <div className="md:col-span-2">
                          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Academic Strengths</label>
                          <input 
                            type="text" 
                            value={editStrengths}
                            onChange={(e) => setEditStrengths(e.target.value)}
                            className="w-full h-12 px-4 rounded-xl border-2 border-slate-200 focus:border-indigo-500 outline-none font-semibold bg-white"
                            placeholder="e.g. math, problem-solving, creativity (comma-separated)"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-end gap-3 pt-2">
                        <button 
                          type="button" 
                          onClick={handleCancelEdit}
                          className="h-12 px-6 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-all"
                          disabled={isUpdating}
                        >
                          Cancel
                        </button>
                        <button 
                          type="submit" 
                          className="h-12 px-8 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-bold shadow-lg hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                          disabled={isUpdating}
                        >
                          {isUpdating ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                              Updating...
                            </>
                          ) : (
                            <>
                              <Check size={16} />
                              Save Changes
                            </>
                          )}
                        </button>
                      </div>
                    </form>
                  </motion.div>
                )}

                {/* Topics Management Section */}
                <div className="mb-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-indigo-600">
                      <Target size={14} /> 
                      <span className="text-xs font-bold uppercase tracking-wider">Learning Topics</span>
                    </div>
                    <button
                      onClick={() => {
                        setAddingSubject(prev => ({ ...prev, [profile.id]: !prev[profile.id] }));
                        setNewSubjectName(prev => ({ ...prev, [profile.id]: '' }));
                      }}
                      className="text-xs font-bold text-purple-600 hover:text-purple-700 transition-colors flex items-center gap-1"
                    >
                      <Plus size={14} /> Add Subject
                    </button>
                  </div>

                  {/* Add Subject Form */}
                  {addingSubject[profile.id] && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="p-4 bg-purple-50 rounded-xl border border-purple-200"
                    >
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={newSubjectName[profile.id] || ''}
                          onChange={(e) => setNewSubjectName(prev => ({ ...prev, [profile.id]: e.target.value }))}
                          placeholder="Enter subject name (e.g. Mathematics, Science...)"
                          className="flex-1 h-10 px-4 rounded-lg border-2 border-purple-200 focus:border-purple-500 outline-none font-semibold text-sm bg-white"
                          onKeyPress={(e) => e.key === 'Enter' && handleAddSubject(profile.id)}
                          autoFocus
                        />
                        <button
                          onClick={() => handleAddSubject(profile.id)}
                          disabled={addingSubjectLoading[profile.id] || !newSubjectName[profile.id]?.trim()}
                          className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg flex items-center justify-center shadow-lg hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                        >
                          {addingSubjectLoading[profile.id] ? (
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Check size={18} />
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setAddingSubject(prev => ({ ...prev, [profile.id]: false }));
                            setNewSubjectName(prev => ({ ...prev, [profile.id]: '' }));
                          }}
                          className="w-10 h-10 bg-slate-100 text-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-200 transition-all flex-shrink-0"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    </motion.div>
                  )}

                  {/* Subjects as Expandable Cards */}
                  {loadingTopics[profile.id] ? (
                    <div className="text-center py-4 text-slate-500 text-sm">Loading topics...</div>
                  ) : childTopics[profile.id] && childTopics[profile.id].length > 0 ? (
                    <div className="space-y-2">
                      {(() => {
                        const grouped: Record<string, any[]> = {};
                        childTopics[profile.id].forEach(t => {
                          const s = t.subject || "General";
                          if (!grouped[s]) grouped[s] = [];
                          grouped[s].push(t);
                        });

                        const isExpanded = (subject: string) => {
                          return expandedSubjects[profile.id]?.has(subject) || false;
                        };

                        return Object.entries(grouped).map(([subject, topics]) => {
                          // Filter out placeholder topics (where topic name equals subject name)
                          const realTopics = topics.filter((t: any) => t.topic !== t.subject);
                          // Sort: active topics first, then inactive
                          const sortedTopics = [...realTopics].sort((a: any, b: any) => {
                            if (a.is_active && !b.is_active) return -1;
                            if (!a.is_active && b.is_active) return 1;
                            return 0;
                          });
                          
                          return (
                          <div key={subject} className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden">
                            {/* Subject Header - Clickable */}
                            <div className="flex items-center justify-between p-4">
                              <button
                                onClick={() => {
                                  toggleSubject(profile.id, subject);
                                  // Load documents when expanding
                                  if (!expandedSubjects[profile.id]?.has(subject)) {
                                    loadSubjectDocuments(profile.id, subject);
                                  }
                                }}
                                className="flex-1 flex items-center justify-between hover:bg-slate-50 transition-all rounded-lg p-2 -m-2"
                              >
                                <h5 className="text-base font-black text-slate-800">{subject}</h5>
                                <ArrowRight 
                                  size={18} 
                                  className={`text-slate-400 transition-transform ${isExpanded(subject) ? 'rotate-90' : ''}`}
                                />
                              </button>
                              <div className="flex items-center gap-2 ml-2">
                                {/* Document count badge */}
                                {subjectDocuments[profile.id]?.[subject] && subjectDocuments[profile.id][subject].length > 0 && (
                                  <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg">
                                    {subjectDocuments[profile.id][subject].length}/2 docs
                                  </span>
                                )}
                                {/* Upload Document Button */}
                                <div className="relative">
                                  <input
                                    type="file"
                                    id={`file-input-${profile.id}-${subject}`}
                                    accept=".pdf,.txt,.md"
                                    className="hidden"
                                    onChange={async (e) => {
                                      const file = e.target.files?.[0];
                                      if (!file) return;

                                      // Validate file size (10MB limit)
                                      if (file.size > 10 * 1024 * 1024) {
                                        alert('File size exceeds 10MB limit. Please choose a smaller file.');
                                        e.target.value = '';
                                        return;
                                      }

                                      // Get topics for this subject
                                      const topics = sortedTopics.map((t: any) => t.topic);
                                      if (topics.length === 0) {
                                        alert('Please add a topic to this subject first before uploading documents.');
                                        e.target.value = '';
                                        return;
                                      }

                                      // If only one topic, use it automatically
                                      let selectedTopic = topics[0];
                                      if (topics.length > 1) {
                                        // Show selection dialog
                                        const selected = prompt(`Select topic for this document:\n${topics.map((t: string, i: number) => `${i + 1}. ${t}`).join('\n')}\n\nEnter topic name or number:`);
                                        if (!selected) {
                                          e.target.value = '';
                                          return;
                                        }
                                        
                                        // Check if it's a number
                                        const num = parseInt(selected);
                                        if (!isNaN(num) && num >= 1 && num <= topics.length) {
                                          selectedTopic = topics[num - 1];
                                        } else if (topics.includes(selected)) {
                                          selectedTopic = selected;
                                        } else {
                                          alert('Invalid topic selection');
                                          e.target.value = '';
                                          return;
                                        }
                                      }

                                      await handleUploadDocument(profile.id, subject, file, selectedTopic);
                                      // Reset file input
                                      e.target.value = '';
                                    }}
                                    disabled={uploadingDocument[`${profile.id}-${subject}`] || (subjectDocuments[profile.id]?.[subject]?.length || 0) >= 2}
                                  />
                                  <button
                                    type="button"
                                    onClick={() => {
                                      const fileInput = document.getElementById(`file-input-${profile.id}-${subject}`) as HTMLInputElement;
                                      if (fileInput && !fileInput.disabled) {
                                        fileInput.click();
                                      }
                                    }}
                                    disabled={uploadingDocument[`${profile.id}-${subject}`] || (subjectDocuments[profile.id]?.[subject]?.length || 0) >= 2}
                                    className={`p-2 rounded-lg transition-all ${
                                      (subjectDocuments[profile.id]?.[subject]?.length || 0) >= 2
                                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                                        : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 cursor-pointer'
                                    }`}
                                    title={
                                      (subjectDocuments[profile.id]?.[subject]?.length || 0) >= 2 
                                        ? 'Maximum 2 documents per subject' 
                                        : 'Upload document (max 10MB, PDF/TXT/MD)'
                                    }
                                  >
                                    {uploadingDocument[`${profile.id}-${subject}`] ? (
                                      <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                                    ) : (
                                      <Upload size={16} />
                                    )}
                                  </button>
                                </div>
                              </div>
                            </div>

                            {/* Expanded Content - Topics List */}
                            {isExpanded(subject) && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="border-t border-slate-200"
                              >
                                <div className="p-4 space-y-2">
                                  {sortedTopics.map((topic: any) => (
                                    <div
                                      key={topic.id}
                                      className={`flex items-center justify-between p-3 rounded-xl border-2 transition-all ${
                                        topic.is_active
                                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-indigo-400 shadow-lg'
                                          : 'bg-slate-50 border-slate-200 text-slate-700'
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
                                          className={`p-1.5 rounded-lg transition-all ${
                                            topic.is_active ? 'text-white/60 hover:text-white hover:bg-white/10' : 'text-red-500 hover:bg-red-50'
                                          }`}
                                          title="Remove topic (only if no sessions)"
                                        >
                                          <Trash2 size={16} />
                                        </button>
                                      </div>
                                    </div>
                                  ))}

                                  {/* Add Topic Form at the bottom */}
                                  {addingTopic[profile.id] === subject ? (
                                    <motion.div
                                      initial={{ opacity: 0 }}
                                      animate={{ opacity: 1 }}
                                      className="p-3 bg-indigo-50 rounded-xl border border-indigo-200"
                                    >
                                      <div className="flex gap-2">
                                        <input
                                          type="text"
                                          value={newTopic[profile.id] || ''}
                                          onChange={(e) => setNewTopic(prev => ({ ...prev, [profile.id]: e.target.value }))}
                                          placeholder="Enter topic name..."
                                          className="flex-1 h-10 px-4 rounded-lg border-2 border-indigo-200 focus:border-indigo-500 outline-none font-semibold text-sm bg-white"
                                          onKeyPress={(e) => e.key === 'Enter' && handleAddTopic(profile.id, subject)}
                                          autoFocus
                                        />
                                        <button
                                          onClick={() => handleAddTopic(profile.id, subject)}
                                          disabled={addingTopicLoading[profile.id] || !newTopic[profile.id]?.trim()}
                                          className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg flex items-center justify-center shadow-lg hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                                        >
                                          {addingTopicLoading[profile.id] ? (
                                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                          ) : (
                                            <Check size={18} />
                                          )}
                                        </button>
                                        <button
                                          onClick={() => {
                                            setAddingTopic(prev => ({ ...prev, [profile.id]: '' }));
                                            setNewTopic(prev => ({ ...prev, [profile.id]: '' }));
                                          }}
                                          className="w-10 h-10 bg-slate-100 text-slate-600 rounded-lg flex items-center justify-center hover:bg-slate-200 transition-all flex-shrink-0"
                                        >
                                          <X size={18} />
                                        </button>
                                      </div>
                                    </motion.div>
                                  ) : (
                                    <button
                                      onClick={() => {
                                        setAddingTopic(prev => ({ ...prev, [profile.id]: subject }));
                                        setNewTopic(prev => ({ ...prev, [profile.id]: '' }));
                                      }}
                                      className="w-full p-3 bg-indigo-50 hover:bg-indigo-100 rounded-xl border-2 border-dashed border-indigo-300 text-indigo-600 font-bold text-sm transition-all flex items-center justify-center gap-2"
                                    >
                                      <Plus size={16} />
                                      Add Topic
                                    </button>
                                  )}

                                  {/* Uploaded Documents Section */}
                                  {subjectDocuments[profile.id]?.[subject] && subjectDocuments[profile.id][subject].length > 0 && (
                                    <div className="mt-4 pt-4 border-t border-slate-200">
                                      <div className="flex items-center gap-2 mb-3">
                                        <FileText size={14} className="text-slate-500" />
                                        <h6 className="text-xs font-black uppercase tracking-wider text-slate-500">Reference Documents</h6>
                                      </div>
                                      <div className="space-y-2">
                                        {subjectDocuments[profile.id][subject].map((doc: any) => (
                                          <div
                                            key={doc.id}
                                            className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200"
                                          >
                                            <div className="flex items-center gap-3 flex-1">
                                              <FileText size={16} className="text-indigo-600" />
                                              <div>
                                                <p className="text-sm font-bold text-slate-800">{doc.file_name}</p>
                                                <p className="text-xs text-slate-500">
                                                  {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                                                </p>
                                              </div>
                                            </div>
                                            <button
                                              onClick={async () => {
                                                if (confirm('Are you sure you want to remove this document?')) {
                                                  try {
                                                    await learningApi.removeSubjectDocument(profile.id, subject, doc.id);
                                                    await loadSubjectDocuments(profile.id, subject);
                                                  } catch (error: any) {
                                                    alert(error.response?.data?.detail || 'Failed to remove document');
                                                  }
                                                }
                                              }}
                                              className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                              title="Remove document"
                                            >
                                              <Trash2 size={16} />
                                            </button>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            )}
                          </div>
                          );
                        });
                      })()}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-slate-500 text-sm bg-slate-50 rounded-xl border border-slate-200">
                      No subjects yet. Add a subject to get started!
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

              <AnimatePresence mode="wait">
                {/* Inline Sessions View */}
                {showSessions && (
                  <motion.div
                    key="sessions"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="glass rounded-3xl p-6 shadow-soft mt-4 overflow-hidden"
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
                {showChat && (
                  <motion.div
                    key="chat"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="glass rounded-3xl p-6 shadow-soft mt-4 overflow-hidden"
                  >
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-4">
                        <button
                          onClick={() => { setSelectedSessionId(null); setSessionChat(null); }}
                          className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 hover:bg-indigo-100 flex items-center justify-center transition-all"
                          title="Back to Sessions"
                        >
                          <ArrowRight size={20} className="rotate-180" />
                        </button>
                        <div>
                          <h4 className="text-xl font-black text-slate-800">Chat Conversation</h4>
                          {sessionChat && (
                            <p className="text-sm text-slate-600 mt-1">
                              {sessionChat.concept} • {new Date(sessionChat.created_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => { setSelectedChildId(null); setViewMode(null); setSelectedSessionId(null); setSessionChat(null); }}
                        className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-all"
                      >
                        <X size={16} className="text-slate-600" />
                      </button>
                    </div>
                    
                    <div className="max-h-96 overflow-y-auto space-y-4 bg-slate-50 rounded-2xl p-4">
                      {loadingChat ? (
                        <div className="text-center py-12">
                          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                          <p className="text-slate-600 font-semibold">Loading chat conversation...</p>
                        </div>
                      ) : !sessionChat || !sessionChat.interactions || sessionChat.interactions.length === 0 ? (
                        <div className="text-center py-12">
                          <p className="text-slate-600 font-semibold">No messages in this session.</p>
                        </div>
                      ) : (
                        sessionChat.interactions.map((interaction: any, idx: number) => (
                          <div
                            key={idx}
                            className={`flex ${interaction.role === 'user' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div
                              className={`max-w-[80%] p-4 rounded-2xl ${
                                interaction.role === 'user'
                                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-tr-none shadow-md'
                                  : 'bg-white text-slate-800 rounded-tl-none border-2 border-slate-200 shadow-sm'
                              }`}
                            >
                              <p className="text-sm leading-relaxed font-medium">{interaction.content}</p>
                              {interaction.transcribed_text && (
                                <div className="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-400">
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
                    key="evaluations"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="glass rounded-3xl p-6 shadow-soft mt-4 overflow-hidden"
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
              </AnimatePresence>
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
  const [isDragging, setIsDragging] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    dispatch(fetchCurriculum());
  }, [dispatch]);

  // Check which children already have curriculum
  const getChildrenWithCurriculum = () => {
    const childrenWithCurriculum = new Set<string>();
    curriculum.forEach((doc: any) => {
      doc.children?.forEach((c: any) => {
        childrenWithCurriculum.add(c.child_id);
      });
    });
    return childrenWithCurriculum;
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile && assignedChildIds.length > 0) {
      // Store child IDs before clearing (needed for success message)
      const uploadedChildIds = [...assignedChildIds];
      
      // Check which children had existing curriculum before upload
      const childrenWithCurriculum = getChildrenWithCurriculum();
      const willReplace = uploadedChildIds.filter(id => childrenWithCurriculum.has(id));
      
      try {
        await dispatch(uploadDocument({ file: selectedFile, childIds: uploadedChildIds }));
        
        // Clear form state
        setSelectedFile(null);
        setAssignedChildIds([]);
        
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        
        // Refresh curriculum list and wait for it to complete
        await dispatch(fetchCurriculum());
        
        // Show success message
        if (willReplace.length > 0) {
          alert(`Curriculum uploaded successfully! Replaced existing curriculum for ${willReplace.length} ${willReplace.length === 1 ? 'child' : 'children'}.`);
        } else {
          alert('Curriculum uploaded successfully!');
        }
      } catch (error: any) {
        console.error('Error uploading curriculum:', error);
        alert(error.response?.data?.detail || 'Failed to upload curriculum');
      }
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to remove this curriculum? It will no longer be available for the assigned children.')) {
      return;
    }
    
    setDeletingId(documentId);
    try {
      await learningApi.removeCurriculum(documentId);
      dispatch(fetchCurriculum());
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to remove curriculum');
    } finally {
      setDeletingId(null);
    }
  };

  const toggleChild = (id: string) => {
    setAssignedChildIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/pdf' || file.type.startsWith('text/') || file.name.endsWith('.md'))) {
      setSelectedFile(file);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-indigo-600 mb-2">
            <BookOpen size={14} /> Resource Center
          </div>
          <h2 className="text-4xl font-black text-slate-800 tracking-tight">Curriculum Materials</h2>
          <p className="text-sm text-slate-500 mt-2">Upload reference materials that will guide the AI in conversations with your children</p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-1 glass rounded-3xl p-6 shadow-soft"
        >
          <h3 className="text-lg font-black text-slate-800 mb-6 flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg">
              <Upload size={18} />
            </div>
            Upload Document
          </h3>
          
          <form onSubmit={handleUpload} className="space-y-5">
            {/* File Upload Area */}
            <label
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative block border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                isDragging 
                  ? 'border-indigo-500 bg-indigo-50 scale-[1.02]' 
                  : selectedFile 
                    ? 'border-indigo-300 bg-indigo-50/50' 
                    : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'
              }`}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                accept=".pdf,.txt,.md"
                className="absolute inset-0 opacity-0 cursor-pointer" 
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <div className="space-y-3">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto transition-all ${
                  selectedFile 
                    ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg' 
                    : 'bg-slate-100 text-slate-400'
                }`}>
                  <FileText size={28} />
                </div>
                {selectedFile ? (
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-slate-800">{selectedFile.name}</p>
                    <p className="text-xs text-slate-500">{formatFileSize(selectedFile.size)}</p>
                  </div>
                ) : (
                  <>
                    <p className="text-sm font-bold text-slate-700">
                      Drop file here or click to browse
                    </p>
                    <p className="text-xs text-slate-500">PDF, TXT, or MD • Max 10MB</p>
                  </>
                )}
              </div>
            </label>

            {/* Child Selection */}
            <div className="space-y-3">
              <label className="text-xs font-black uppercase tracking-wider text-slate-600 px-1 flex items-center justify-between">
                <span>Assign to Children</span>
                {assignedChildIds.length > 0 && (
                  <span className="text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg text-[10px]">
                    {assignedChildIds.length} selected
                  </span>
                )}
              </label>
              {profiles.length === 0 ? (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                  <p className="text-xs text-amber-700 font-semibold">No children registered yet. Add a child first!</p>
                </div>
              ) : (
                <>
                  <div className="flex flex-wrap gap-2">
                    {profiles.map(p => {
                      const childrenWithCurriculum = getChildrenWithCurriculum();
                      const hasExisting = childrenWithCurriculum.has(p.id);
                      const isSelected = assignedChildIds.includes(p.id);
                      
                      return (
                        <motion.button
                          key={p.id}
                          type="button"
                          onClick={() => toggleChild(p.id)}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all relative ${
                            isSelected 
                              ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg' 
                              : 'bg-white text-slate-700 border-2 border-slate-200 hover:border-indigo-300'
                          }`}
                          title={hasExisting && isSelected ? 'Will replace existing curriculum' : ''}
                        >
                          {p.name}
                          {hasExisting && isSelected && (
                            <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 rounded-full border-2 border-white flex items-center justify-center">
                              <span className="text-[8px] text-white font-black">!</span>
                            </span>
                          )}
                        </motion.button>
                      );
                    })}
                  </div>
                  {selectedFile && assignedChildIds.some(id => getChildrenWithCurriculum().has(id)) && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-2">
                      <AlertCircle size={14} className="text-blue-600 flex-shrink-0 mt-0.5" />
                      <p className="text-xs text-blue-700 font-semibold">
                        Some selected children already have curriculum. It will be replaced with the new file.
                      </p>
                    </div>
                  )}
                </>
              )}
              {selectedFile && assignedChildIds.length === 0 && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center gap-2">
                  <AlertCircle size={14} className="text-amber-600 flex-shrink-0" />
                  <p className="text-xs text-amber-700 font-semibold">Please select at least one child</p>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={!selectedFile || assignedChildIds.length === 0 || isLoading}
              className="w-full h-12 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-black shadow-lg hover:shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload size={16} />
                  Upload Curriculum
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* Document List */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 glass rounded-3xl p-6 shadow-soft"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white shadow-lg">
                <FileText size={18} />
              </div>
              Uploaded Curriculum
            </h3>
            {curriculum.length > 0 && (
              <span className="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-lg">
                {curriculum.length} {curriculum.length === 1 ? 'document' : 'documents'}
              </span>
            )}
          </div>
          
          <div className="space-y-3">
            {curriculum.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16"
              >
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center mx-auto mb-4">
                  <FileText size={32} className="text-slate-400" />
                </div>
                <p className="font-black text-slate-400 uppercase tracking-wider text-sm mb-1">No curriculum uploaded yet</p>
                <p className="text-xs text-slate-500">Upload your first document to get started</p>
              </motion.div>
            ) : (
              <AnimatePresence>
                {curriculum.map((doc, index) => {
                  const assignedChildren = doc.children?.map(c => profiles.find(p => p.id === c.child_id)?.name).filter(Boolean) || [];
                  return (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05 }}
                      className="group p-5 bg-white/80 backdrop-blur-sm rounded-2xl border-2 border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4 flex-1">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg flex-shrink-0">
                            <FileText size={20} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-black text-slate-800 mb-2 truncate">{doc.file_name}</p>
                            <div className="flex flex-wrap items-center gap-3 text-xs">
                              {doc.file_size && (
                                <span className="text-slate-500 font-semibold">
                                  {formatFileSize(doc.file_size)}
                                </span>
                              )}
                              {assignedChildren.length > 0 ? (
                                <div className="flex items-center gap-2">
                                  <Users size={12} className="text-indigo-500" />
                                  <span className="text-slate-600 font-semibold">
                                    {assignedChildren.length} {assignedChildren.length === 1 ? 'child' : 'children'}
                                  </span>
                                  <div className="flex -space-x-2">
                                    {assignedChildren.slice(0, 3).map((name, i) => (
                                      <div
                                        key={i}
                                        className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 border-2 border-white flex items-center justify-center text-white text-[10px] font-black"
                                        title={name}
                                      >
                                        {name?.[0]?.toUpperCase()}
                                      </div>
                                    ))}
                                    {assignedChildren.length > 3 && (
                                      <div className="w-6 h-6 rounded-full bg-slate-300 border-2 border-white flex items-center justify-center text-slate-600 text-[10px] font-black">
                                        +{assignedChildren.length - 3}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ) : (
                                <span className="text-amber-600 font-semibold">Not assigned</span>
                              )}
                            </div>
                            {assignedChildren.length > 0 && (
                              <p className="text-xs text-slate-500 mt-2">
                                {assignedChildren.join(', ')}
                              </p>
                            )}
                          </div>
                        </div>
                        <button 
                          onClick={() => handleDelete(doc.id)}
                          disabled={deletingId === doc.id}
                          className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Remove curriculum"
                        >
                          {deletingId === doc.id ? (
                            <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Trash2 size={18} />
                          )}
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            )}
          </div>
        </motion.div>
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
