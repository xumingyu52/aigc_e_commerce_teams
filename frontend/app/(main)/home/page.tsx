"use client"

import { Card } from "@heroui/react"

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6">
      <Card variant="default">
        <Card.Header>
          <Card.Title>首页</Card.Title>
          <Card.Description className="text-[15px] leading-snug !text-slate-600 dark:!text-slate-300">
            页面建设中
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <p className="text-sm text-slate-600 dark:text-slate-400">此处为占位内容，后续可接入真实首页模块。</p>
        </Card.Content>
      </Card>
    </div>
  )
}
