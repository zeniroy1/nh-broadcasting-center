import { Subscription } from './types';

// Currency types
export type Currency = 'KRW' | 'USD' | 'CNY' | 'JPY';

// Currency display names
export const CURRENCY_NAMES: Record<Currency, string> = {
    KRW: '원화 (₩)',
    USD: '달러 ($)',
    CNY: '위안화 (¥)',
    JPY: '엔화 (¥)'
};

// Currency symbols
export const CURRENCY_SYMBOLS: Record<Currency, string> = {
    KRW: '₩',
    USD: '$',
    CNY: '¥',
    JPY: '¥'
};

// Exchange rates (based on KRW)
// 1 KRW = X other currency
// These are default values, will be updated with real-time rates
export let EXCHANGE_RATES: Record<Currency, number> = {
    KRW: 1,
    USD: 0.00075,    // Default: 1 KRW ≈ 0.00075 USD (1,330 KRW per USD)
    CNY: 0.0054,     // Default: 1 KRW ≈ 0.0054 CNY (185 KRW per CNY)
    JPY: 0.11        // Default: 1 KRW ≈ 0.11 JPY (9 KRW per JPY)
};

// Function to update exchange rates dynamically
export const updateExchangeRates = (newRates: Record<Currency, number>) => {
    EXCHANGE_RATES = newRates;
};

// Convert amount from KRW to target currency
export const convertCurrency = (amountInKRW: number, targetCurrency: Currency): number => {
    return amountInKRW * EXCHANGE_RATES[targetCurrency];
};

// Format currency with specified currency type
export const formatCurrency = (amount: number, currency: Currency = 'KRW'): string => {
    const locale = currency === 'KRW' ? 'ko-KR' :
        currency === 'CNY' ? 'zh-CN' :
            currency === 'JPY' ? 'ja-JP' : 'en-US';

    // KRW and JPY don't use decimal places
    const useDecimals = currency !== 'KRW' && currency !== 'JPY';

    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: useDecimals ? 2 : 0,
        maximumFractionDigits: useDecimals ? 2 : 0
    }).format(amount);
};

// Format date to YYYY.MM.DD
export const formatDateKorean = (dateString: string): string => {
    return dateString.replace(/-/g, '.');
};

// Calculate D-Day
export const calculateDDay = (targetDateStr: string): string => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const target = new Date(targetDateStr);
    target.setHours(0, 0, 0, 0);

    const diffTime = target.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'D-Day';
    if (diffDays < 0) return `D+${Math.abs(diffDays)}`;
    return `D-${diffDays}`;
};

// Calculate Month and Day for "Every Month X Day" display
export const getPaymentDay = (dateString: string): string => {
    const date = new Date(dateString);
    return `매월 ${date.getDate()}일 결제`;
};

// Helper to get visual styles based on service name
export const getServiceStyles = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('netflix') || n.includes('넷플릭스')) {
        return {
            icon: 'movie',
            colorClass: 'text-red-500',
            bgClass: 'bg-red-500/10',
            borderClass: 'border-red-500/20',
            badgeBg: 'bg-orange-900/30',
            badgeText: 'text-orange-400',
            badgeRing: 'ring-orange-500/20'
        };
    }
    if (n.includes('spotify') || n.includes('스포티파이') || n.includes('music')) {
        return {
            icon: 'music_note',
            colorClass: 'text-green-500',
            bgClass: 'bg-green-500/10',
            borderClass: 'border-green-500/20',
            badgeBg: 'bg-green-900/30',
            badgeText: 'text-green-400',
            badgeRing: 'ring-green-500/20'
        };
    }
    if (n.includes('gpt') || n.includes('ai') || n.includes('claude')) {
        return {
            icon: 'auto_awesome',
            colorClass: 'text-white',
            bgClass: 'bg-white/10',
            borderClass: 'border-white/20',
            badgeBg: 'bg-blue-900/30',
            badgeText: 'text-blue-400',
            badgeRing: 'ring-blue-500/20'
        };
    }
    if (n.includes('adobe') || n.includes('figma') || n.includes('design')) {
        return {
            icon: 'design_services',
            colorClass: 'text-blue-500',
            bgClass: 'bg-blue-500/10',
            borderClass: 'border-blue-500/20',
            badgeBg: 'bg-slate-700',
            badgeText: 'text-slate-300',
            badgeRing: 'ring-slate-500/40'
        };
    }
    // Default
    return {
        icon: 'credit_card',
        colorClass: 'text-primary',
        bgClass: 'bg-primary/20',
        borderClass: 'border-primary/30',
        badgeBg: 'bg-indigo-900/30',
        badgeText: 'text-indigo-400',
        badgeRing: 'ring-indigo-500/20'
    };
};
