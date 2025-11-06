"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import ChatMessage from "./chat-message"
import SuggestedQueries from "./suggested-queries"

interface ChatAreaProps {
  chatHistory: { role: "user" | "assistant"; content: string }[]
  onChatHistoryUpdate: (history: { role: "user" | "assistant"; content: string }[]) => void
}

export default function ChatArea({ chatHistory, onChatHistoryUpdate }: ChatAreaProps) {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    // Add user message to history
    const userMessage = { role: "user", content: input }
    const updatedHistory = [...chatHistory, userMessage]
    onChatHistoryUpdate(updatedHistory)
    setInput("")
    setLoading(true)

    try {
      const response = await fetch("http://localhost:8000/queries", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ q: input }),
      })

      if (!response.ok) throw new Error("Failed to get response")
      const data = await response.json()

      // Add assistant response to history
      const assistantMessage = {
        role: "assistant",
        content: data.answer || data.content || "No response received",
      }
      onChatHistoryUpdate([...updatedHistory, assistantMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error processing your request.",
      }
      onChatHistoryUpdate([...updatedHistory, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {chatHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center space-y-6">
            <div className="text-center space-y-2">
              <h1 className="text-4xl font-bold text-balance">Intellidesk</h1>
              <p className="text-lg text-muted-foreground">an RAG Based project by Tanish Raghav</p>
            </div>

            {/* Suggested Queries */}
            <SuggestedQueries onQuerySelect={setInput} />
          </div>
        ) : (
          <>
            {chatHistory.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-4 bg-background">
        <form onSubmit={handleSendMessage} className="flex gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything..."
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading || !input.trim()} className="gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </form>
      </div>
    </div>
  )
}
