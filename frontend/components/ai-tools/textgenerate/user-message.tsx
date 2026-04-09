"use client"

import { Avatar, Card } from "@heroui/react"
import { getUserMessageBubbleClassName } from "./message-format"

interface UserMessageProps {
  content: string
}

export function UserMessage({ content }: UserMessageProps) {
  return (
    <div className="flex justify-end gap-3">
      <Card className={getUserMessageBubbleClassName()}>
        <Card.Content className="p-4">
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
            {content}
          </p>
        </Card.Content>
      </Card>
      <Avatar
        className="mt-[2px] flex-shrink-0"
        size="sm"
      >
        <Avatar.Image src="/images/user-avatar.jpg" alt="用户头像" />
        <Avatar.Fallback>用户</Avatar.Fallback>
      </Avatar>
    </div>
  )
}
