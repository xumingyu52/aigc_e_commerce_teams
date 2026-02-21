/** @type {import('next').NextConfig} */
const nextConfig = {
    // output: 'export', // 注释掉静态导出
    reactStrictMode: true,
    // 恢复 rewrites 代理，让 Next.js 自动转发 API 请求到 Flask (5000)
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:5000/api/:path*' // Flask后端地址
            }
        ]
    }
}

module.exports = nextConfig