import fs from 'node:fs';
import path from 'node:path';

const vcConfigPath = path.resolve('.vercel/output/functions/_render.func/.vc-config.json');

if (fs.existsSync(vcConfigPath)) {
  try {
    const config = JSON.parse(fs.readFileSync(vcConfigPath, 'utf-8'));
    config.runtime = 'nodejs20.x';
    fs.writeFileSync(vcConfigPath, JSON.stringify(config, null, 2));
    console.log('[Post-Build] Successfully patched Vercel Serverless Function runtime to: nodejs20.x');
  } catch (err) {
    console.error('[Post-Build] Error patching .vc-config.json:', err);
  }
} else {
  console.log('[Post-Build] .vc-config.json not found (static build or alternative output)');
}
