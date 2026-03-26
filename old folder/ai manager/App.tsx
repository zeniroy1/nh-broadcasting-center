import React, { useState, useEffect } from 'react';
import StatsCards from './components/StatsCards';
import AddForm from './components/AddForm';
import SubscriptionList from './components/SubscriptionList';
import Advisor from './components/Advisor';
import { Subscription } from './types';
import { Currency, CURRENCY_NAMES, CURRENCY_SYMBOLS, updateExchangeRates } from './utils';
import { initializeExchangeRates, getExchangeRates } from './services/exchangeRateService';

const App: React.FC = () => {
    const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
    const [isDarkMode, setIsDarkMode] = useState<boolean>(true);
    const [currency, setCurrency] = useState<Currency>('KRW');

    // Load from LocalStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem('subscriptions');
        if (saved) {
            try {
                setSubscriptions(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to parse subscriptions", e);
            }
        }

        // Load theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            setIsDarkMode(false);
            document.documentElement.classList.remove('dark');
        } else {
            setIsDarkMode(true);
            document.documentElement.classList.add('dark');
        }

        // Load currency preference
        const savedCurrency = localStorage.getItem('currency') as Currency;
        if (savedCurrency && ['KRW', 'USD', 'CNY', 'JPY'].includes(savedCurrency)) {
            setCurrency(savedCurrency);
        }

        // Initialize exchange rates
        initializeExchangeRates().then(async () => {
            // Update rates after initialization
            try {
                const rates = await getExchangeRates();
                updateExchangeRates(rates);
            } catch (error) {
                console.error('Failed to update exchange rates:', error);
            }
        });
    }, []);

    // Save to LocalStorage whenever subscriptions change
    useEffect(() => {
        localStorage.setItem('subscriptions', JSON.stringify(subscriptions));
    }, [subscriptions]);

    const handleAddSubscription = (newSub: Omit<Subscription, 'id'>) => {
        const sub: Subscription = {
            ...newSub,
            id: Date.now().toString(), // Simple ID generation
        };
        setSubscriptions(prev => [...prev, sub]);
    };

    const handleDeleteSubscription = (id: string) => {
        if (window.confirm('정말 삭제하시겠습니까?')) {
            setSubscriptions(prev => prev.filter(s => s.id !== id));
        }
    };

    // Toggle theme
    const toggleTheme = () => {
        const newMode = !isDarkMode;
        setIsDarkMode(newMode);

        if (newMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    };

    // Handle currency change
    const handleCurrencyChange = (newCurrency: Currency) => {
        setCurrency(newCurrency);
        localStorage.setItem('currency', newCurrency);
    };

    // Calculations
    const monthlyTotal = subscriptions.reduce((sum, sub) => sum + sub.price, 0);
    const annualTotal = monthlyTotal * 12;

    return (
        <>
            <header className="bg-card-light dark:bg-card-dark border-b border-border-light dark:border-border-dark sticky top-0 z-50 shadow-sm transition-colors duration-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/20 text-primary">
                                <span className="material-symbols-outlined">smart_toy</span>
                            </div>
                            <h1 className="text-xl font-bold tracking-tight text-text-dark dark:text-text-light">AI 구독 비서</h1>
                        </div>
                        <div className="flex items-center gap-4">
                            {/* Currency Selector */}
                            <select
                                value={currency}
                                onChange={(e) => handleCurrencyChange(e.target.value as Currency)}
                                className="px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-[#374151] border border-gray-300 dark:border-border-dark text-sm font-medium text-gray-900 dark:text-text-light cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                {(Object.keys(CURRENCY_NAMES) as Currency[]).map((curr) => (
                                    <option key={curr} value={curr}>
                                        {CURRENCY_SYMBOLS[curr]} {curr}
                                    </option>
                                ))}
                            </select>

                            {/* Theme Toggle */}
                            <div
                                onClick={toggleTheme}
                                className="relative inline-flex h-8 w-16 items-center rounded-full bg-gray-200 dark:bg-[#374151] border border-gray-300 dark:border-border-dark cursor-pointer transition-colors hover:bg-gray-300 dark:hover:bg-gray-700 shadow-inner group"
                            >
                                <div className="absolute left-1.5 z-10 flex items-center justify-center">
                                    <span className={`material-symbols-outlined text-[18px] transition-colors ${!isDarkMode ? 'text-yellow-400' : 'text-gray-500 opacity-50'
                                        }`}>light_mode</span>
                                </div>
                                <div className="absolute right-1.5 z-10 flex items-center justify-center">
                                    <span className={`material-symbols-outlined text-[18px] transition-colors ${isDarkMode ? 'text-indigo-400' : 'text-gray-500 opacity-50'
                                        }`}>dark_mode</span>
                                </div>
                                <div className={`absolute h-6 w-6 rounded-full bg-primary shadow-md ring-1 ring-black/10 dark:ring-white/10 transition-transform flex items-center justify-center z-20 ${isDarkMode ? 'translate-x-[34px]' : 'translate-x-[2px]'
                                    }`}>
                                </div>
                            </div>
                            <div className="h-6 w-px bg-border-dark hidden sm:block"></div>
                            <button className="p-2 text-text-muted-dark hover:text-primary transition-colors">
                                <span className="material-symbols-outlined">notifications</span>
                            </button>
                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm border border-primary/30">
                                JD
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-grow p-4 sm:p-6 lg:p-8">
                <div className="max-w-7xl mx-auto space-y-6">

                    {/* Stats */}
                    <StatsCards monthlyTotal={monthlyTotal} annualTotal={annualTotal} currency={currency} />

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2 space-y-6">
                            {/* Add Form */}
                            <AddForm onAdd={handleAddSubscription} />

                            {/* List */}
                            <SubscriptionList
                                subscriptions={subscriptions}
                                onDelete={handleDeleteSubscription}
                                currency={currency}
                            />
                        </div>

                        <div className="lg:col-span-1">
                            {/* AI Advisor */}
                            <Advisor subscriptions={subscriptions} />
                        </div>
                    </div>
                </div>
            </main>

            <footer className="bg-card-light dark:bg-card-dark border-t border-border-light dark:border-border-dark mt-auto py-6 transition-colors duration-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-center text-gray-500 text-sm">
                    © 2024 AI Sub Manager. All rights reserved.
                </div>
            </footer>
        </>
    );
};

export default App;
