import React, { useState } from "react";
import { 
  ArrowLeft, 
  Info, 
  CheckCircle, 
  AlertCircle, 
  Calculator,
  History, Home, BookOpen, TrendingUp, User
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import StudentNavigation from "../components/StudentNavigation"
import { useTranslation } from "react-i18next";

export default function StudentForecast() {
  const { t, i18n } = useTranslation();
  const [classesToAttend, setClassesToAttend] = useState(12);

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };
  
  // Mock calculation constants
  const currentAttendance = 74;
  const totalClassesSoFar = 40;
  const futureClassesMax = 20;

  // Simple linear projection for the demo
  // Formula: (Present + New) / (Total + New) * 100
  const presentSoFar = (currentAttendance / 100) * totalClassesSoFar;
  const denom = totalClassesSoFar + classesToAttend;
  const projectedRatio = denom > 0
    ? (presentSoFar + classesToAttend) / denom
    : 0;

  const projectedScore = Math.round(projectedRatio * 100);


  const TARGET = 0.75;

  const classesNeeded = (() => {
    if (totalClassesSoFar <= 0) return 1;

    // minimum x such that (presentSoFar + x)/(totalClassesSoFar + x) >= 0.75
    const safePresent = Math.min(presentSoFar, totalClassesSoFar);
    const neededRaw = (TARGET * totalClassesSoFar - safePresent) / (1 - TARGET);

    return Math.max(0, Math.ceil(neededRaw));
  })();
  
  const meetsTargetWithSlider = classesToAttend >= classesNeeded;
  const isEligible = meetsTargetWithSlider;

  const canReachWithinSlider = classesNeeded <= futureClassesMax;


  // Chart Data
  const chartData = [
    { name: "Score", value: projectedScore, color: isEligible ? "var(--success)" : "var(--danger)" },
    { name: "Remaining", value: Math.max(0, 100 - projectedScore), color: "var(--border-color)" },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col md:flex-row font-sans text-[var(--text-main)]">
      
      {/* 1. Sidebar */}
      <StudentNavigation activePage="forecast" />

      {/* 2. Main Content */}
      <main className="flex-1 md:ml-64 p-6 md:p-8 pb-24 md:pb-8 animate-in fade-in duration-500 relative">
        
        {/* Language Switcher */}
        <div className="absolute top-6 right-6 z-10">
            <div className="flex gap-2 items-center bg-[var(--bg-card)] px-3 py-1.5 rounded-full border border-[var(--border-color)] shadow-sm">
              <button 
                onClick={() => changeLanguage('en')} 
                className={`text-xs ${i18n.language === 'en' ? 'font-bold text-[var(--primary)] border-b-2 border-[var(--primary)]' : 'text-[var(--text-body)] opacity-80 hover:text-[var(--text-body)]'}`}
              >
                English
              </button>
              <span className="text-[var(--text-body)] opacity-70 text-xs">|</span>
              <button 
                onClick={() => changeLanguage('hi')} 
                className={`text-xs ${i18n.language === 'hi' ? 'font-bold text-[var(--primary)] border-b-2 border-[var(--primary)]' : 'text-[var(--text-body)] opacity-80 hover:text-[var(--text-body)]'}`}
              >
                हिंदी
              </button>
            </div>
        </div>

        <div className="max-w-2xl mx-auto space-y-6">
          
          {/* Header */}
          <div className="flex items-center gap-3 mb-2">
            <button className="p-2 bg-[var(--bg-secondary)] hover:opacity-90 rounded-full transition-colors text-[var(--text-body)] opacity-90">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-[var(--text-main)]">{t('forecast.title')}</h2>
              <p className="text-[var(--text-body)] opacity-90 text-sm">{t('forecast.subtitle')}</p>
            </div>
          </div>

          {/* Info Card */}
          <div className="bg-[var(--primary-hover)] border border-[var(--primary-hover)] rounded-2xl p-5 flex gap-4">
            <div className="flex-shrink-0 mt-1">
              <Info className="text-[var(--primary)]" size={24} />
            </div>
            <div className="space-y-2">
              <h4 className="text-base font-bold text-[var(--primary)]">{t('forecast.info_card.title')}</h4>
              <p className="text-xs text-[var(--text-body)] leading-relaxed">
                {t('forecast.info_card.desc')}
              </p>
              <ul className="text-xs text-[var(--text-body)] space-y-1 list-disc pl-4">
                <li><span className="font-semibold">{t('forecast.info_card.below_75')}</span> {t('forecast.info_card.below_75_desc')}</li>
                <li><span className="font-semibold">{t('forecast.info_card.range_75_85')}</span> {t('forecast.info_card.range_75_85_desc')}</li>
                <li><span className="font-semibold">{t('forecast.info_card.above_85')}</span> {t('forecast.info_card.above_85_desc')}</li>
              </ul>
            </div>
          </div>

          {/* Simulation Card */}
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] shadow-sm p-6 space-y-8">
            
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-[var(--text-main)]">{t('forecast.simulation.title')}</h3>
                <p className="text-xs text-[var(--text-body)] opacity-90">{t('forecast.simulation.subtitle')}</p>
              </div>
              <span className="bg-[var(--primary-hover)] text-[var(--primary)] font-bold px-4 py-1.5 rounded-full text-xs tracking-wide">
                {t('forecast.simulation.badge')}
              </span>
            </div>

            {/* Slider Controls */}
            <div className="space-y-4">
              <div className="flex justify-between text-sm font-medium">
                <span className="text-[var(--text-body)]">{t('forecast.simulation.slider_label')}</span>
                <span className="text-[var(--primary)] bg-[var(--primary-hover)] px-4 py-1.5 rounded-full font-medium">{t('forecast.simulation.classes_count', {count: classesToAttend})}</span>
              </div>
              
              <div className="relative h-2 bg-[var(--bg-secondary)] rounded-full">
                <div 
                  className="absolute top-0 left-0 h-full bg-[var(--primary)] rounded-full transition-all duration-150" 
                  style={{width: `${(classesToAttend / futureClassesMax) * 100}%`}}
                ></div>
                <input 
                  type="range" 
                  min="0" 
                  max={futureClassesMax} 
                  value={classesToAttend} 
                  onChange={(e) => setClassesToAttend(Number(e.target.value))}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                {/* Thumb Visual (Optional custom thumb logic can be complex, default slider works for functionality) */}
              </div>
              <div className="flex justify-between text-xs text-[var(--text-body)] opacity-80">
                <span>0</span>
                <span>{futureClassesMax}</span>
              </div>
            </div>

            {/* Results Grid */}
            <div className="flex flex-col sm:flex-row items-center gap-8 pt-4">
              
              {/* Donut Chart */}
              <div className="relative w-32 h-32 flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      innerRadius={45}
                      outerRadius={65}
                      startAngle={90}
                      endAngle={-270}
                      dataKey="value"
                      stroke="none"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className={`text-2xl font-bold ${isEligible ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                    {projectedScore}%
                  </span>
                  <span className="text-[10px] text-[var(--text-body)] opacity-80 uppercase font-medium">
                    {t('forecast.simulation.expected_score').split(' ').map((line, i) => <React.Fragment key={i}>{line}<br/></React.Fragment>)}
                  </span>
                </div>
              </div>

              {/* Stats & Verdict */}
              <div className="flex-1 w-full space-y-6">
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="space-y-1">
                    <p className="text-[var(--text-body)] opacity-90 text-xs">{t('forecast.simulation.current_score')}</p>
                    <p className="font-semibold text-[var(--text-main)]">{currentAttendance}%</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[var(--text-body)] opacity-90 text-xs">{t('forecast.simulation.after_attending')}</p>
                    <p className={`font-bold ${isEligible ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                      {projectedScore}%
                    </p>
                  </div>
                  <div className="col-span-2 pt-2 border-t border-[var(--border-color)] flex justify-between items-center">
                    <p className="text-[var(--text-body)] opacity-90 text-xs">{t('forecast.simulation.needed_for_75')}</p>
                    <p className="font-bold text-[var(--text-main)]">{canReachWithinSlider
                       ? t('forecast.simulation.more_classes', { count: classesNeeded })
                       : t('forecast.simulation.more_classes_overflow', { 
                           count: classesNeeded,
                           minCount: classesNeeded,
                           sliderMax: futureClassesMax,
                         })}
                    </p>
                  </div>
                </div>

                {/* Eligibility Pill */}
                <div className={`rounded-xl p-4 flex items-start gap-3 ${
                  isEligible ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--danger)]/10 text-[var(--danger)]"
                }`}>
                  {isEligible ? <CheckCircle size={20} className="mt-0.5" /> : <AlertCircle size={20} className="mt-0.5" />}
                  <div>
                    <h4 className="font-bold text-sm">
                      {isEligible ? t('forecast.simulation.eligible') : t('forecast.simulation.not_eligible')}
                    </h4>
                    <p className="text-xs opacity-90 mt-1">
                      {isEligible 
                        ? t('forecast.simulation.eligible_desc') 
                        : t('forecast.simulation.not_eligible_desc')}
                    </p>
                  </div>
                </div>

              </div>
            </div>

            <p className="text-xs text-[var(--text-body)] opacity-80 text-center pt-4 border-t border-[var(--border-color)]">
              {t('forecast.simulation.disclaimer')}
            </p>

          </div>

        </div>
      </main>
    </div>
  );
}
