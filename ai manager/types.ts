export interface Subscription {
  id: string;
  name: string;
  price: number;
  paymentDate: string; // YYYY-MM-DD
}

export interface AdvisorMessage {
  role: 'user' | 'model';
  text: string;
}

export interface AIAnalysisResult {
  message: string;
}

declare global {
  interface Window {
    ENV: {
      GEMINI_API_KEY?: string;
    };
  }
}
