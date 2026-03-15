import { spawn } from "child_process";
import { describe, it, expect } from "vitest";
import path from "path";

const pkgDir = path.resolve(__dirname, "..", "..");

function runCommand(
  cmd: string,
  args: string[],
  opts: Record<string, unknown> = {},
) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn(cmd, args, { cwd: pkgDir, shell: true, ...opts });
    let stderr = "";
    child.stderr.on("data", (c) => (stderr += c.toString()));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(
          new Error(`${cmd} ${args.join(" ")} exited with ${code}\n${stderr}`),
        );
      }
    });
  });
}

describe("UI checklist scripts", () => {
  it("type-check should exit cleanly", async () => {
    await runCommand("npm", ["run", "type-check"]);
  });

  it("lint should exit cleanly", async () => {
    await runCommand("npm", ["run", "lint"]);
  });

  it("build should exit cleanly", async () => {
    await runCommand("npm", ["run", "build"]);
  }, 20000);

  it("dev should start without immediate errors", async () => {
    const child = spawn("npm", ["run", "dev"], { cwd: pkgDir, shell: true });
    let stderr = "";
    child.stderr.on("data", (c) => (stderr += c.toString()));

    await new Promise<void>((resolve) =>
      setTimeout(() => {
        child.kill();
        resolve();
      }, 3000),
    );

    // allow warnings (e.g. config duplicates) but no real error text
    expect(stderr).not.toMatch(/error/i);
  });
});
