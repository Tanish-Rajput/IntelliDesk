"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

const SUGGESTIONS = [
  "What are the key topics in my documents?",
  "Summarize the main findings",
  "What questions can I ask you?",
  "Help me understand this project better",
]

interface SuggestedQueriesProps {
  onQuerySelect: (query: string) => void
}

export default function SuggestedQueries({ onQuerySelect }: SuggestedQueriesProps) {
  return (
    <div className="w-full max-w-2xl space-y-2">
      <p className="text-sm text-muted-foreground text-center">Try asking:</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {SUGGESTIONS.map((suggestion, index) => (
          <Button
            key={index}
            variant="outline"
            className="justify-start gap-2 text-left h-auto p-3 bg-transparent"
            onClick={() => onQuerySelect(suggestion)}
          >
            <ArrowRight className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{suggestion}</span>
          </Button>
        ))}
      </div>
    </div>
  )
}
