/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_LANGFLOW_URL: process.env.NEXT_PUBLIC_LANGFLOW_URL,
    NEXT_PUBLIC_LANGFLOW_API_KEY: process.env.NEXT_PUBLIC_LANGFLOW_API_KEY,
    NEXT_PUBLIC_ENV: process.env.NEXT_PUBLIC_ENV,
    NEXT_PUBLIC_SUPPORT_PHONE: process.env.NEXT_PUBLIC_SUPPORT_PHONE,
    NEXT_PUBLIC_USE_WEBSOCKETS: process.env.NEXT_PUBLIC_USE_WEBSOCKETS,
  },
  webpack: (config, { isServer }) => {
    // Handle Node.js modules for client-side compilation
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        assert: false,
        url: false,
        util: false,
        path: false,
        stream: false,
        os: false,
        https: false,
        http: false,
        zlib: false,
      }
    }
    return config
  },
};

module.exports = nextConfig;