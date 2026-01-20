import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';

interface ProgressGaugeProps {
  state: 'understood' | 'partial' | 'confused' | null;
}

const ProgressGauge: React.FC<ProgressGaugeProps> = ({ state }) => {
  const { t } = useTranslation();
  const getProgress = () => {
    switch (state) {
      case 'confused': return 33;
      case 'partial': return 66;
      case 'understood': return 100;
      default: return 5;
    }
  };

  const getColor = () => {
    switch (state) {
      case 'confused': return '#ef4444'; // red-500
      case 'partial': return '#f59e0b'; // amber-500
      case 'understood': return '#10b981'; // emerald-500
      default: return '#e2e8f0'; // slate-200
    }
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex justify-between items-end mb-1">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-1">
            {t('child.concept_mastery')}
          </p>
          <p className="text-xl font-black text-primary">
            {state === 'understood' ? t('child.concept_mastered') : 
             state === 'partial' ? t('child.building_understanding') : 
             state === 'confused' ? t('child.initial_discovery') : t('child.starting_adventure')}
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

      <div className="grid grid-cols-3 gap-2 mt-6">
        <div className={`h-1 rounded-full ${state === 'confused' ? 'bg-red-500' : 'bg-border'}`} />
        <div className={`h-1 rounded-full ${state === 'partial' ? 'bg-amber-500' : 'bg-border'}`} />
        <div className={`h-1 rounded-full ${state === 'understood' ? 'bg-emerald-500' : 'bg-border'}`} />
      </div>
    </div>
  );
};

export default ProgressGauge;


