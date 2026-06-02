"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll<HTMLElement>(".reveal");
    const obs = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) (e.target as HTMLElement).classList.add("revealed");
        }),
      { threshold: 0.1 }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

function TiltCard({ children, className }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.transform = `perspective(700px) rotateY(${x * 18}deg) rotateX(${-y * 18}deg) scale(1.06) translateZ(20px)`;
    el.style.boxShadow = `${-x * 20}px ${-y * 20}px 40px rgba(34,211,238,0.15)`;
  };
  const onLeave = () => {
    if (!ref.current) return;
    ref.current.style.transform = "";
    ref.current.style.boxShadow = "";
  };
  return (
    <div ref={ref} className={`tilt-card ${className ?? ""}`} onMouseMove={onMove} onMouseLeave={onLeave}>
      {children}
    </div>
  );
}

const PIPELINE = [
  { icon: "🔗", label: "URL Input",      time: "< 50ms",  desc: "POST /ingest returns instantly",     color: "#22d3ee" },
  { icon: "▶",  label: "YT Transcript",  time: "~1–2s",   desc: "youtube-transcript-api",             color: "#60a5fa" },
  { icon: "🎙", label: "Groq Whisper",   time: "~10–30s", desc: "Instagram reel transcription",       color: "#f472b6" },
  { icon: "🧠", label: "BGE Embedding",  time: "~2–5s",   desc: "BAAI/bge-small-en-v1.5 CPU",        color: "#a78bfa" },
  { icon: "🗄",  label: "Qdrant Store",  time: "~100ms",  desc: "Parallel A + B upsert",             color: "#34d399" },
  { icon: "🔍", label: "RAG Retrieve",   time: "~15ms",   desc: "asyncio.gather search A + B",       color: "#fbbf24" },
  { icon: "⚡", label: "Groq LLaMA",    time: "~300ms",  desc: "llama-3.3-70b TTFT stream",         color: "#fb923c" },
];

const TECH = [
  { name: "LangGraph", icon: "⬡", color: "#22d3ee", desc: "State graph orchestration" },
  { name: "Qdrant",    icon: "◈", color: "#f472b6", desc: "Vector similarity search" },
  { name: "Groq",      icon: "⚡", color: "#a78bfa", desc: "Sub-second LLM inference" },
  { name: "BGE-small", icon: "🧠", color: "#34d399", desc: "Free local embeddings" },
  { name: "Redis",     icon: "⚙", color: "#fb923c", desc: "Memory & job state" },
  { name: "FastAPI",   icon: "🚀", color: "#60a5fa", desc: "Async Python backend" },
  { name: "Next.js",   icon: "▲", color: "#e2e8f0", desc: "App Router frontend" },
];

const TIMING_ROWS = [
  { stage: "/ingest returns job_id",              ref: "< 50ms",   note: "Non-blocking BackgroundTask" },
  { stage: "YouTube transcript fetch",             ref: "~1–2s",    note: "Via transcript API" },
  { stage: "Instagram download + Groq Whisper",    ref: "~10–30s",  note: "Scales with video duration" },
  { stage: "BGE embedding (CPU, parallel)",        ref: "~2–5s",    note: "ThreadPoolExecutor" },
  { stage: "Qdrant upsert (parallel A+B)",         ref: "~100ms",   note: "Async client" },
  { stage: "Qdrant vector search (parallel A+B)",  ref: "~10–20ms", note: "asyncio.gather" },
  { stage: "Groq LLaMA time-to-first-token",       ref: "~200–400ms", note: "128k context window" },
];

