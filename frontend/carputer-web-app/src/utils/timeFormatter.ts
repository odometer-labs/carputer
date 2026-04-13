//this is a function for formatting the time for am/pm (I made this file so that I can 
// actually test something for TimeIndicator.svelte)
export function formatTime(date: Date) : string {
  const hours = (date.getHours() % 12) || 12;
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const sign = date.getHours() >= 12 ? 'PM' : 'AM';

  return `${hours}:${minutes} ${sign}`;
}