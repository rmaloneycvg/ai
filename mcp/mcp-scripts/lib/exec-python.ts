/**
 * Execute a Python script within the mcp-scripts venv.
 */

import { execFile } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

export interface ExecResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

/**
 * Run a Python script relative to the mcp-scripts root using the local venv.
 */
export function execPython(scriptPath: string, args: string[] = []): Promise<ExecResult> {
  const python = resolve(ROOT, ".venv", "bin", "python");
  const script = resolve(ROOT, scriptPath);

  return new Promise((res) => {
    execFile(python, [script, ...args], { cwd: ROOT, timeout: 30_000 }, (error, stdout, stderr) => {
      const exitCode = error && "code" in error ? (error.code as number) ?? 1 : error ? 1 : 0;
      res({ stdout: stdout.trim(), stderr: stderr.trim(), exitCode });
    });
  });
}
