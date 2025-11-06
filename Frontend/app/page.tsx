"use client"

import { useState } from "react"
import Sidebar from "@/components/sidebar"
import ChatArea from "@/components/chat-area"

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatHistory, setChatHistory] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleDataSourceUpdate = () => {
    setRefreshTrigger((prev) => prev + 1)
  }

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onDataSourceUpdate={handleDataSourceUpdate}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <ChatArea chatHistory={chatHistory} onChatHistoryUpdate={setChatHistory} />
      </div>
    </div>
  )
}
