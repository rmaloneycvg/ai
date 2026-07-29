import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

export interface ReadJsonResult {
  success: boolean;
  data?: unknown;
  error?: string;
  path: string;
}

export function readJson(filePath: string): ReadJsonResult {
  const resolved = resolve(filePath);

  if (!existsSync(resolved)) {
    return { success: false, error: `File not found: ${resolved}`, path: resolved };
  }

  try {
    const content = readFileSync(resolved, "utf-8");
    const data = JSON.parse(content);
    return { success: true, data, path: resolved };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `Parse error: ${message}`, path: resolved };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const path = process.argv[2];
  if (!path) {
    console.error(JSON.stringify({ success: false, error: "Usage: read-json.ts <path>" }));
    process.exit(1);
  }
  const result = readJson(path);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}
