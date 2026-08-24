/**
 * Slack Collector — STUB
 *
 * Collects channel activity (channel names and message counts only, NO message content).
 *
 * TODO: Implement using Slack Web API
 * - Endpoint: conversations.history (to count messages per channel)
 * - Endpoint: conversations.list (to get channel names)
 * - Auth: Bot token with channels:history and channels:read scopes
 * - Docs: https://api.slack.com/methods/conversations.history
 *
 * Required config:
 *   collectors.slack.config.botToken — Slack Bot OAuth token (xoxb-...)
 *   collectors.slack.config.userToken — Slack User OAuth token (xoxp-...) for DM counts
 */

import type { Config, CollectorResult, SlackEntry } from "../types.js";
import { getCollectorConfig } from "../config.js";

export async function collectSlackActivity(
  date: string,
  config: Config
): Promise<CollectorResult<SlackEntry[]>> {
  const collectorConfig = getCollectorConfig(config, "slack");

  const hasCredentials = collectorConfig.botToken || collectorConfig.userToken;

  if (!hasCredentials) {
    return {
      success: false,
      data: null,
      errors: [
        "Not configured: Slack API credentials required. " +
        "Set config.collectors.slack.config with botToken (xoxb-...) or userToken (xoxp-...).",
      ],
      source: "slack",
    };
  }

  // TODO: Implement Slack API calls
  // 1. List channels user is in: conversations.list
  // 2. For each channel, get message count for target date:
  //    conversations.history with oldest/latest timestamps
  // 3. Count messages authored by the user (do NOT store content)
  // 4. Map to SlackEntry[] (channel name + count only)

  return {
    success: false,
    data: null,
    errors: ["Slack collector not yet implemented. API integration pending."],
    source: "slack",
  };
}

export const slackCollector = {
  name: "slack",
  collect: collectSlackActivity,
};
