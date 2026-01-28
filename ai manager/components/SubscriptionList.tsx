import React from 'react';
import { Subscription } from '../types';
import { formatCurrency, convertCurrency, getPaymentDay, calculateDDay, getServiceStyles, Currency } from '../utils';

interface SubscriptionListProps {
    subscriptions: Subscription[];
    onDelete: (id: string) => void;
    currency: Currency;
}

const SubscriptionList: React.FC<SubscriptionListProps> = ({ subscriptions, onDelete, currency }) => {
    return (
        <div className="bg-white dark:bg-card-dark rounded-lg shadow-md border border-gray-200 dark:border-border-dark overflow-hidden group relative transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/10 hover:border-indigo-500/30">
            <div className="absolute inset-0 -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-1000 ease-in-out bg-gradient-to-r from-transparent via-white/5 to-transparent skew-x-12 pointer-events-none z-0"></div>
            <div className="relative z-10 px-6 py-4 border-b border-gray-200 dark:border-border-dark flex justify-between items-center bg-gray-50 dark:bg-[#111827]/30">
                <h3 className="text-lg font-bold text-gray-900 dark:text-text-light">내 구독 목록</h3>
                <button className="text-sm text-primary font-medium hover:underline">
                    총 {subscriptions.length}개
                </button>
            </div>

            <div className="relative z-10 divide-y divide-gray-200 dark:divide-border-dark">
                {subscriptions.length === 0 ? (
                    <div className="p-8 text-center text-gray-500 dark:text-text-muted-dark">
                        <span className="material-symbols-outlined text-4xl mb-2 opacity-50">sentiment_dissatisfied</span>
                        <p>등록된 구독 서비스가 없습니다</p>
                    </div>
                ) : (
                    subscriptions.map((sub) => {
                        const style = getServiceStyles(sub.name);
                        return (
                            <div key={sub.id} className="p-4 flex flex-wrap items-center justify-between gap-4 hover:bg-gray-50 dark:hover:bg-[#374151]/30 transition-colors group/item">
                                <div className="flex items-center gap-4 min-w-[200px]">
                                    <div className={`w-10 h-10 rounded-lg ${style.bgClass} flex items-center justify-center shrink-0 border ${style.borderClass}`}>
                                        <span className={`material-symbols-outlined ${style.colorClass}`}>{style.icon}</span>
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-text-light">{sub.name}</p>
                                        <p className="text-xs text-gray-500 dark:text-text-muted-dark">구독 서비스</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-8 flex-1 justify-end">
                                    <div className="text-right">
                                        <p className="font-bold text-gray-900 dark:text-text-light">{formatCurrency(convertCurrency(sub.price, currency), currency)}</p>
                                        <p className="text-xs text-gray-500 dark:text-text-muted-dark">{getPaymentDay(sub.paymentDate)}</p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style.badgeBg} ${style.badgeText} ${style.badgeRing}`}>
                                            {calculateDDay(sub.paymentDate)}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => onDelete(sub.id)}
                                        className="text-text-muted-dark hover:text-red-400 transition-colors p-2 rounded-full hover:bg-red-500/10 opacity-0 group-hover/item:opacity-100 focus:opacity-100"
                                        title="삭제"
                                    >
                                        <span className="material-symbols-outlined">delete</span>
                                    </button>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default SubscriptionList;
