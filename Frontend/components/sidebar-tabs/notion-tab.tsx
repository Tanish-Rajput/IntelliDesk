"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"

interface NotionTabProps {
  onSuccess: (message: string) => void
}

export default function NotionTab({ onSuccess }: NotionTabProps) {
  const [apiKey, setApiKey] = useState("")
  const [databaseId, setDatabaseId] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKey.trim() || !databaseId.trim()) return

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append("notion_api_key", apiKey)
      formData.append("notion_db", databaseId)
      formData.append("file", new Blob(), "empty.json") // Empty file

      const response = await fetch("http://localhost:8000/fetchData", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) throw new Error("Failed to fetch Notion data")

      onSuccess("✓ Notion data connected successfully!")
      setApiKey("")
      setDatabaseId("")
    } catch (error) {
      console.error("Error:", error)
      onSuccess("✗ Error connecting Notion data")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="notion-key" className="text-sm font-medium">
          Notion API Key
        </Label>
        <Input
          id="notion-key"
          type="password"
          placeholder="ntn_***"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="text-sm"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="notion-db" className="text-sm font-medium">
          Database ID
        </Label>
        <Input
          id="notion-db"
          placeholder="Enter your Notion database ID"
          value={databaseId}
          onChange={(e) => setDatabaseId(e.target.value)}
          className="text-sm"
        />
      </div>

      <Button type="submit" disabled={loading || !apiKey.trim() || !databaseId.trim()} className="w-full gap-2">
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Connecting...
          </>
        ) : (
          "Connect Notion"
        )}
      </Button>
    </form>
  )
}
