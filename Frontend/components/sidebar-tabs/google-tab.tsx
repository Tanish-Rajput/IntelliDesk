"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Loader2, Upload } from "lucide-react"

interface GoogleTabProps {
  onSuccess: (message: string) => void
}

export default function GoogleTab({ onSuccess }: GoogleTabProps) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("notion_api_key", "")
      formData.append("notion_db", "")

      const response = await fetch("http://localhost:8000/fetchData", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) throw new Error("Failed to fetch Google Drive data")

      onSuccess("✓ Google Drive connected successfully!")
      setFile(null)
    } catch (error) {
      console.error("Error:", error)
      onSuccess("✗ Error connecting Google Drive")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="google-file" className="text-sm font-medium">
          Google Credentials JSON
        </Label>
        <div className="relative">
          <input id="google-file" type="file" accept=".json" onChange={handleFileChange} className="hidden" />
          <Button
            type="button"
            variant="outline"
            className="w-full gap-2 justify-start bg-transparent"
            onClick={() => document.getElementById("google-file")?.click()}
          >
            <Upload className="w-4 h-4" />
            {file ? file.name : "Choose credentials file"}
          </Button>
        </div>
      </div>

      {file && <p className="text-xs text-muted-foreground">File selected: {file.name}</p>}

      <Button type="submit" disabled={loading || !file} className="w-full gap-2">
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Connecting...
          </>
        ) : (
          "Connect Google Drive"
        )}
      </Button>
    </form>
  )
}
