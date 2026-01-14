import React from 'react';
import { useAppDispatch, useAppSelector } from '../hooks/store';
import { logout as userLogout } from '../features/user/userSlice';
import { clearLearningState } from '../features/learning/learningSlice';
import { setView } from '../features/parent/parentSlice';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Settings, 
  LogOut, 
  BarChart3, 
  Users,
  BookMarked,
  Sparkles
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const dispatch = useAppDispatch();
  const { role, currentChild } = useAppSelector((state) => state.user);
  const { currentView } = useAppSelector((state) => state.parent);

  const navItems = role === 'child' ? [
    { icon: LayoutDashboard, label: 'Current Adventure', active: true, view: 'adventure' },
    { icon: MessageSquare, label: 'Past Discovery', view: 'past' },
    { icon: Settings, label: 'Preferences', view: 'settings' },
  ] : [
    { icon: BarChart3, label: 'Growth Insights', active: currentView === 'insights', view: 'insights' },
    { icon: Users, label: 'Children', active: currentView === 'children', view: 'children' },
    { icon: BookMarked, label: 'Curriculum', active: currentView === 'curriculum', view: 'curriculum' },
    { icon: Settings, label: 'Portal Settings', active: currentView === 'settings', view: 'settings' },
  ];

  const handleNavClick = (view: string) => {
    if (role === 'parent') {
      dispatch(setView(view as any));
    }
  };

  const handleLogout = () => {
    dispatch(userLogout());
    dispatch(clearLearningState());
  };

  return (
    <div className="w-72 bg-primary flex flex-col h-full overflow-hidden text-white/80 font-sans shadow-2xl border-r border-white/5">
      {/* Brand */}
      <div className="p-8 flex items-center gap-3">
        <div className="w-10 h-10 bg-white/10 backdrop-blur-md rounded-xl flex items-center justify-center text-white font-black border border-white/10 shadow-inner">
          LL
        </div>
        <span className="text-xl font-black text-white tracking-tighter">
          LEARN<span className="text-secondary">LOOP</span>
        </span>
      </div>

      {/* User Profile Card */}
      <div className="mx-6 mb-8 p-6 bg-white/5 rounded-[1.5rem] border border-white/10 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-secondary/20 flex items-center justify-center text-2xl shadow-inner border border-secondary/20">
            {role === 'child' ? currentChild?.avatar : '👤'}
          </div>
          <div className="overflow-hidden">
            <p className="text-[10px] font-black text-secondary uppercase tracking-[0.15em] mb-0.5">
              {role === 'child' ? 'Student' : 'Administrator'}
            </p>
            <p className="font-bold text-white leading-tight truncate">
              {role === 'child' ? currentChild?.name : 'Parent Hub'}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-4 space-y-1">
        {navItems.map((item, idx) => (
          <button
            key={idx}
            onClick={() => handleNavClick(item.view)}
            className={`w-full flex items-center gap-4 px-6 py-4 rounded-xl font-bold text-sm transition-all group ${
              item.active 
                ? 'bg-secondary text-white shadow-lg shadow-secondary/10' 
                : 'hover:bg-white/5 hover:text-white'
            }`}
          >
            <item.icon size={20} className={item.active ? 'text-white' : 'text-white/40 group-hover:text-secondary transition-colors'} />
            {item.label}
          </button>
        ))}
      </div>

      {/* Footer / System Health */}
      <div className="mt-auto p-6 space-y-6">
        <div className="p-4 bg-black/20 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-white/30">
            <span>System Health</span>
            <div className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
          </div>
          <p className="text-[10px] text-white/40 font-medium leading-relaxed">
            AI grounded in verified academic curriculum.
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-6 py-4 rounded-xl font-bold text-sm text-white/40 hover:text-white hover:bg-white/5 transition-all"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
