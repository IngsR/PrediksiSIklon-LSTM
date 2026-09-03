import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel/serverless';

// https://astro.build/config
export default defineConfig({
  site: 'https://prediksi.ikhwann.my.id',
  output: 'hybrid',
  adapter: vercel({
    includeFiles: [
      './public/models/model.onnx',
      './public/models/feature_scaler.json',
      './public/models/target_scaler.json'
    ],
    webAnalytics: { enabled: false },
  }),
  server: {
    port: 4321,
  },
});


