import { Subscription } from "../types";

export const getSubscriptionAdvice = async (
  apiKey: string,
  subscriptions: Subscription[]
): Promise<string> => {
  if (!apiKey) throw new Error("API Key is missing");

  const subsList = subscriptions
    .map((s) => `- ${s.name}: ${s.price} KRW (Next bill: ${s.paymentDate})`)
    .join("\n");

  const prompt = `
  You are a smart financial advisor specializing in subscription management.
  
  Here is the user's current subscription list:
  ${subsList}
  
  Please analyze this list and provide advice in Korean (Hangul).
  
  Your analysis must include:
  1. "중복되는 기능의 서비스": Identify any services that offer similar functionality (e.g., multiple music apps, multiple OTTs) and suggest consolidating.
  2. "사용자 패턴 기반 유지/해지 권고": Give specific advice on what to keep or cancel to save money.
  3. A brief summary of total potential savings if recommendations are followed.

  Keep the tone helpful, professional, and concise. Format with clear line breaks.
  `;

  try {
    // Using REST API instead of SDK
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  text: prompt,
                },
              ],
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Gemini API Error:", errorData);
      throw new Error(`API 오류: ${response.status}`);
    }

    const data = await response.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text;

    return text || "분석 결과를 가져올 수 없습니다.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw new Error("AI 분석 중 오류가 발생했습니다.");
  }
};
