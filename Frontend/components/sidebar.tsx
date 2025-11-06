"use client"

import { useState } from "react"
import { ChevronLeft, ChevronRight, FileText, Database, Cloud } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import NotionTab from "./sidebar-tabs/notion-tab"
import GoogleTab from "./sidebar-tabs/google-tab"
import PdfTab from "./sidebar-tabs/pdf-tab"
import SuccessAlert from "./success-alert"

type TabType = "notion" | "google" | "pdf"

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  onDataSourceUpdate: () => void
}

export default function Sidebar({ isOpen, onToggle, onDataSourceUpdate }: SidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>("notion")
  const [successMessage, setSuccessMessage] = useState("")

  const showSuccess = (message: string) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(""), 3000)
  }

  return (
    <>
      {/* Sidebar */}
      <div
        className={`${
          isOpen ? "w-80" : "w-0"
        } bg-card border-r border-border transition-all duration-300 overflow-hidden flex flex-col`}
      >
        <div className="p-4 space-y-4 flex-1 overflow-y-auto">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold text-foreground">Data Sources</h2>
            <p className="text-sm text-muted-foreground">Connect your data sources for RAG</p>
          </div>

          {/* Tab Buttons */}
          <div className="flex gap-2">
            <Button
              variant={activeTab === "notion" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("notion")}
              className="flex-1 gap-2"
            >
              <Database className="w-4 h-4" />
              Notion
            </Button>
            <Button
              variant={activeTab === "google" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("google")}
              className="flex-1 gap-2"
            >
              <Cloud className="w-4 h-4" />
              Google
            </Button>
            <Button
              variant={activeTab === "pdf" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("pdf")}
              className="flex-1 gap-2"
            >
              <FileText className="w-4 h-4" />
              PDF
            </Button>
          </div>

          {/* Tab Content */}
          <Card className="p-4 bg-background/50">
            {activeTab === "notion" && (
              <NotionTab
                onSuccess={(msg) => {
                  showSuccess(msg)
                  onDataSourceUpdate()
                }}
              />
            )}
            {activeTab === "google" && (
              <GoogleTab
                onSuccess={(msg) => {
                  showSuccess(msg)
                  onDataSourceUpdate()
                }}
              />
            )}
            {activeTab === "pdf" && (
              <PdfTab
                onSuccess={(msg) => {
                  showSuccess(msg)
                  onDataSourceUpdate()
                }}
              />
            )}
          </Card>
        </div>
      </div>

      {/* Toggle Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggle}
        className="absolute left-0 top-4 z-10 rounded-r-lg border-l-0"
      >
        {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </Button>

      {/* Success Alert */}
      {successMessage && <SuccessAlert message={successMessage} />}
    </>
  )
}
