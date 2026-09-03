import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';

async function generateOpenGraph() {
  const width = 1200;
  const height = 630;

  // 1. Foto profil dari public/profile.png berukuran 360x360 px dengan aspect ratio terkunci & rounded corner
  const profileInputPath = path.resolve('public/profile.png');
  const profileSize = 360;
  const cornerRadius = 34;

  // Mask SVG untuk rounded squircle foto profil
  const roundedMask = Buffer.from(`
    <svg width="${profileSize}" height="${profileSize}">
      <rect x="0" y="0" width="${profileSize}" height="${profileSize}" rx="${cornerRadius}" ry="${cornerRadius}" fill="#ffffff" />
    </svg>
  `);

  const roundedProfile = await sharp(profileInputPath)
    .resize(profileSize, profileSize, { fit: 'cover' })
    .composite([{ input: roundedMask, blend: 'dest-in' }])
    .png()
    .toBuffer();

  // 2. Background SVG dan Typography tema maritim & AI
  const svgBackground = `
  <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ffffff" />
        <stop offset="60%" stop-color="#f8fafc" />
        <stop offset="100%" stop-color="#eff6ff" />
      </linearGradient>
      <linearGradient id="barGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#1e3a8a" />
        <stop offset="50%" stop-color="#2563eb" />
        <stop offset="100%" stop-color="#1e3a8a" />
      </linearGradient>
      <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#1e3a8a" flood-opacity="0.10" />
        <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#1e3a8a" flood-opacity="0.05" />
      </filter>
    </defs>

    <!-- Background Utama -->
    <rect width="${width}" height="${height}" fill="url(#bgGrad)" />

    <!-- Aksen Bar Kiri (Deep Navy Siklon) -->
    <rect x="0" y="0" width="12" height="${height}" fill="url(#barGrad)" />

    <!-- Border Luar Halus -->
    <rect x="1" y="1" width="${width - 2}" height="${height - 2}" fill="none" stroke="#e2e8f0" stroke-width="2" />

    <!-- Ornamen Dot Grid Kanan Bawah -->
    <g opacity="0.14" fill="#1e3a8a">
      <circle cx="1090" cy="510" r="4.5" />
      <circle cx="1125" cy="510" r="4.5" />
      <circle cx="1160" cy="510" r="4.5" />
      <circle cx="1090" cy="545" r="4.5" />
      <circle cx="1125" cy="545" r="4.5" />
      <circle cx="1160" cy="545" r="4.5" />
      <circle cx="1090" cy="580" r="4.5" />
      <circle cx="1125" cy="580" r="4.5" />
      <circle cx="1160" cy="580" r="4.5" />
    </g>

    <!-- Card Kiri: Foto Profil Ikhwan Ramadhan (Aspect Ratio Terkunci) -->
    <rect x="55" y="115" width="400" height="400" rx="42" fill="#ffffff" stroke="#dbeafe" stroke-width="2.5" filter="url(#cardShadow)" />
    <!-- Inner Frame Ring -->
    <rect x="73" y="133" width="364" height="364" rx="34" fill="#f8fafc" stroke="#eff6ff" stroke-width="2" />

    <!-- Sisi Kanan: Teks & Informasi Project Siklon Tropis -->
    <!-- Badge -->
    <g transform="translate(485, 115)">
      <rect width="335" height="38" rx="19" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5" />
      <text x="167" y="24" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13.5" font-weight="800" fill="#1e3a8a" letter-spacing="1.2" text-anchor="middle">
        PORTOFOLIO SKRIPSI // DEEP LEARNING LSTM
      </text>
    </g>

    <!-- Judul Utama (47px, Tidak Terpotong) -->
    <text x="485" y="222" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="47" font-weight="900" fill="#0f172a" letter-spacing="-1">
      Sistem Prediksi Siklon Tropis
    </text>

    <!-- Subtitle / Deskripsi Project (25px) -->
    <text x="485" y="280" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="25" font-weight="600" fill="#334155" letter-spacing="-0.2">
      Prediksi Lintasan &amp; Mitigasi Bencana Sumatera Barat
    </text>

    <!-- Author & Developer Info -->
    <g transform="translate(485, 330)">
      <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="20" font-weight="700" fill="#1e3a8a">
        Pengembang: Ikhwan Ramadhan (Frontend &amp; AI)
      </text>
    </g>

    <!-- Divider Line -->
    <line x1="485" y1="365" x2="1145" y2="365" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round" />

    <!-- Footer Info / Meta -->
    <g transform="translate(485, 425)">
      <!-- Wilayah Studi -->
      <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="21" font-weight="600" fill="#64748b">
        📍 Wilayah Samudera Hindia · Sumbar
      </text>
      <!-- Tech Stack -->
      <text x="390" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="21" font-weight="800" fill="#1e3a8a">
        • LSTM · ONNX · Astro · Leaflet
      </text>
    </g>
  </svg>
  `;

  // 3. Gabungkan background SVG dengan foto profil di koordinat x: 75, y: 135
  const outputBuffer = await sharp(Buffer.from(svgBackground))
    .composite([
      {
        input: roundedProfile,
        top: 135,
        left: 75,
      },
    ])
    .png({ quality: 100 })
    .toBuffer();

  // Simpan ke public/og.png dan public/opengraph-image.png
  const targetOgPng = path.resolve('public/og.png');
  const targetOpengraphPng = path.resolve('public/opengraph-image.png');
  fs.writeFileSync(targetOgPng, outputBuffer);
  fs.writeFileSync(targetOpengraphPng, outputBuffer);

  console.log(`✅ Gambar OpenGraph Siklon Tropis berhasil diperbarui sempurna!`);
}

generateOpenGraph().catch((err) => {
  console.error('Error generating OpenGraph:', err);
  process.exit(1);
});
