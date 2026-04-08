"use client"

import { Card, Separator } from "@heroui/react"
import { usePathname } from "next/navigation"

import { DASHBOARD_NAV } from "@/components/layout/nav-config"

function getAnalyticsPageTitle(pathname: string) {
  const hit = DASHBOARD_NAV.children.find((c) => pathname === c.href || pathname.startsWith(`${c.href}/`))
  return hit?.label ?? ""
}

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? ""
  const pageTitle = getAnalyticsPageTitle(pathname)

  return (
    <div className="mx-auto w-full max-w-7xl p-4 sm:p-6">
      <Card variant="secondary" className="p-6">
        <div className="mx-auto w-full max-w-7xl space-y-5">
          {pageTitle ? (
            <div className="space-y-4">
              <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">{pageTitle}</h1>
              <Separator className="opacity-70" />
            </div>
          ) : null}

          {children}

          <Separator className="opacity-60" />
          <p className="text-center text-xs text-slate-500">
            智创电商营销系统 · 数据看板为占位展示，接入接口后可替换为真实图表与指标
          </p>
        </div>
      </Card>
    </div>
  )
}
