import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAppDispatch, useAppSelector } from '../hooks/store';
import { logout as userLogout } from '../features/user/userSlice';
import { clearLearningState } from '../features/learning/learningSlice';
import { setView } from '../features/parent/parentSlice';
import { 
  Settings, 
  LogOut, 
  BarChart3, 
  Users,
  BookMarked,
  GraduationCap,
  FileText
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { role, currentChild } = useAppSelector((state) => state.user);
  const { currentView } = useAppSelector((state) => state.parent);

  // For children, no sidebar - they go straight to chat
  if (role === 'child') {
    return null;
  }

  // Parent navigation items
  const navItems = [
    { icon: BarChart3, label: t('nav.insights'), active: currentView === 'insights', view: 'insights' },
    { icon: Users, label: t('nav.children'), active: currentView === 'children', view: 'children' },
    { icon: BookMarked, label: t('nav.curriculum'), active: currentView === 'curriculum', view: 'curriculum' },
    { icon: FileText, label: t('nav.reports'), active: currentView === 'reports', view: 'reports' },
    { icon: Settings, label: t('nav.settings'), active: currentView === 'settings', view: 'settings' },
  ];

  const handleNavClick = (view: string) => {
    dispatch(setView(view as any));
  };

  const handleLogout = () => {
    dispatch(userLogout());
    dispatch(clearLearningState());
  };

  return (
    <div className="w-64 glass-dark flex flex-col h-full border-r border-white/10 shadow-lg">
      {/* Brand */}
      <div className="p-6 flex items-center gap-3 border-b border-white/10">
        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-black shadow-lg">
          <GraduationCap size={20} />
        </div>
        <span className="text-lg font-black text-white tracking-tight">
          <span className="text-indigo-300">LEARN</span>
          <span className="text-white">LOOP</span>
        </span>
      </div>

      {/* User Profile Card */}
      <div className="mx-4 mt-6 p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-lg font-bold shadow-lg">
            P
          </div>
          <div className="overflow-hidden flex-1">
            <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider mb-0.5">
              {t('common.parent')}
            </p>
            <p className="font-bold text-white text-sm leading-tight truncate">
              {t('common.parent_dashboard')}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item, idx) => (
          <button
            key={idx}
            onClick={() => handleNavClick(item.view)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-semibold text-sm transition-all group ${
              item.active 
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30' 
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <item.icon 
              size={20} 
              className={item.active ? 'text-white' : 'text-white/40 group-hover:text-indigo-300 transition-colors'} 
            />
            {item.label}
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/10 space-y-3">
        <div className="p-3 bg-white/5 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-wider">{t('common.status')}</span>
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          </div>
          <p className="text-[10px] text-white/50 font-medium leading-relaxed">
            {t('common.ai_system_active')}
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl font-semibold text-sm text-white/60 hover:text-white hover:bg-white/5 transition-all"
        >
          <LogOut size={18} />
          {t('nav.sign_out')}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
