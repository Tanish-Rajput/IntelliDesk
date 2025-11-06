// src/components/PdfTab.tsx
"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Loader2, Upload } from "lucide-react";
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://rhihmakcvscsodsbmrej.supabase.co";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJoaWhtYWtjdnNjc29kc2JtcmVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE3MTY2NjQsImV4cCI6MjA3NzI5MjY2NH0.HoGQ-mM1gpoY9c6-MG9-1hlrij-myENqyb8jDkhIcnM";

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn("Supabase URL or KEY missing. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY");
}

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);


interface PdfTabProps {
  onSuccess: (message: string) => void;
}

export default function PdfTab({ onSuccess }: PdfTabProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
    } else {
      alert("Please select a valid PDF file");
    }
  };

  // Helper to create a safe filename (optional)
  const makeSafeFilename = (name: string) => {
    // you can add timestamp or user-id prefix to avoid collisions
    const ts = Date.now();
    return `${ts}__${name.replace(/\s+/g, "_")}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setProgress(null);

    try {
      const bucket = "Pdfs"; // ensure bucket exists in Supabase dashboard
      const safeName = makeSafeFilename(file.name);

      // Upload to Supabase. Note: supabase-js storage.upload does not provide a progress callback.
      // For large files with progress, consider generating a signed URL on the backend and uploading via fetch.
      const { data, error } = await supabase.storage.from(bucket).upload(safeName, file, {
        cacheControl: "3600",
        upsert: true,
      });

      if (error) {
        console.error("Supabase upload error:", error);
        throw error;
      }

      // Optionally confirm public URL or path (if needed)
      // const { publicURL } = supabase.storage.from(bucket).getPublicUrl(safeName);

      // Notify the FastAPI backend with the filename
      const backendResp = await fetch("http://localhost:8000/pdfData", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pdf_file: safeName }),
      });

      if (!backendResp.ok) {
        const body = await backendResp.text();
        throw new Error(`Backend responded with ${backendResp.status}: ${body}`);
      }

      onSuccess("✓ PDF uploaded to Supabase and backend notified successfully!");
      setFile(null);
    } catch (err) {
      console.error(err);
      onSuccess(`✗ Error: ${(err as Error).message}`);
    } finally {
      setLoading(false);
      setProgress(null);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="pdf-file" className="text-sm font-medium">
          Upload PDF
        </Label>
        <div className="relative">
          <input id="pdf-file" type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
          <Button
            type="button"
            variant="outline"
            className="w-full gap-2 justify-start bg-transparent"
            onClick={() => document.getElementById("pdf-file")?.click()}
          >
            <Upload className="w-4 h-4" />
            {file ? file.name : "Choose PDF file"}
          </Button>
        </div>
      </div>

      {file && (
        <p className="text-xs text-muted-foreground">
          File selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
        </p>
      )}

      {/* Progress (if you implement a signed URL upload with fetch you can set progress) */}
      {progress !== null && <p className="text-xs">Upload progress: {progress}%</p>}

      <Button type="submit" disabled={loading || !file} className="w-full gap-2">
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Processing...
          </>
        ) : (
          "Upload PDF"
        )}
      </Button>
    </form>
  );
}
