import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';

interface ProgressGaugeProps {
  state?: 'understood' | 'partial' | 'confused' | 'procedural' | null;
  masteryPercent?: number | null; // From evaluation report (0-100)
}

const ProgressGauge: React.FC<ProgressGaugeProps> = ({ 
  state, 
  masteryPercent
}) => {
  const { t } = useTranslation();
  
  // If we have evaluation results (session ended), use those instead of state
  const isEvaluationMode = masteryPercent !== null;
  
  const getProgress = () => {
    if (isEvaluationMode && masteryPercent !== null) {
      return masteryPercent;
    }
    // Fallback to old state-based logic during conversation
    switch (state) {
      case 'confused': return 33;
      case 'partial': return 66;
      case 'understood': return 100;
      default: return 5;
    }
  };

  const getColor = () => {
    if (isEvaluationMode) {
      const percent = masteryPercent ?? 0;
      if (percent >= 80) return '#8b5cf6'; // violet-500 (excellent)
      if (percent >= 50) return '#f59e0b'; // amber-500 (good)
      return '#ef4444'; // red-500 (needs improvement)
    }
    // Fallback to old state-based colors
    switch (state) {
      case 'confused': return '#ef4444'; // red-500
      case 'partial': return '#f59e0b'; // amber-500
      case 'understood': return '#8b5cf6'; // violet-500
      default: return '#e2e8f0'; // slate-200
    }
  };

  const getStatusText = () => {
    if (isEvaluationMode && masteryPercent !== null && masteryPercent !== undefined) {
      if (masteryPercent >= 80) return t('child.concept_mastered');
      if (masteryPercent >= 50) return t('child.building_understanding');
      return t('child.initial_discovery');
    }
    // Fallback to old state-based text
    if (state === 'understood') return t('child.concept_mastered');
    if (state === 'partial') return t('child.building_understanding');
    if (state === 'confused') return t('child.initial_discovery');
    return t('child.starting_adventure');
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex justify-between items-end mb-1">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-1">
            {t('child.concept_mastery')}
          </p>
          <p className="text-xl font-black text-primary">
            {getStatusText()}
          </p>
        </div>
        <span className="text-2xl font-black text-primary">{getProgress()}%</span>
      </div>
      
      <div className="h-4 w-full bg-muted rounded-full overflow-hidden border border-border">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${getProgress()}%`, backgroundColor: getColor() }}
          transition={{ type: "spring", stiffness: 50, damping: 15 }}
          className="h-full rounded-full"
        />
      </div>

      {/* Only show state indicators during conversation (not after evaluation) */}
      {!isEvaluationMode && (
        <div className="grid grid-cols-3 gap-2 mt-6">
          <div className={`h-1 rounded-full ${state === 'confused' ? 'bg-red-500' : 'bg-border'}`} />
          <div className={`h-1 rounded-full ${state === 'partial' ? 'bg-amber-500' : 'bg-border'}`} />
          <div className={`h-1 rounded-full ${state === 'understood' ? 'bg-violet-500' : 'bg-border'}`} />
        </div>
      )}
    </div>
  );
};

export default ProgressGauge;


