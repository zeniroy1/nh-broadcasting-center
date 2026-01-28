import React, { useState } from 'react';
import { getSubscriptionAdvice } from '../services/geminiService';
import { Subscription } from '../types';

interface AdvisorProps {
    subscriptions: Subscription[];
}

const Advisor: React.FC<AdvisorProps> = ({ subscriptions }) => {
    const [apiKey, setApiKey] = useState('');
    const [loading, setLoading] = useState(false);
    const [advice, setAdvice] = useState<string>('');

    // Load API Key from Runtime Environment
    React.useEffect(() => {
        const envKey = window.ENV?.GEMINI_API_KEY;
        if (envKey && envKey !== '__GEMINI_API_KEY__') {
            setApiKey(envKey);
        }
    }, []);

    const handleAnalyze = async () => {
        if (!apiKey.trim()) {
            alert('API Key를 입력해주세요');
            return;
        }

        if (subscriptions.length === 0) {
            setAdvice("구독 목록이 비어있어 분석할 수 없습니다. 구독을 추가해주세요.");
            return;
        }

        setLoading(true);
        setAdvice("분석 중입니다...");

        try {
            const result = await getSubscriptionAdvice(apiKey, subscriptions);
            setAdvice(result);
        } catch (error: any) {
            setAdvice(`오류가 발생했습니다: ${error.message || "알 수 없는 오류"}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white dark:bg-card-dark rounded-lg shadow-md border border-gray-200 dark:border-border-dark h-full flex flex-col sticky top-24 group relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/10 hover:border-indigo-500/30">
            <div className="absolute inset-0 -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-1000 ease-in-out bg-gradient-to-r from-transparent via-white/5 to-transparent skew-x-12 pointer-events-none z-0"></div>

            {/* Header */}
            <div className="relative z-10 p-6 border-b border-gray-200 dark:border-border-dark bg-gradient-to-r from-indigo-100 dark:from-indigo-900/30 to-white dark:to-card-dark">
                <div className="flex items-center gap-3 mb-2">
                    <span className="material-symbols-outlined text-primary text-3xl">psychology</span>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-text-light">AI 소비 분석</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-text-muted-dark leading-relaxed">
                    구독 패턴을 분석하여 비용 절감 팁을 제안합니다. Google API Key를 입력하세요.
                </p>
            </div>

            {/* Content */}
            <div className="relative z-10 p-6 flex-1 flex flex-col gap-5">
                <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-text-muted-dark mb-1.5">Google API Key</label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                            <span className="material-symbols-outlined text-[18px]">key</span>
                        </div>
                        <input
                            type="password"
                            className="pl-9 block w-full rounded-lg border-gray-300 dark:border-border-dark bg-gray-50 dark:bg-[#374151] text-gray-900 dark:text-text-light placeholder-gray-400 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2.5"
                            placeholder="sk-..."
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                        />
                    </div>
                </div>

                <button
                    onClick={handleAnalyze}
                    disabled={loading}
                    className="w-full bg-primary hover:bg-primary-hover text-white py-3 rounded-lg font-medium shadow-md shadow-primary/20 transition-all flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <span className="animate-spin material-symbols-outlined text-[20px]">refresh</span>
                    ) : (
                        <span className="material-symbols-outlined text-[20px]">auto_fix_high</span>
                    )}
                    {loading ? '분석 중...' : '최적화 조언받기'}
                </button>

                <div className="flex-1 bg-gray-50 dark:bg-[#111827]/50 rounded-lg p-4 border border-gray-200 dark:border-border-dark overflow-y-auto min-h-[200px] max-h-[400px]">
                    <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center shrink-0 border border-indigo-200 dark:border-indigo-500/30">
                            <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                        </div>
                        <div className="bg-white dark:bg-card-dark p-3 rounded-lg rounded-tl-none border border-gray-200 dark:border-border-dark shadow-sm">
                            <p className="text-sm text-gray-700 dark:text-text-muted-dark leading-relaxed whitespace-pre-wrap">
                                {advice || `안녕하세요! API 키를 입력하시면 현재 구독 중인 서비스들의 가격 효율성을 분석해드립니다. \n\n예를 들어, "넷플릭스와 디즈니+를 번갈아 구독하여 연간 10만원을 절약하세요"와 같은 조언을 드릴 수 있습니다.`}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="relative z-10 p-4 border-t border-gray-200 dark:border-border-dark bg-gray-50 dark:bg-[#111827]/30 rounded-b-lg">
                <p className="text-xs text-center text-gray-500">
                    AI 분석은 개인정보 보호 정책에 따라 안전하게 처리됩니다.
                </p>
            </div>
        </div >
    );
};

export default Advisor;
