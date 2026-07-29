import { execSync } from "node:child_process";

export interface StatusEntry {
  path: string;
  index: string;
  workTree: string;
}

export interface GitStatus {
  staged: StatusEntry[];
  unstaged: StatusEntry[];
  untracked: string[];
}

export function parseStatus(porcelain: string): GitStatus {
  const staged: StatusEntry[] = [];
  const unstaged: StatusEntry[] = [];
  const untracked: string[] = [];

  for (const line of porcelain.split("\n")) {
    if (!line) continue;

    const index = line[0];
    const workTree = line[1];
    const path = line.slice(3);

    if (index === "?") {
      untracked.push(path);
    } else {
      if (index !== " " && index !== "?") {
        staged.push({ path, index, workTree });
      }
      if (workTree !== " " && workTree !== "?") {
        unstaged.push({ path, index, workTree });
      }
    }
  }

  return { staged, unstaged, untracked };
}

export function getStatus(cwd?: string): GitStatus {
  const output = execSync("git status --porcelain=v1", {
    encoding: "utf-8",
    cwd,
  });
  return parseStatus(output);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const status = getStatus();
  console.log(JSON.stringify(status, null, 2));
}
