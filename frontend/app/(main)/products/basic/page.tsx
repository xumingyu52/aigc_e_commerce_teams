"use client"

import { Card } from "@heroui/react"

export default function ProductBasicLibraryPage() {
  return (
    <Card variant="secondary" className="p-6">
      <Card.Header>
        <Card.Title>商品基础信息库</Card.Title>
        <Card.Description>
          集中管理 SKU、规格、类目、价格与库存等主数据；可按《前端重构实施指南》阶段 7–8 接入表格与表单。
        </Card.Description>
      </Card.Header>
    </Card>
  )
}
