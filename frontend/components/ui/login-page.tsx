"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import Canvas from "./canvas"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      // 简单本地验证
      if (email === 'zxhy' && password === '12345678') {
        // 调用Flask后端API
        // 使用相对路径，通过Next.js代理转发
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password }),
        })

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
             // 登录成功后跳转到主页，动态获取主机名
             const targetHost = window.location.hostname;
             window.location.href = `http://${targetHost}:5000/home`
          } else {
             alert(data.message || '登录失败')
          }
        } else {
           // 处理非200响应
           alert(`登录请求失败: ${response.status}`)
        }
      } else {
        alert('账号或密码错误')
      }
    } catch (error) {
      console.error('登录失败:', error)
      alert('登录失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // ...处理逻辑
  }

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden">

      {/* 背景 - 蓝白渐变 */}
      <div className="absolute inset-0 z-0">
        {/* 基础渐变层 - 蓝白色 */}
        <Canvas style={{
          background: 'linear-gradient(to top, #0c3483 0%, #a2b6df 100%, #6b8cce 100%, #a2b6df 100%)'
        }} />

        {/* 第一组光斑 - 蓝青色 */}
        <div className="absolute -bottom-20 left-1/4 w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '1.2s' }}>
        </div>
        <div className="absolute bottom-40 right-1/4 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '1.8s' }}>
        </div>

        {/* 第二组光斑 - 深紫色 */}
        <div className="absolute top-1/3 left-1/3 w-72 h-72 bg-violet-700/25 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '0.8s' }}>
        </div>
        <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '2.2s' }}>
        </div>
      </div>

      {/* 粒子系统 - 动态星星效果 */}
      <div className="absolute inset-0 z-5 overflow-hidden pointer-events-none">
        {/* 粒子层1 - 小星星 */}
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full animate-ping"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDuration: `${Math.random() * 3 + 2}s`,
              animationDelay: `${Math.random() * 2}s`,
              opacity: Math.random() * 0.5 + 0.3,
              boxShadow: '0 0 6px 2px rgba(255, 255, 255, 0.3)'
            }}
          />
        ))}

        {/* 粒子层2 - 中等星星 */}
        {[...Array(30)].map((_, i) => (
          <div
            key={`medium-${i}`}
            className="absolute w-1.5 h-1.5 bg-blue-200 rounded-full animate-ping"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDuration: `${Math.random() * 4 + 3}s`,
              animationDelay: `${Math.random() * 3}s`,
              opacity: Math.random() * 0.4 + 0.2,
              boxShadow: '0 0 10px 3px rgba(167, 139, 250, 0.4)'
            }}
          />
        ))}

        {/* 粒子层3 - 流动的光点 */}
        {[...Array(20)].map((_, i) => (
          <div
            key={`flow-${i}`}
            className="absolute w-2 h-2 bg-purple-300/40 rounded-full animate-pulse"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDuration: `${Math.random() * 5 + 4}s`,
              animationDelay: `${Math.random() * 4}s`,
              opacity: Math.random() * 0.3 + 0.1,
              boxShadow: '0 0 15px 5px rgba(139, 92, 246, 0.3)',
              transform: 'scale(1)'
            }}
          />
        ))}
      </div>

      {/* 动态光斑 - 保留并增强 */}
      <div className="absolute bottom-20 left-1/4 w-72 h-72 bg-violet-600/30 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: '2s' }}>
      </div>
      <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-indigo-600/25 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: '1.5s' }}>
      </div>

      {/* 登录卡片 - 使用深蓝底色 */}
      <div className="relative z-10 w-full max-w-[980px] px-4">
        <Card className="bg-slate-800/90 backdrop-blur-sm border border-blue-600/30 shadow-2xl shadow-slate-900/90 min-h-[540px] grid md:grid-cols-5 overflow-hidden">
          {/* ================= 左侧：抽象科技概念展示 ================= */}
          <div className="hidden md:flex md:col-span-3 flex-col justify-center items-center bg-slate-900 relative overflow-hidden p-10">

            {/* 背景：深邃的极光渐变 */}
            <div className="absolute inset-0 z-0">
              <div className="absolute top-[-50%] left-[-50%] w-[200%] h-[200%] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/40 via-slate-900 to-slate-900 animate-[spin_60s_linear_infinite]"></div>
              <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-b from-transparent via-slate-900/80 to-slate-900"></div>
            </div>

            {/* 核心视觉：3D 悬浮引擎结构 */}
            <div className="relative z-10 w-64 h-64 mb-12 flex items-center justify-center">

              {/* 外圈轨道 1 */}
              <div className="absolute w-full h-full border border-blue-500/20 rounded-full animate-[spin_10s_linear_infinite]">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1.5 w-3 h-3 bg-blue-500 rounded-full shadow-[0_0_15px_#3b82f6]"></div>
              </div>

              {/* 外圈轨道 2 (反向旋转) */}
              <div className="absolute w-48 h-48 border border-indigo-500/30 rounded-full animate-[spin_15s_linear_infinite_reverse]">
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1.5 w-2 h-2 bg-indigo-400 rounded-full"></div>
              </div>

              {/* 中心核心：发光球体 */}
              <div className="relative w-32 h-32 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-full shadow-[0_0_50px_rgba(37,99,235,0.5)] flex items-center justify-center animate-pulse">
                {/* 中心 LOGO */}
                <svg className="w-16 h-16 text-white drop-shadow-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>

              {/* 悬浮的功能图标 */}
              {/* 1. 购物车 (电商) */}
              <div className="absolute -top-4 -right-4 bg-slate-800/80 backdrop-blur-md p-2.5 rounded-xl border border-white/10 shadow-lg animate-bounce" style={{ animationDelay: '0s' }}>
                <span className="text-xl">🛒</span>
              </div>
              {/* 2. 喇叭 (营销) */}
              <div className="absolute bottom-4 -left-8 bg-slate-800/80 backdrop-blur-md p-2.5 rounded-xl border border-white/10 shadow-lg animate-bounce" style={{ animationDelay: '1s' }}>
                <span className="text-xl">📢</span>
              </div>
              {/* 3. 搜索 (流量) */}
              <div className="absolute top-1/2 -right-12 bg-slate-800/80 backdrop-blur-md p-2.5 rounded-xl border border-white/10 shadow-lg animate-bounce" style={{ animationDelay: '2s' }}>
                <span className="text-xl">🔍</span>
              </div>

            </div>

            {/* 文案区域 */}
            <div className="relative z-10 text-center space-y-4 max-w-sm">
              <h2 className="text-3xl font-bold text-white tracking-tight">
                智能营销，从这里开始
              </h2>
              <div className="w-12 h-1 bg-blue-500 mx-auto rounded-full"></div>
              <p className="text-slate-400 text-sm leading-relaxed">
                AI驱动营销革新，智能生成文案、图片、视频，数字人直播带货，助力品牌实现电商数字化转型升级。
              </p>
            </div>

            {/* 底部装饰：网格线 */}
            <div className="absolute bottom-0 w-full h-24 bg-[linear-gradient(to_top,rgba(15,23,42,1),transparent)] z-10"></div>
            <div className="absolute bottom-0 w-full h-full opacity-20 pointer-events-none"
              style={{ backgroundImage: 'radial-gradient(circle, #3b82f6 1px, transparent 1px)', backgroundSize: '30px 30px' }}>
            </div>

          </div>
          <div className="md:col-span-2">
            <CardHeader className="space-y-1">
              {/* 系统名称使用亮蓝色 */}
              <h1 className="text-3xl font-bold text-right text-blue-400 mb-2 mr-12 mt-14">智创电商营销系统</h1>
              {/* 标题使用白色 */}
              <CardDescription className="text-right text-blue-100 mr-[70px]">请输入您的账号和密码登录系统</CardDescription>
            </CardHeader>

            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4 max-w-md ml-auto mt-8 mr-1 px-10">
                <div className="space-y-2">
                  <Label className="text-blue-100" htmlFor="username">账号</Label>
                  <Input
                    id="username"
                    className="bg-slate-700 border-blue-500/50 text-white focus:ring-blue-400 focus:border-blue-400"
                    type="text"
                    placeholder="请输入账号"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-blue-100" htmlFor="password">密码</Label>
                    <a href="#" className="text-sm text-blue-300 hover:text-blue-400 hover:underline">
                      忘记密码?
                    </a>
                  </div>
                  <Input
                    id="password"
                    className="bg-slate-700 border-blue-500/50 text-white focus:ring-blue-400 focus:border-blue-400"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="remember"
                    className="border-blue-400 data-[state=checked]:bg-blue-500"
                  />
                  <Label htmlFor="remember" className="text-sm font-normal text-blue-100">
                    记住我
                  </Label>
                </div>
              </CardContent>
              <CardFooter className="max-w-md mr-1 px-10">
                {/* 按钮使用蓝色渐变 */}
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white font-medium shadow-lg transition-all"
                  disabled={isLoading}
                >
                  {isLoading ? "登录中..." : "登录"}
                </Button>
              </CardFooter>
            </form>
            <div className="px-8 pb-6 text-right text-sm text-blue-200 mr-[104px]">
              还没有账号?{" "}
              <a href="#" className="text-blue-300 hover:text-blue-400 hover:underline">
                注册
              </a>
            </div>
          </div>

        </Card>
      </div>

    </div>
  )
}

