import type { Metadata } from "next";
import { Space_Grotesk, Orbitron } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "600", "700", "900"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "VideoRAG — Analyse & Compare Social Media Videos with AI",
  description:
    "Drop YouTube and Instagram video URLs. VideoRAG ingests transcripts, embeds them with BGE-small, stores in Qdrant, and lets you chat using LangGraph + Groq for instant, cited insights.",
  keywords: ["video analysis", "RAG", "LangGraph", "Qdrant", "Groq", "YouTube", "Instagram", "AI chatbot"],
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    shortcut: "/favicon.svg",
  },
  openGraph: {
    title: "VideoRAG — AI Video Analysis",
    description: "Compare social media videos using RAG. Citations. Real-time streaming. Sub-second latency.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${orbitron.variable}`}>
      <body>{children}</body>
    </html>
  );
}
