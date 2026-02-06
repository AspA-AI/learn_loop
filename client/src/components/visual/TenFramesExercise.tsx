import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface TenFrame {
  red: number;
  white: number;
  equation: string;
  complete: boolean;
}

interface TenFramesExerciseProps {
  frames: TenFrame[];
  instruction: string;
  onComplete: (answers: Record<number, number>) => void;
}

const TenFramesExercise: React.FC<TenFramesExerciseProps> = ({ frames, instruction, onComplete }) => {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [completed, setCompleted] = useState(false);

  const handleAnswerChange = (frameIndex: number, value: string) => {
    const numValue = value === '' ? 0 : parseInt(value, 10);
    if (!isNaN(numValue)) {
      const newAnswers = { ...answers, [frameIndex]: numValue };
      setAnswers(newAnswers);
      
      // Check if all incomplete frames are answered
      const incompleteFrames = frames
        .map((f, idx) => (!f.complete ? idx : -1))
        .filter(idx => idx !== -1);
      
      const allAnswered = incompleteFrames.every(idx => newAnswers[idx] !== undefined && newAnswers[idx] !== 0);
      
      if (allAnswered && !completed) {
        setCompleted(true);
        onComplete(newAnswers);
      }
    }
  };

  const renderTenFrame = (red: number, white: number, _frameIndex: number) => {
    const total = red + white;
    const circles = [];
    
    // First row (5 circles)
    for (let i = 0; i < 5; i++) {
      circles.push(
        <div
          key={`row1-${i}`}
          className={`w-8 h-8 rounded-full border-2 ${
            i < red ? 'bg-red-500 border-red-600' : 
            i < total ? 'bg-white border-slate-300' : 
            'bg-slate-100 border-slate-200'
          }`}
        />
      );
    }
    
    // Second row (5 circles)
    for (let i = 0; i < 5; i++) {
      circles.push(
        <div
          key={`row2-${i}`}
          className={`w-8 h-8 rounded-full border-2 ${
            (i + 5) < red ? 'bg-red-500 border-red-600' : 
            (i + 5) < total ? 'bg-white border-slate-300' : 
            'bg-slate-100 border-slate-200'
          }`}
        />
      );
    }
    
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="grid grid-cols-5 gap-1 p-2 bg-slate-50 rounded-lg border-2 border-slate-200">
          {circles}
        </div>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl p-6 shadow-lg border-2 border-indigo-100 mt-4"
    >
      <p className="text-sm font-bold text-slate-700 mb-4">{instruction}</p>
      
      <div className="grid grid-cols-2 gap-6">
        {frames.map((frame, frameIndex) => (
          <div key={frameIndex} className="flex flex-col items-center gap-3">
            {renderTenFrame(frame.red, frame.white, frameIndex)}
            
            <div className="flex items-center gap-2">
              <span className="text-base font-semibold text-slate-700">
                {frame.equation.split('=')[0].trim()}
              </span>
              <span className="text-base font-semibold text-slate-700">=</span>
              {frame.complete ? (
                <span className="text-lg font-bold text-indigo-600">
                  {frame.equation.split('=')[1].trim()}
                </span>
              ) : (
                <input
                  type="number"
                  value={answers[frameIndex] || ''}
                  onChange={(e) => handleAnswerChange(frameIndex, e.target.value)}
                  className="w-16 px-2 py-1 text-center text-lg font-bold border-2 border-indigo-300 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
                  placeholder="?"
                  disabled={completed}
                />
              )}
            </div>
          </div>
        ))}
      </div>
      
      {completed && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-4 p-3 bg-green-50 border-2 border-green-200 rounded-lg text-center"
        >
          <p className="text-sm font-bold text-green-700">Great job! ✅</p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default TenFramesExercise;

