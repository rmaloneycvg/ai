/**
 * Zoom Meetings Collector — STUB
 *
 * TODO: Implement using Zoom REST API
 * - Endpoint: GET /users/me/meetings (for scheduled) and /past_meetings (for completed)
 * - Auth: Server-to-Server OAuth or OAuth2 user-level
 * - Docs: https://developers.zoom.us/docs/api/meetings/
 *
 * Required config:
 *   collectors.zoom.config.accountId — Zoom account ID
 *   collectors.zoom.config.clientId — OAuth app client ID
 *   collectors.zoom.config.clientSecret — OAuth app client secret
 */

import type { Config, CollectorResult, MeetingEntry } from "../types.js";
import { getCollectorConfig } from "../config.js";

export async function collectZoomMeetings(
  date: string,
  config: Config
): Promise<CollectorResult<MeetingEntry[]>> {
  const collectorConfig = getCollectorConfig(config, "zoom");

  const hasCredentials = collectorConfig.accountId && collectorConfig.clientId && collectorConfig.clientSecret;

  if (!hasCredentials) {
    return {
      success: false,
      data: null,
      errors: [
        "Not configured: Zoom API credentials required. " +
        "Set config.collectors.zoom.config with accountId, clientId, and clientSecret.",
      ],
      source: "zoom",
    };
  }

  // TODO: Implement Zoom API call
  // 1. Acquire Server-to-Server OAuth token: POST /oauth/token
  // 2. GET /users/me/meetings?type=scheduled for target date
  // 3. GET /report/users/me/meetings for past meetings on target date
  // 4. Combine and deduplicate
  // 5. Map to MeetingEntry[]

  return {
    success: false,
    data: null,
    errors: ["Zoom collector not yet implemented. API integration pending."],
    source: "zoom",
  };
}

export const zoomCollector = {
  name: "zoom",
  collect: collectZoomMeetings,
};
