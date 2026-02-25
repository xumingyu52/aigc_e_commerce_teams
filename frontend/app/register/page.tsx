 "use client"
 
 import { useState } from "react"
 import { useRouter } from "next/navigation"
 import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
 import { Label } from "@/components/ui/label"
 import { Input } from "@/components/ui/input"
 import { Button } from "@/components/ui/button"
 import { Eye, EyeOff } from "lucide-react"
import ParticlesBackground from "@/components/ui/particles-background"
 
 export default function RegisterPage() {
   const router = useRouter()
   const [username, setUsername] = useState("")
   const [password, setPassword] = useState("")
   const [confirm, setConfirm] = useState("")
   const [isSubmitting, setIsSubmitting] = useState(false)
   const [showPwd, setShowPwd] = useState(false)
   const [showConfirm, setShowConfirm] = useState(false)
   const host = typeof window !== "undefined" ? window.location.hostname : "localhost"
   const logoUrl = `http://${host}:5000/static/images/${encodeURIComponent('智行合一logo.png')}`
 
   const onSubmit = (e: React.FormEvent) => {
     e.preventDefault()
     if (!username || !password) {
       alert("请输入账号与密码")
       return
     }
     if (password !== confirm) {
       alert("两次输入的密码不一致")
       return
     }
     setIsSubmitting(true)
     try {
       const raw = typeof window !== "undefined" ? localStorage.getItem("accounts") : null
       const list: Array<{ username: string; password: string }> = raw ? JSON.parse(raw) : []
       if (list.find((u) => u.username === username)) {
         alert("该账号已存在")
       } else {
         list.push({ username, password })
         localStorage.setItem("accounts", JSON.stringify(list))
         alert("注册成功，请使用该账号登录")
         router.push("/")
       }
     } catch {
       alert("注册失败，请重试")
     } finally {
       setIsSubmitting(false)
     }
   }
 
  return (
    <main className="relative min-h-screen w-full overflow-hidden">
      <ParticlesBackground />
      <div className="absolute inset-0 flex items-center justify-center">
      <Card className="relative w-full max-w-[420px] bg-white/30 backdrop-blur-xl border border-white/40 shadow-[0_20px_50px_rgba(37,99,235,0.12)] rounded-[20px] overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-br from-white/50 via-white/25 to-transparent"></div>
          <div
            className="absolute inset-0 opacity-60"
            style={{
              background:
                'radial-gradient(100% 60% at 50% 0%, rgba(147,197,253,0.3) 0%, transparent 70%)',
            }}
          />
        </div>
        <CardHeader className="relative z-10 px-8 pt-10 pb-4">
           <div className="flex flex-col items-center">
             <img src={logoUrl} alt="智行合一" className="h-[40px] md:h-[48px] w-auto object-contain" />
             <div className="mt-1 text-[13px] md:text-[14px] font-medium text-slate-600 tracking-wide">智行合一</div>
             <CardTitle className="mt-6 text-xl font-bold text-slate-800 text-center">注册账号</CardTitle>
           </div>
         </CardHeader>
         <form onSubmit={onSubmit}>
          <CardContent className="relative z-10 px-8 py-4">
             <div className="space-y-1.5">
               <Label htmlFor="username" className="text-slate-700 text-sm">账号</Label>
               <Input
                 id="username"
                 value={username}
                 onChange={(e) => setUsername(e.target.value)}
                 className="h-11 rounded-xl px-4 border border-white/60 bg-white/70 backdrop-blur-sm placeholder:text-slate-400 focus-visible:ring-2 focus-visible:ring-blue-500/20 focus-visible:border-blue-400/60 transition-all text-sm"
                 placeholder="请输入账号"
               />
             </div>
             <div className="space-y-1.5 mt-4">
               <Label htmlFor="password" className="text-slate-700 text-sm">密码</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPwd ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                   className="h-11 rounded-xl px-4 pr-10 border border-white/60 bg-white/70 backdrop-blur-sm placeholder:text-slate-400 focus-visible:ring-2 focus-visible:ring-blue-500/20 focus-visible:border-blue-400/60 transition-all text-sm"
                  placeholder="请输入密码"
                />
                <button
                  type="button"
                  aria-label={showPwd ? "隐藏密码" : "显示密码"}
                  onClick={() => setShowPwd((v) => !v)}
                  className="absolute inset-y-0 right-3 flex items-center text-slate-500 hover:text-slate-700"
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
             </div>
             <div className="space-y-1.5 mt-4">
               <Label htmlFor="confirm" className="text-slate-700 text-sm">确认密码</Label>
              <div className="relative">
                <Input
                  id="confirm"
                  type={showConfirm ? "text" : "password"}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                   className="h-11 rounded-xl px-4 pr-10 border border-white/60 bg-white/70 backdrop-blur-sm placeholder:text-slate-400 focus-visible:ring-2 focus-visible:ring-blue-500/20 focus-visible:border-blue-400/60 transition-all text-sm"
                  placeholder="请再次输入密码"
                />
                <button
                  type="button"
                  aria-label={showConfirm ? "隐藏密码" : "显示密码"}
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute inset-y-0 right-3 flex items-center text-slate-500 hover:text-slate-700"
                >
                  {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
             </div>
          </CardContent>
          <CardFooter className="relative z-10 px-8 pb-6 pt-2">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="h-11 w-full rounded-xl bg-gradient-to-r from-[#2563EB] to-[#1D4ED8] hover:from-[#1E4FD8] hover:to-[#1E40AF] text-white font-semibold tracking-wide shadow-lg transition-all text-sm"
            >
              {isSubmitting ? "提交中..." : "注册"}
            </Button>
          </CardFooter>
        </form>
        <div className="px-8 pb-6 text-center text-xs text-slate-500">
          已有账号?{" "}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              router.push("/")
            }}
            className="text-blue-600 hover:text-blue-700 hover:underline"
          >
            返回登录
          </a>
        </div>
      </Card>
      </div>
    </main>
   )
 }
