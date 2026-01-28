import { Currency } from '../utils';

interface ExchangeRateResponse {
    result: string;
    base_code: string;
    conversion_rates: {
        [key: string]: number;
    };
}

// Cache for exchange rates
let cachedRates: { [key in Currency]?: number } | null = null;
let lastFetchTime = 0;
const CACHE_DURATION = 3600000; // 1 hour in milliseconds

/**
 * Fetch real-time exchange rates from API
 * Base currency: USD (then convert to KRW base)
 */
export const fetchExchangeRates = async (): Promise<{ [key in Currency]: number }> => {
    const now = Date.now();

    // Return cached rates if they're still fresh
    if (cachedRates && (now - lastFetchTime) < CACHE_DURATION) {
        return cachedRates as { [key in Currency]: number };
    }

    try {
        // Using USD as base currency for more reliable data
        const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');

        if (!response.ok) {
            throw new Error('Failed to fetch exchange rates');
        }

        const data: ExchangeRateResponse = await response.json();

        // Get USD → other currencies rates
        const usdToKRW = data.conversion_rates.KRW || 1470; // 1 USD = X KRW
        const usdToCNY = data.conversion_rates.CNY || 7.2;  // 1 USD = Y CNY
        const usdToJPY = data.conversion_rates.JPY || 150;  // 1 USD = Z JPY

        // Convert to KRW base (1 KRW = ? other currency)
        const rates: { [key in Currency]: number } = {
            KRW: 1,                    // Base
            USD: 1 / usdToKRW,         // 1 KRW = (1/X) USD
            CNY: usdToCNY / usdToKRW,  // 1 KRW = (Y/X) CNY
            JPY: usdToJPY / usdToKRW   // 1 KRW = (Z/X) JPY
        };

        // Cache the rates
        cachedRates = rates;
        lastFetchTime = now;

        // Also save to localStorage for offline fallback
        localStorage.setItem('exchangeRates', JSON.stringify(rates));
        localStorage.setItem('exchangeRatesTimestamp', now.toString());

        console.log('✅ Exchange rates updated:', {
            '1 USD': `₩${usdToKRW.toLocaleString()}`,
            '1 CNY': `₩${Math.round(usdToKRW / usdToCNY).toLocaleString()}`,
            '1 JPY': `₩${Math.round(usdToKRW / usdToJPY).toLocaleString()}`
        });

        return rates;
    } catch (error) {
        console.error('Error fetching exchange rates:', error);

        // Try to load from localStorage as fallback
        const savedRates = localStorage.getItem('exchangeRates');
        if (savedRates) {
            try {
                return JSON.parse(savedRates);
            } catch (e) {
                console.error('Failed to parse saved rates');
            }
        }

        // Return default rates if all else fails
        console.warn('Using default exchange rates');
        return {
            KRW: 1,
            USD: 1 / 1470,      // 1 USD = 1470 KRW
            CNY: 7.2 / 1470,    // 1 CNY ≈ 204 KRW
            JPY: 150 / 1470     // 1 JPY ≈ 9.8 KRW
        };
    }
};

/**
 * Get current exchange rates (from cache or fetch if needed)
 */
export const getExchangeRates = async (): Promise<{ [key in Currency]: number }> => {
    return await fetchExchangeRates();
};

/**
 * Initialize exchange rates when app starts
 */
export const initializeExchangeRates = async (): Promise<void> => {
    // Try to load from localStorage first for instant display
    const savedRates = localStorage.getItem('exchangeRates');
    const savedTimestamp = localStorage.getItem('exchangeRatesTimestamp');

    if (savedRates && savedTimestamp) {
        const timestamp = parseInt(savedTimestamp);
        const now = Date.now();

        if ((now - timestamp) < CACHE_DURATION) {
            try {
                cachedRates = JSON.parse(savedRates);
                lastFetchTime = timestamp;
            } catch (e) {
                console.error('Failed to parse saved rates');
            }
        }
    }

    // Fetch fresh rates in background
    fetchExchangeRates().catch(err => console.error('Background fetch failed:', err));
};
