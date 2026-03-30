import { redirect } from "next/navigation"

/** 无独立「工作台」聚合页，默认进入文案智造器 */
export default function WorkspaceIndexPage() {
  redirect("/workspace/copywriting")
}