export default function LandingPage() {
  useReveal();
  const [particles, setParticles] = useState<{
    left: string;
    top: string;
    animationDelay: string;
    animationDuration: string;
    width: string;
    height: string;
  }[]>([]);

  useEffect(() => {
    const generated = Array.from({ length: 30 }).map(() => ({
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 8}s`,
      animationDuration: `${6 + Math.random() * 8}s`,
      width: `${2 + Math.random() * 3}px`,
      height: `${2 + Math.random() * 3}px`,
    }));
    setParticles(generated);
  }, []);

  return (
    <div className="landing">
      {/* NAV */}
      <nav className="landing-nav">
        <span className="logo-text"><span className="logo-icon">◈</span> VideoRAG</span>
        <Link href="/app" id="get-started-nav" className="btn-primary btn-sm">Get Started →</Link>
      </nav>

      {/* ── HERO ─────────────────────────────────────────────────── */}
      <section className="hero-section">
        <div className="hero-grid-bg" aria-hidden />
        <div className="hero-particles" aria-hidden>
          {particles.map((p, i) => (
            <span key={i} className="hero-particle" style={p} />
          ))}
        </div>

        <div className="hero-content">
          <div className="hero-badge reveal">RAG · LangGraph · Groq · Qdrant</div>
          <h1 className="hero-title reveal">
            Analyse.<br />Compare.<br />
            <span className="gradient-text">Dominate.</span>
          </h1>
          <p className="hero-sub reveal">
            Drop two social media videos — VideoRAG ingests, embeds, and lets you chat with both
            using a <strong>LangGraph RAG pipeline</strong> powered by Groq's sub-second LLM.
          </p>
          <div className="hero-cta reveal">
            <Link href="/app" id="get-started-hero" className="btn-primary btn-lg">Get Started →</Link>
            <span className="hero-hint">YouTube + Instagram · No sign-up needed</span>
          </div>

          {/* 3D floating stats */}
          <div className="hero-stats reveal">
            {[
              { val: "< 50ms", label: "Response start" },
              { val: "384-dim", label: "BGE vectors" },
              { val: "128k",   label: "LLM context" },
            ].map((s) => (
              <div key={s.label} className="hero-stat-card">
                <span className="hero-stat-val">{s.val}</span>
                <span className="hero-stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="hero-orb hero-orb-a" aria-hidden />
        <div className="hero-orb hero-orb-b" aria-hidden />
        <div className="hero-orb hero-orb-c" aria-hidden />
      </section>

      {/* ── PIPELINE FLOW ─────────────────────────────────────────── */}
      <section className="section pipeline-section">
        <div className="section-inner">
          <h2 className="section-title reveal">How It Works</h2>
          <p className="section-sub reveal">From URL to insight in seconds — every step is parallel and non-blocking.</p>

          <div className="pipeline-grid">
            {PIPELINE.map((node, i) => (
              <div key={node.label} className="pipeline-item reveal" style={{ animationDelay: `${i * 80}ms` }}>
                <div className="pipeline-node-3d" style={{ "--pipe-color": node.color } as React.CSSProperties}>
                  <div className="pipe-number">{i + 1}</div>
                  <span className="pipe-icon-3d">{node.icon}</span>
                  <span className="pipe-label">{node.label}</span>
                  <span className="pipe-time" style={{ color: node.color }}>{node.time}</span>
                  <span className="pipe-desc">{node.desc}</span>
                  {i < PIPELINE.length - 1 && <div className="pipe-connector" />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TIMING TABLE ─────────────────────────────────────────── */}
      <section className="section timing-section">
        <div className="section-inner">
          <h2 className="section-title reveal">Real Pipeline Timings</h2>
          <p className="section-sub reveal">
            Reference values from our e2e test suite. After your job completes, actual timings from your specific videos appear in the app.
          </p>
          <div className="timing-table-wrap reveal">
            <table className="timing-table">
              <thead>
                <tr>
                  <th>Stage</th>
                  <th>Reference Time</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {TIMING_ROWS.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? "row-even" : ""}>
                    <td><code>{row.stage}</code></td>
                    <td><span className="time-badge">{row.ref}</span></td>
                    <td className="note-col">{row.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="timing-note">
              ⚡ Instagram varies most — Groq Whisper transcription scales linearly with audio length (~1s per 20s of video).
            </p>
          </div>
        </div>
      </section>

      {/* ── TECH STACK ───────────────────────────────────────────── */}
      <section className="section tech-section">
        <div className="section-inner">
          <h2 className="section-title reveal">The Stack</h2>
          <p className="section-sub reveal">Every choice is deliberate — free, fast, and production-safe.</p>
          <div className="tech-flex">
            {TECH.map((t) => (
              <TiltCard key={t.name} className="reveal">
                <div className="tech-card" style={{ "--t-color": t.color } as React.CSSProperties}>
                  <span className="tech-icon-wrap" style={{ background: `${t.color}18`, border: `1px solid ${t.color}33` }}>
                    <span className="tech-icon" style={{ color: t.color }}>{t.icon}</span>
                  </span>
                  <span className="tech-name">{t.name}</span>
                  <span className="tech-desc">{t.desc}</span>
                </div>
              </TiltCard>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────── */}
      <section className="section cta-section reveal">
        <div className="cta-inner">
          <h2 className="cta-title">Ready to analyse your videos?</h2>
          <p className="cta-sub">Paste two URLs and ask anything — citations included.</p>
          <Link href="/app" id="get-started-cta" className="btn-primary btn-lg">Launch VideoRAG →</Link>
        </div>
        <div className="hero-orb cta-orb-a" aria-hidden />
        <div className="hero-orb cta-orb-b" aria-hidden />
      </section>

      <footer className="landing-footer">
        <span>VideoRAG · LangGraph + Qdrant + Groq · Built with FastAPI + Next.js</span>
      </footer>
    </div>
  );
}
