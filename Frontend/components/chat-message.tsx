import { MessageCircle, Bot } from "lucide-react"
import { Card } from "@/components/ui/card"

interface MessageProps {
  message: {
    role: "user" | "assistant"
    content: string
  }
}

export default function ChatMessage({ message }: MessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && <Bot className="w-6 h-6 text-primary flex-shrink-0 mt-1" />}
      <Card className={`max-w-2xl p-4 ${isUser ? "bg-primary text-primary-foreground" : "bg-card text-foreground"}`}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
      </Card>
      {isUser && <MessageCircle className="w-6 h-6 text-primary flex-shrink-0 mt-1" />}
    </div>
  )
}
