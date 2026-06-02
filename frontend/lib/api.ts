const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function postIngest(ytUrl: string, igUrl: string) {
  const res = await fetch(`${BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ yt_url: ytUrl, ig_url: igUrl }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStatus(jobId: string) {
  const res = await fetch(`${BASE}/status/${jobId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMetadata(jobId: string) {
  const res = await fetch(`${BASE}/metadata/${jobId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getTimings(jobId: string) {
  const res = await fetch(`${BASE}/timings/${jobId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function chatStream(question: string, threadId: string, jobId: string) {
  return fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, thread_id: threadId, job_id: jobId }),
  });
}
