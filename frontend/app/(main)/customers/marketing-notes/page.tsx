"use client"

import { Card } from "@heroui/react"

export default function MarketingNotesPage() {
  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-6">
      <Card variant="secondary" className="p-6">
        <Card.Header>
          <Card.Title>营销笔记发布</Card.Title>
          <Card.Description>占位页：笔记编辑、审核与多渠道发布可在此接入</Card.Description>
        </Card.Header>
      </Card>
    </div>
  )
}
