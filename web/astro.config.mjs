import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel/serverless';

// https://astro.build/config
export default defineConfig({
  output: 'hybrid',
  adapter: vercel({
    webAnalytics: { enabled: false },
    runtime: 'nodejs20.x',
  }),
  server: {
    port: 4321,
  },
});
