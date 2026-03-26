const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;
const CALENDAR_ID = import.meta.env.VITE_GOOGLE_CALENDAR_ID;

export const fetchEvents = async (startDate, endDate) => {
    if (!API_KEY || !CALENDAR_ID) {
        console.warn("Google Calendar API Key or Calendar ID is missing.");
        return [];
    }

    const BASE_URL = `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(CALENDAR_ID)}/events`;

    // Format dates to ISO string for API
    const timeMin = startDate.toISOString();
    const timeMax = endDate.toISOString();

    const params = new URLSearchParams({
        key: API_KEY,
        timeMin: timeMin,
        timeMax: timeMax,
        singleEvents: 'true',
        orderBy: 'startTime'
    });

    try {
        const response = await fetch(`${BASE_URL}?${params.toString()}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error?.message || 'Failed to fetch events');
        }

        const data = await response.json();

        return data.items.map(item => {
            const start = item.start.dateTime || item.start.date;
            const end = item.end.dateTime || item.end.date;
            const isAllDay = !item.start.dateTime;

            return {
                id: item.id,
                title: item.summary || 'No Title',
                start: new Date(start),
                end: new Date(end),
                allDay: isAllDay,
                location: item.location || '',
                description: item.description || '',
                type: 'google'
            };
        });
    } catch (error) {
        console.error("Error fetching Google Calendar events:", error);
        throw error; // Re-throw to let the component handle it
    }
};
