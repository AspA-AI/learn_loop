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
  X
} from 'lucide-react';

const GrowthInsights: React.FC = () => {
  const dispatch = useAppDispatch();
  const { insights, isLoading } = useAppSelector((state) => state.parent);

  useEffect(() => {
    dispatch(fetchInsights());
  }, [dispatch]);

  if (isLoading) {
    return (
      <div className="space-y-10 animate-fade-in">
        <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-border text-center">
          <p className="text-muted-foreground font-bold">Loading insights...</p>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="space-y-10 animate-fade-in">
        <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-border text-center">
          <p className="text-muted-foreground font-bold">No insights available yet. Start a learning session to see progress!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-secondary mb-2">
            <TrendingUp size={12} /> Analytics Overview
          </div>
          <h2 className="text-4xl font-black text-primary tracking-tight">Growth Insights</h2>
        </div>
        <div className="flex gap-4">
          <button className="bg-white border border-border p-4 rounded-xl text-primary hover:bg-muted transition-all relative">
            <Bell size={20} />
            <div className="absolute top-3 right-3 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
          </button>
        </div>
      </header>

      {/* Summary Card */}
      <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-border">
        <h3 className="text-2xl font-black text-primary mb-6">Learning Summary</h3>
        <p className="text-lg font-medium text-primary leading-relaxed mb-6">{insights.summary}</p>
        
        <div className="grid grid-cols-3 gap-6 mt-8">
          <div className="p-6 bg-muted/30 rounded-2xl border border-border/50">
            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-2">Overall Mastery</p>
            <p className="text-3xl font-black text-primary">{insights.overall_mastery}%</p>
          </div>
          <div className="p-6 bg-muted/30 rounded-2xl border border-border/50">
            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-2">Total Sessions</p>
            <p className="text-3xl font-black text-primary">{insights.total_sessions}</p>
          </div>
          <div className="p-6 bg-muted/30 rounded-2xl border border-border/50">
            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-2">Learning Hours</p>
            <p className="text-3xl font-black text-primary">{insights.total_hours}</p>
          </div>
        </div>
      </div>

      {/* Achievements & Challenges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {insights.achievements.length > 0 && (
          <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-border">
            <h3 className="text-xl font-black text-primary mb-6 flex items-center gap-2">
              <Award size={20} className="text-secondary" /> Achievements
            </h3>
            <ul className="space-y-4">
              {insights.achievements.map((achievement, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-secondary mt-2 flex-shrink-0" />
                  <p className="font-medium text-primary leading-relaxed">{achievement}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {insights.challenges.length > 0 && (
          <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-border">
            <h3 className="text-xl font-black text-primary mb-6 flex items-center gap-2">
              <TrendingUp size={20} className="text-secondary" /> Areas to Focus
            </h3>
            <ul className="space-y-4">
              {insights.challenges.map((challenge, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-500 mt-2 flex-shrink-0" />
                  <p className="font-medium text-primary leading-relaxed">{challenge}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Recommended Next Steps */}
      {insights.recommended_next_steps.length > 0 && (
        <div className="bg-primary p-10 rounded-[2.5rem] shadow-lg text-white">
          <h3 className="text-xl font-black mb-6 flex items-center gap-2">
            <ArrowRight size={20} className="text-secondary" /> Recommended Next Steps
          </h3>
          <ul className="space-y-3">
            {insights.recommended_next_steps.map((step, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-secondary mt-2 flex-shrink-0" />
                <p className="font-medium text-white/90 leading-relaxed">{step}</p>
              </li>
            ))}
          </ul>
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
  const [editingTopic, setEditingTopic] = useState<string | null>(null);
  const [tempTopic, setTempTopic] = useState('');

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

  const handlePinTopic = (childId: string) => {
    if (tempTopic.trim()) {
      dispatch(pinTopic({ childId, topic: tempTopic }));
      setEditingTopic(null);
      setTempTopic('');
    }
  };

  return (
    <div className="space-y-10 animate-fade-in">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-secondary mb-2">
            <Users size={12} /> Profile Management
          </div>
          <h2 className="text-4xl font-black text-primary tracking-tight">Your Children</h2>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 bg-primary text-white px-6 py-4 rounded-xl font-bold shadow-xl hover:bg-primary/90 transition-all"
        >
          <UserPlus size={18} /> Add Child
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Add Child Form Overlay */}
        {isAdding && (
          <div className="md:col-span-2 bg-primary p-8 rounded-[2rem] text-white shadow-2xl relative overflow-hidden">
            <div className="relative z-10">
              <h3 className="text-2xl font-black mb-6">Register a New Child</h3>
              <form onSubmit={handleAddChild} className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-widest mb-2 opacity-60">Child's Name</label>
                  <input 
                    type="text" 
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full h-14 px-6 rounded-xl bg-white/10 border border-white/20 focus:border-secondary outline-none font-bold"
                    placeholder="e.g. Leo"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-widest mb-2 opacity-60">Age Level</label>
                  <select 
                    value={newAge}
                    onChange={(e) => setNewAge(Number(e.target.value) as any)}
                    className="w-full h-14 px-6 rounded-xl bg-white/10 border border-white/20 focus:border-secondary outline-none font-bold appearance-none"
                  >
                    <option value={6} className="text-primary">Age 6 (Early Explorer)</option>
                    <option value={8} className="text-primary">Age 8 (Junior Discoverer)</option>
                    <option value={10} className="text-primary">Age 10 (Advanced Learner)</option>
                  </select>
                </div>
                <div className="flex items-end gap-2">
                  <button type="submit" className="flex-1 h-14 bg-secondary text-white rounded-xl font-black shadow-lg hover:bg-secondary/90 transition-all">Create Profile</button>
                  <button type="button" onClick={() => setIsAdding(false)} className="h-14 px-6 bg-white/5 border border-white/10 rounded-xl font-bold hover:bg-white/10 transition-all">Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {profiles.map((profile) => (
          <motion.div
            key={profile.id}
            whileHover={{ y: -4 }}
            className="bg-white p-8 rounded-[2rem] shadow-sm border border-border flex flex-col"
          >
            <div className="flex items-start justify-between mb-8">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center text-4xl shadow-inner border border-border">
                  {profile.avatar}
                </div>
                <div>
                  <h3 className="text-2xl font-black text-primary">{profile.name}</h3>
                  <div className="flex items-center gap-2 text-[10px] font-black text-muted-foreground uppercase tracking-widest mt-1">
                    Age {profile.age_level} • <span className="text-secondary">Level {profile.age_level === 6 ? 'I' : profile.age_level === 8 ? 'II' : 'III'}</span>
                  </div>
                </div>
              </div>
              <div className="bg-accent/30 text-accent-foreground px-4 py-2 rounded-xl text-xs font-black flex items-center gap-2 border border-accent/20">
                <Key size={14} /> {profile.learningCode}
              </div>
            </div>

            {/* Target Topic Section */}
            <div className="mb-8 p-6 bg-muted/30 rounded-2xl border border-border/50">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Target size={14} className="text-secondary" /> 
                  <span className="text-[10px] font-black uppercase tracking-widest">Pinned Mission</span>
                </div>
                {editingTopic !== profile.id && (
                  <button 
                    onClick={() => { setEditingTopic(profile.id); setTempTopic(profile.target_topic || ''); }}
                    className="text-[10px] font-black text-secondary uppercase hover:underline"
                  >
                    Change
                  </button>
                )}
              </div>
              
              {editingTopic === profile.id ? (
                <div className="flex gap-2">
                  <input 
                    type="text"
                    value={tempTopic}
                    onChange={(e) => setTempTopic(e.target.value)}
                    placeholder="Enter topic..."
                    className="flex-1 h-10 px-4 rounded-lg border border-border outline-none font-bold text-sm focus:border-secondary"
                    autoFocus
                  />
                  <button 
                    onClick={() => handlePinTopic(profile.id)}
                    className="w-10 h-10 bg-secondary text-white rounded-lg flex items-center justify-center"
                  >
                    <Check size={18} />
                  </button>
                </div>
              ) : (
                <p className="text-lg font-black text-primary">
                  {profile.target_topic || 'No topic assigned yet'}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="p-5 bg-muted/50 rounded-2xl border border-border text-center">
                <Award size={14} className="mx-auto mb-2 text-muted-foreground" />
                <p className="text-lg font-black text-primary">{getChildStats(profile.id).mastery}%</p>
                <p className="text-[8px] font-black text-muted-foreground uppercase tracking-widest">Mastery</p>
              </div>
              <div className="p-5 bg-muted/50 rounded-2xl border border-border text-center">
                <Clock size={14} className="mx-auto mb-2 text-muted-foreground" />
                <p className="text-lg font-black text-primary">{getChildStats(profile.id).hours}</p>
                <p className="text-[8px] font-black text-muted-foreground uppercase tracking-widest">Hours</p>
              </div>
            </div>

            <button className="w-full h-14 bg-white border-2 border-primary/10 text-primary rounded-xl font-bold hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2 group">
              Detailed History <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </motion.div>
        ))}
        
        {!isAdding && (
          <button 
            onClick={() => setIsAdding(true)}
            className="group bg-muted/30 border-2 border-dashed border-border p-8 rounded-[2rem] flex flex-col items-center justify-center gap-4 hover:border-secondary hover:bg-secondary/5 transition-all min-h-[350px]"
          >
            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center text-muted-foreground group-hover:text-secondary group-hover:shadow-md transition-all">
              <Plus size={28} />
            </div>
            <p className="font-bold text-muted-foreground group-hover:text-secondary">Register New Child</p>
          </button>
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
              <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground px-1">Assign to Children</label>
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
            </div>

            <button
              type="submit"
              disabled={!selectedFile || assignedChildIds.length === 0 || isLoading}
              className="w-full h-14 bg-primary text-white rounded-xl font-black shadow-lg hover:bg-primary/90 transition-all disabled:opacity-50"
            >
              {isLoading ? 'Processing...' : 'Verify & Ground AI'}
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
