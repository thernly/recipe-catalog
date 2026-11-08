import { readFile, writeFile, readdir, mkdir } from "node:fs/promises";
import { join, relative } from "node:path";
import { createHash } from "node:crypto";

const build = new URL("../build/", import.meta.url);
const buildPath = decodeURIComponent(build.pathname);
const assets = join(buildPath, "_app");
await mkdir(assets, { recursive: true });
async function processDirectory(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await processDirectory(path);
      continue;
    }
    if (!entry.name.endsWith(".html")) continue;
    let html = await readFile(path, "utf8");
    const matches = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)];
    for (const [tag, attributes, code] of matches) {
      if (/\bsrc\s*=/.test(attributes) || !code.trim()) continue;
      if (
        /\btype\s*=/.test(attributes) &&
        !/type=["'](?:module|text\/javascript)["']/.test(attributes)
      )
        continue;
      const hash = createHash("sha256").update(code).digest("hex").slice(0, 16);
      const assetPath = join(assets, `bootstrap-${hash}.js`);
      await writeFile(assetPath, code);
      const source = "/" + relative(buildPath, assetPath).split("\\").join("/");
      html = html.replace(
        tag,
        `<script${attributes} src="${source}"></script>`,
      );
    }
    await writeFile(path, html);
  }
}
await processDirectory(buildPath);
