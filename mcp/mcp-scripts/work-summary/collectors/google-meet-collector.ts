/**
 * Google Meet Collector — STUB
 *
 * TODO: Implement using Google Calendar API
 * - Endpoint: GET /calendars/{calendarId}/events
 * - Filter events with conferenceData.conferenceSolution.name === "Google Meet"
 * - Auth: OAuth2 with scope calendar.readonly
 * - Docs: https://developers.google.com/calendar/api/v3/reference/events/list
 *
 * Required config:
 *   collectors.google-meet.config.credentialsPath — Path to OAuth2 credentials JSON
 *   collectors.google-meet.config.calendarId — Calendar ID (default: "primary")
 */

import type { Config, CollectorResult, MeetingEntry } from "../types.js";
import { getCollectorConfig } from "../config.js";

export async function collectGoogleMeetMeetings(
  date: string,
  config: Config
): Promise<CollectorResult<MeetingEntry[]>> {
  const collectorConfig = getCollectorConfig(config, "google-meet");

  const hasCredentials = collectorConfig.credentialsPath;

  if (!hasCredentials) {
    return {
      success: false,
      data: null,
      errors: [
        "Not configured: Google Meet API credentials required. " +
        "Set config.collectors.google-meet.config with credentialsPath (OAuth2 JSON) and calendarId.",
      ],
      source: "google-meet",
    };
  }

  // TODO: Implement Google Calendar API call
  // 1. Load credentials from credentialsPath
  // 2. Acquire/refresh OAuth2 token
  // 3. GET /calendars/{calendarId}/events?timeMin=...&timeMax=...
  // 4. Filter events with conferenceData present
  // 5. Map to MeetingEntry[]

  return {
    success: false,
    data: null,
    errors: ["Google Meet collector not yet implemented. API integration pending."],
    source: "google-meet",
  };
}

export const googleMeetCollector = {
  name: "google-meet",
  collect: collectGoogleMeetMeetings,
};
