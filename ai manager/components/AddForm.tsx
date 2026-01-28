import React, { useState } from 'react';
import { Subscription } from '../types';
import { Currency, CURRENCY_SYMBOLS, CURRENCY_NAMES, EXCHANGE_RATES } from '../utils';

interface AddFormProps {
    onAdd: (sub: Omit<Subscription, 'id'>) => void;
}

const AddForm: React.FC<AddFormProps> = ({ onAdd }) => {
    const [name, setName] = useState('');
    const [price, setPrice] = useState('');
    const [date, setDate] = useState('');
    const [inputCurrency, setInputCurrency] = useState<Currency>('KRW');

    const handleSubmit = () => {
        if (!name || !price || !date) {
            alert('모든 필드를 입력해주세요.');
            return;
        }

        // Convert input price to KRW if needed
        let priceInKRW = Number(price);
        if (inputCurrency !== 'KRW') {
            // Convert to KRW: divide by exchange rate
            priceInKRW = Number(price) / EXCHANGE_RATES[inputCurrency];
        }

        onAdd({
            name,
            price: Math.round(priceInKRW), // Round to nearest won
            paymentDate: date
        });

        // Reset
        setName('');
        setPrice('');
        setDate('');
        setInputCurrency('KRW');
    };

    return (
        <div className="bg-white dark:bg-card-dark rounded-lg p-6 shadow-md border border-gray-200 dark:border-border-dark group relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/10 hover:border-indigo-500/30">
            <div className="absolute inset-0 -translate-x-[150%] group-hover:translate-x-[150%] transition-transform duration-1000 ease-in-out bg-gradient-to-r from-transparent via-white/5 to-transparent skew-x-12 pointer-events-none z-0"></div>
            <div className="relative z-10">
                <h3 className="text-lg font-bold text-gray-900 dark:text-text-light mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">add_circle</span>
                    새 구독 추가
                </h3>

                {/* First Row: Input Fields */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end mb-4">
                    <div className="md:col-span-4">
                        <label className="block text-sm font-medium text-gray-600 dark:text-text-muted-dark mb-1.5">서비스명</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <span className="material-symbols-outlined text-[20px]">subscriptions</span>
                            </div>
                            <input
                                type="text"
                                className="pl-10 block w-full rounded-lg border-gray-300 dark:border-border-dark bg-gray-50 dark:bg-[#374151] text-gray-900 dark:text-text-light placeholder-gray-400 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2.5 transition-all"
                                placeholder="예: 넷플릭스"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="md:col-span-4">
                        <label className="block text-sm font-medium text-gray-600 dark:text-text-muted-dark mb-1.5">
                            구독료 ({CURRENCY_SYMBOLS[inputCurrency]})
                        </label>
                        <div className="flex gap-2">
                            {/* Currency Selector */}
                            <select
                                value={inputCurrency}
                                onChange={(e) => setInputCurrency(e.target.value as Currency)}
                                className="w-28 rounded-lg border-gray-300 dark:border-border-dark bg-gray-50 dark:bg-[#374151] text-gray-900 dark:text-text-light text-sm font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary py-2.5 px-2"
                            >
                                {(Object.keys(CURRENCY_NAMES) as Currency[]).map((curr) => (
                                    <option key={curr} value={curr}>
                                        {curr}
                                    </option>
                                ))}
                            </select>

                            {/* Price Input */}
                            <div className="relative flex-1">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                    <span className="material-symbols-outlined text-[20px]">attach_money</span>
                                </div>
                                <input
                                    type="number"
                                    className="pl-10 block w-full rounded-lg border-gray-300 dark:border-border-dark bg-gray-50 dark:bg-[#374151] text-gray-900 dark:text-text-light placeholder-gray-400 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2.5 transition-all"
                                    placeholder={inputCurrency === 'KRW' ? '17000' : inputCurrency === 'USD' ? '12.75' : inputCurrency === 'JPY' ? '1870' : '91.80'}
                                    value={price}
                                    onChange={(e) => setPrice(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                    <div className="md:col-span-4">
                        <label className="block text-sm font-medium text-gray-600 dark:text-text-muted-dark mb-1.5">다음 결제일</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <span className="material-symbols-outlined text-[20px]">event</span>
                            </div>
                            <input
                                type="date"
                                className="pl-10 block w-full rounded-lg border-gray-300 dark:border-border-dark bg-gray-50 dark:bg-[#374151] text-gray-900 dark:text-text-light placeholder-gray-400 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2.5 transition-all"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                {/* Second Row: Centered Add Button */}
                <div className="flex justify-center">
                    <button
                        onClick={handleSubmit}
                        className="w-full md:w-auto flex justify-center items-center gap-2 bg-primary hover:bg-primary-hover text-white px-8 py-2.5 rounded-lg text-sm font-medium shadow-sm transition-all active:scale-95"
                    >
                        <span>추가</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AddForm;
