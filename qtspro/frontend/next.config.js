/** @type {import('next').NextConfig} */
// The backend URL is determined by an environment variable.
// In development, this will default to localhost.
// In production (on Netlify/Vercel), you should set NEXT_PUBLIC_API_URL.
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
