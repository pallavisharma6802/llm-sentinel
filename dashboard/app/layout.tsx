import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "LLM Sentinel - Hallucination Detection Dashboard",
  description: "Real-time monitoring and detection of LLM hallucinations",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  )
}
