import type { TrackRange } from "../services/settings_preferences";


//this is a function for formatting the time for am/pm (I made this file so that I can 
// actually test something for TimeIndicator.svelte)
export function formatTime(date: Date) : string {
  const hours = (date.getHours() % 12) || 12;
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const sign = date.getHours() >= 12 ? 'PM' : 'AM';

  return `${hours}:${minutes} ${sign}`;
}


// this function gets the date by 1 day, week, month or year. 
// if there shouldn't be a date, if the user has selected all tracks
// to show then it should default to null
export function getAfterDate(range: TrackRange) : Date | null {
  if (range === "all") return null;

  const date = new Date();

  // set to midnight
  date.setHours(0, 0, 0, 0);

  switch (range) {
    case "day":
      date.setDate(date.getDate() - 1);
      break;
    case "week":
      date.setDate(date.getDate() - 7);
      break;
    case "month":
      date.setMonth(date.getMonth() - 1);
      break;
    case "year":
      date.setFullYear(date.getFullYear() - 1);
      break;
  }

  return date;
}
