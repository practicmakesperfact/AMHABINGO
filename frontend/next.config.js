/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Allow ngrok tunnel to serve the app without the browser warning page
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'ngrok-skip-browser-warning', value: '1' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
