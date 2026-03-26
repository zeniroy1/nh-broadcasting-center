import React from 'react';
import { formatCurrency, convertCurrency, Currency } from '../utils';

interface StatsCardsProps {
    monthlyTotal: number;
    annualTotal: number;
    currency: Currency;
}

const StatsCards: React.FC<StatsCardsProps> = ({ monthlyTotal, annualTotal, currency }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Monthly Card */}
            <div className="bg-white dark:bg-card-dark rounded-lg p-6 shadow-md border border-gray-200 dark:border-border-dark flex flex-col justify-between group relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/10 hover:border-indigo-500/30">
                <div className="absolute inset-0 -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-1000 ease-in-out bg-gradient-to-r from-transparent via-white/5 to-transparent skew-x-12 pointer-events-none z-0"></div>
                <div className="relative z-10 flex items-start justify-between">
                    <div>
                        <p className="text-gray-600 dark:text-text-muted-dark text-sm font-medium mb-1">이번 달 예상 지출</p>
                        <h2 className="text-3xl font-bold text-gray-900 dark:text-text-light">{formatCurrency(convertCurrency(monthlyTotal, currency), currency)}</h2>
                    </div>
                    <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-primary border border-indigo-200 dark:border-indigo-500/20">
                        <span className="material-symbols-outlined">calendar_month</span>
                    </div>
                </div>
                <div className="relative z-10 mt-4 flex items-center gap-2 text-sm text-green-400 font-medium">
                    <span className="material-symbols-outlined text-[18px]">trending_down</span>
                    <span>지난달 대비 --% (데이터 없음)</span>
                </div>
            </div>

            {/* Annual Card */}
            <div className="bg-white dark:bg-card-dark rounded-lg p-6 shadow-md border border-gray-200 dark:border-border-dark flex flex-col justify-between group relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/10 hover:border-indigo-500/30">
                <div className="absolute inset-0 -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-1000 ease-in-out bg-gradient-to-r from-transparent via-white/5 to-transparent skew-x-12 pointer-events-none z-0"></div>
                <div className="relative z-10 flex items-start justify-between">
                    <div>
                        <p className="text-gray-600 dark:text-text-muted-dark text-sm font-medium mb-1">연간 예상 지출</p>
                        <h2 className="text-3xl font-bold text-gray-900 dark:text-text-light">{formatCurrency(convertCurrency(annualTotal, currency), currency)}</h2>
                    </div>
                    <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-primary border border-indigo-200 dark:border-indigo-500/20">
                        <span className="material-symbols-outlined">savings</span>
                    </div>
                </div>
                <div className="relative z-10 mt-4 flex items-center gap-2 text-sm text-gray-500 dark:text-text-muted-dark">
                    <span className="material-symbols-outlined text-[18px]">info</span>
                    <span>월 예상 지출 × 12개월</span>
                </div>
            </div>
        </div>
    );
};

export default StatsCards;
