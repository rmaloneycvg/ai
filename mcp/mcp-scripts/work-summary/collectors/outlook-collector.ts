/**
 * Outlook Email Collector — STUB
 *
 * Collects email subjects only (NO body content) for daily activity tracking.
 *
 * TODO: Implement using Microsoft Graph API
 * - Endpoint: GET /me/messages?$select=subject,from,receivedDateTime,isRead
 * - Filter by receivedDateTime for target date
 * - Auth: OAuth2 with delegated permissions (Mail.Read)
 * - Docs: https://learn.microsoft.com/en-us/graph/api/user-list-messages
 *
 * Required config:
 *   collectors.outlook.config.clientId — Azure AD app registration client ID
 *   collectors.outlook.config.tenantId — Azure AD tenant ID
 *   collectors.outlook.config.clientSecret — App secret
 */

import type { Config, CollectorResult, OutlookEntry } from "../types.js";
import { getCollectorConfig } from "../config.js";

export async function collectOutlookEmails(
  date: string,
  config: Config
): Promise<CollectorResult<OutlookEntry[]>> {
  const collectorConfig = getCollectorConfig(config, "outlook");

  const hasCredentials = collectorConfig.clientId && collectorConfig.tenantId;

  if (!hasCredentials) {
    return {
      success: false,
      data: null,
      errors: [
        "Not configured: Outlook API credentials required. " +
        "Set config.collectors.outlook.config with clientId, tenantId, and clientSecret.",
      ],
      source: "outlook",
    };
  }

  // TODO: Implement Graph API call
  // 1. Acquire token using MSAL
  // 2. GET /me/messages?$filter=receivedDateTime ge '...' and receivedDateTime lt '...'
  //    &$select=subject,from,receivedDateTime,isRead
  //    &$orderby=receivedDateTime
  // 3. Map to OutlookEntry[] (subject, from address, timestamp, isRead)
  // 4. NEVER include message body content

  return {
    success: false,
    data: null,
    errors: ["Outlook collector not yet implemented. API integration pending."],
    source: "outlook",
  };
}

export const outlookCollector = {
  name: "outlook",
  collect: collectOutlookEmails,
};
