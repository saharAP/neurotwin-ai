/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // NEXT_DIST_DIR lets a production build run next to a live dev server without sharing .next.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
};
export default nextConfig;
