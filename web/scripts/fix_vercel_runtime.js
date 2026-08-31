import fs from 'node:fs';
import path from 'node:path';

// Recursively find all .vc-config.json files in .vercel/output
function findVcConfigs(dir, results = []) {
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      findVcConfigs(fullPath, results);
    } else if (entry.name === '.vc-config.json') {
      results.push(fullPath);
    }
  }
  return results;
}

const outputDir = path.resolve('.vercel/output');
const configs = findVcConfigs(outputDir);

if (configs.length === 0) {
  console.log('[Post-Build] No .vc-config.json found (static build or alternative output)');
} else {
  for (const configPath of configs) {
    try {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      if (config.runtime && config.runtime.startsWith('nodejs')) {
        const oldRuntime = config.runtime;
        config.runtime = 'nodejs20.x';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        console.log(`[Post-Build] Patched ${path.relative(outputDir, configPath)}: ${oldRuntime} -> nodejs20.x`);
      }
    } catch (err) {
      console.error(`[Post-Build] Error patching ${configPath}:`, err);
    }
  }
}
