/**
 * Microsoft Teams Collector — STUB
 *
 * TODO: Implement using Microsoft Graph API
 * - Endpoint: GET /me/calendar/events?$filter=isOnlineMeeting eq true
 * - Auth: OAuth2 with delegated permissions (Calendars.Read)
 * - Docs: https://learn.microsoft.com/en-us/graph/api/user-list-events
 *
 * Required config:
 *   collectors.teams.config.clientId — Azure AD app registration client ID
 *   collectors.teams.config.tenantId — Azure AD tenant ID
 *   collectors.teams.config.clientSecret — App secret or use device code flow
 */

import type { Config, CollectorResult, MeetingEntry } from "../types.js";
import { getCollectorConfig } from "../config.js";

export async function collectTeamsMeetings(
  date: string,
  config: Config
): Promise<CollectorResult<MeetingEntry[]>> {
  const collectorConfig = getCollectorConfig(config, "teams");

  const hasCredentials = collectorConfig.clientId && collectorConfig.tenantId;

  if (!hasCredentials) {
    return {
      success: false,
      data: null,
      errors: [
        "Not configured: Microsoft Teams API credentials required. " +
        "Set config.collectors.teams.config with clientId, tenantId, and clientSecret.",
      ],
      source: "teams",
    };
  }

  // TODO: Implement Graph API call
  // 1. Acquire token using MSAL (client credentials or device code)
  // 2. GET /me/calendar/events for target date
  // 3. Filter: isOnlineMeeting eq true AND onlineMeetingProvider eq 'teamsForBusiness'
  // 4. Map to MeetingEntry[]

  return {
    success: false,
    data: null,
    errors: ["Teams collector not yet implemented. API integration pending."],
    source: "teams",
  };
}

export const teamsCollector = {
  name: "teams",
  collect: collectTeamsMeetings,
};
