import { writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";

export interface WriteJsonOptions {
  indent?: number;
  mkdir?: boolean;
}

export interface WriteJsonResult {
  success: boolean;
  path: string;
  error?: string;
}

export function writeJson(
  filePath: string,
  data: unknown,
  options: WriteJsonOptions = {}
): WriteJsonResult {
  const { indent = 2, mkdir = true } = options;
  const resolved = resolve(filePath);

  if (data === undefined) {
    return { success: false, path: resolved, error: "Data cannot be undefined" };
  }

  try {
    JSON.stringify(data); // validate serializable
  } catch {
    return { success: false, path: resolved, error: "Data is not JSON-serializable" };
  }

  try {
    if (mkdir) {
      mkdirSync(dirname(resolved), { recursive: true });
    }
    const content = JSON.stringify(data, null, indent) + "\n";
    writeFileSync(resolved, content, "utf-8");
    return { success: true, path: resolved };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, path: resolved, error: `Write error: ${message}` };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const path = process.argv[2];
  const dataArg = process.argv[3];
  const indent = parseInt(process.argv[4] || "2", 10);

  if (!path || !dataArg) {
    console.error(JSON.stringify({ success: false, error: "Usage: write-json.ts <path> <json-data> [indent]" }));
    process.exit(1);
  }

  let data: unknown;
  try {
    data = JSON.parse(dataArg);
  } catch {
    console.error(JSON.stringify({ success: false, error: "Invalid JSON data argument" }));
    process.exit(1);
  }

  const result = writeJson(path, data, { indent });
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}
