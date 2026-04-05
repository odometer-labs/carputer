/*
    this file contains data types for the fastapi to use.
*/

export interface StartTrackResponse {
  createdTrackId: number;
}

export interface EndTrackResponse {
  success: string;
}
