/** @type {import('next').NextConfig} */
const nextConfig = {
  // React Strict Mode's development remount initializes Leaflet twice on the same map node.
  reactStrictMode: false,
};

module.exports = nextConfig;
