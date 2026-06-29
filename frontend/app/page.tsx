"use client";

import {
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  ChevronDown,
  ExternalLink,
  Eye,
  LoaderCircle,
  MessageCircle,
  MessageSquareText,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  SkipForward,
  Sparkles,
  Users
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type ProductForm = {
  company_name: string;
  product_name: string;
  one_liner: string;
  product_description: string;
  target_audience: string;
  growth_goal: string;
  main_problem: string;
  solution: string;
  competitors: string;
  keywords: string;
  negative_keywords: string;
};

type ProductRead = {
  id: string;
  company_id: string;
};

type SearchJobRead = {
  status: string;
  error_message: string | null;
};

type BlueskyStatus = {
  configured: boolean;
  connected: boolean;
  handle: string | null;
  account_id: string | null;
};

type SocialItemRead = {
  id: string;
  content_text: string;
  content_url: string | null;
  source_title: string | null;
  engagement_score: number;
  published_at: string | null;
  raw_json: Record<string, unknown>;
};

type LeadRead = {
  id: string;
  author_name: string | null;
  intent_type: string;
  lead_score: number;
  confidence: number;
  pain_point: string | null;
  user_need: string | null;
  reason: string | null;
  social_item: SocialItemRead | null;
};

type MessageRead = {
  id: string;
  lead_id: string;
  draft_text: string;
  final_text: string | null;
  risk_level: string;
  policy_notes: Record<string, unknown>;
  status: string;
};

type SendResponse = {
  message: MessageRead;
  action: string;
  log: { error_message: string | null; platform_response_id: string | null };
};

type ReviewItem = {
  lead: LeadRead;
  message: MessageRead;
  reply: string;
  localStatus: "ready" | "skipped" | "sent";
  sentUrl?: string | null;
};

const initialProduct: ProductForm = {
  company_name: "AIMO Studio",
  product_name: "AIMO",
  one_liner: "AI marketing copilot for early-stage teams",
  product_description:
    "AIMO helps founders find relevant public conversations, understand user intent, and prepare thoughtful replies.",
  target_audience: "SaaS founders, indie hackers, and small product teams",
  growth_goal: "Find early users and validate product positioning",
  main_problem: "Founders struggle to find the right early users and join relevant conversations",
  solution:
    "Surface high-intent public discussions and create useful, human-reviewed replies grounded in each person's context.",
  competitors: "Apollo, Hootsuite, Buffer",
  keywords: "startup marketing, find customers, early users",
  negative_keywords: "job, hiring, course, giveaway"
};

function splitList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function excerpt(value: string, max = 180) {
  return value.length > max ? `${value.slice(0, max).trim()}…` : value;
}

function formatIntent(value: string) {
  return value.replaceAll("_", " ");
}

export default function HomePage() {
  const [apiUrl] = useState(() => {
    const configured = process.env.NEXT_PUBLIC_API_URL;
    if (configured) return configured.replace(/\/$/, "");
    if (
      typeof window !== "undefined" &&
      ["localhost", "127.0.0.1"].includes(window.location.hostname)
    ) {
      return "http://127.0.0.1:8000";
    }
    return "https://aimo-backend.zeabur.app";
  });
  const [product, setProduct] = useState<ProductForm>(initialProduct);
  const [platform, setPlatform] = useState<BlueskyStatus | null>(null);
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [stage, setStage] = useState("Ready to discover");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [platformMenuOpen, setPlatformMenuOpen] = useState(false);

  const selected = useMemo(
    () => queue.find((item) => item.message.id === selectedId) ?? null,
    [queue, selectedId]
  );
  const sentCount = queue.filter((item) => item.localStatus === "sent").length;
  const readyCount = queue.filter((item) => item.localStatus === "ready").length;

  useEffect(() => {
    void loadPlatformStatus();
  }, []);

  async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${apiUrl}${path}`, {
      ...options,
      headers: {
        ...(options?.body ? { "Content-Type": "application/json" } : {}),
        ...(options?.headers ?? {})
      }
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;
    if (!response.ok) {
      const detail = data && typeof data === "object" ? data.detail : null;
      throw new Error(typeof detail === "string" ? detail : response.statusText || "Request failed");
    }
    return data as T;
  }

  async function loadPlatformStatus() {
    try {
      const status = await request<BlueskyStatus>("/api/integrations/bluesky/status");
      setPlatform(status);
    } catch {
      setPlatform({ configured: false, connected: false, handle: null, account_id: null });
    }
  }

  function updateProduct(field: keyof ProductForm, value: string) {
    setProduct((current) => ({ ...current, [field]: value }));
  }

  function productPayload() {
    return {
      ...product,
      competitors: splitList(product.competitors),
      keywords: splitList(product.keywords),
      negative_keywords: splitList(product.negative_keywords)
    };
  }

  async function findUsers() {
    setBusy("discover");
    setError(null);
    setNotice(null);
    setQueue([]);
    setSelectedId(null);
    try {
      setStage("Saving product brief");
      const created = await request<ProductRead>("/api/products", {
        method: "POST",
        body: JSON.stringify(productPayload())
      });

      if (platform?.configured) {
        setStage("Connecting your Bluesky account");
        try {
          await request("/api/integrations/bluesky/connect", {
            method: "POST",
            body: JSON.stringify({ company_id: created.company_id })
          });
          await loadPlatformStatus();
        } catch {
          // Public discovery still works without write credentials.
        }
      }

      setStage("Building search strategy");
      await request(`/api/products/${created.id}/generate-search-strategies`, { method: "POST" });

      setStage("Searching live Bluesky conversations");
      const jobs = await request<SearchJobRead[]>(`/api/products/${created.id}/run-search`, {
        method: "POST",
        body: JSON.stringify({ platforms: ["bluesky"], process_now: true })
      });
      const failedJob = jobs.find((job) => job.status === "failed");
      if (failedJob) {
        throw new Error(failedJob.error_message || "Bluesky search failed.");
      }

      setStage("Ranking the strongest user signals");
      const leads = await request<LeadRead[]>(
        `/api/products/${created.id}/leads?platform=bluesky&min_score=40`
      );
      const candidateLeads = leads
        .filter((lead) => lead.social_item?.content_text)
        .filter(
          (lead, index, values) =>
            values.findIndex((candidate) => candidate.author_name === lead.author_name) === index
        )
        .slice(0, 8);
      if (!candidateLeads.length) {
        throw new Error("No strong Bluesky matches were found. Try broader keywords.");
      }

      setStage(`Writing personalized replies`);
      const messages = await Promise.all(
        candidateLeads.map((lead) =>
          request<MessageRead>(`/api/leads/${lead.id}/outreach-message`, {
            method: "POST",
            body: JSON.stringify({ message_type: "reply", tone: "helpful" })
          })
        )
      );
      const nextQueue = candidateLeads
        .map((lead, index) => ({
          lead,
          message: messages[index],
          reply: messages[index].draft_text,
          localStatus: "ready" as const
        }))
        .filter((item) => !["high", "blocked"].includes(item.message.risk_level))
        .slice(0, 5);
      if (!nextQueue.length) {
        throw new Error("Matches were found, but none passed the outreach safety checks.");
      }
      setQueue(nextQueue);
      setSelectedId(nextQueue[0].message.id);
      setStage(`${nextQueue.length} replies ready for review`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Discovery failed");
      setStage("Discovery needs attention");
    } finally {
      setBusy(null);
    }
  }

  function updateReply(value: string) {
    if (!selected) return;
    setQueue((current) =>
      current.map((item) => (item.message.id === selected.message.id ? { ...item, reply: value } : item))
    );
  }

  function selectNext(afterId: string) {
    const currentIndex = queue.findIndex((item) => item.message.id === afterId);
    const next =
      queue.slice(currentIndex + 1).find((item) => item.localStatus === "ready") ??
      queue.find((item) => item.localStatus === "ready" && item.message.id !== afterId);
    setSelectedId(next?.message.id ?? afterId);
  }

  function skipSelected() {
    if (!selected) return;
    setQueue((current) =>
      current.map((item) =>
        item.message.id === selected.message.id ? { ...item, localStatus: "skipped" } : item
      )
    );
    setNotice(`Skipped @${selected.lead.author_name ?? "user"}.`);
    selectNext(selected.message.id);
  }

  async function regenerateSelected() {
    if (!selected) return;
    setBusy("regenerate");
    setError(null);
    try {
      const message = await request<MessageRead>(
        `/api/outreach-messages/${selected.message.id}/regenerate`,
        { method: "POST" }
      );
      setQueue((current) =>
        current.map((item) =>
          item.message.id === message.id
            ? { ...item, message, reply: message.draft_text, localStatus: "ready" }
            : item
        )
      );
      setNotice("A fresh reply is ready.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not regenerate reply");
    } finally {
      setBusy(null);
    }
  }

  async function approveAndSend() {
    if (!selected) return;
    if (!platform?.connected) {
      setError("Add BLUESKY_HANDLE and BLUESKY_APP_PASSWORD to the backend before sending.");
      return;
    }
    setBusy("send");
    setError(null);
    setNotice(null);
    try {
      const updated = await request<MessageRead>(
        `/api/outreach-messages/${selected.message.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ final_text: selected.reply })
        }
      );
      await request(`/api/outreach-messages/${updated.id}/approve`, { method: "POST" });
      const result = await request<SendResponse>(`/api/outreach-messages/${updated.id}/send`, {
        method: "POST"
      });
      if (result.message.status !== "sent") {
        throw new Error(result.log.error_message || "Bluesky did not accept the reply.");
      }
      setQueue((current) =>
        current.map((item) =>
          item.message.id === selected.message.id
            ? {
                ...item,
                message: result.message,
                localStatus: "sent",
                sentUrl: result.log.platform_response_id
              }
            : item
        )
      );
      setNotice(`Reply sent from @${platform.handle}.`);
      selectNext(selected.message.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not send reply");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <img src="/aimo-logo.svg" alt="" />
          </div>
          <div>
            <strong>AIMO</strong>
            <span>Your AI CMO, in motion.</span>
          </div>
        </div>

        <div className="platform-switcher">
          <button
            type="button"
            className="add-platform-button"
            aria-expanded={platformMenuOpen}
            onClick={() => setPlatformMenuOpen((current) => !current)}
          >
            <span className="add-platform-icon"><Plus size={14} /></span>
            Add another platform
            <ChevronDown className={platformMenuOpen ? "open" : ""} size={15} />
          </button>
          {platformMenuOpen && (
            <div className="platform-dropdown" role="menu" aria-label="Other platforms">
              <div className="platform-option" role="menuitem" aria-disabled="true">
                <span className="platform-option-icon x-icon">X</span>
                <div>
                  <strong>X / Twitter</strong>
                  <small>Coming soon</small>
                </div>
              </div>
              <div className="platform-option" role="menuitem" aria-disabled="true">
                <span className="platform-option-icon reddit-icon"><MessageCircle size={16} /></span>
                <div>
                  <strong>Reddit</strong>
                  <small>Coming soon</small>
                </div>
              </div>
              <p>Preview only · API integrations coming soon</p>
            </div>
          )}
        </div>

        <div className="platform-card">
          <div className="platform-icon"><Radio size={18} /></div>
          <div>
            <span>LIVE SOURCE</span>
            <strong>Bluesky</strong>
          </div>
          <div className={`connection-dot ${platform?.connected ? "online" : ""}`} />
        </div>

        <section className="brief">
          <div className="section-heading">
            <span>Product brief</span>
            <small>01</small>
          </div>
          <label>
            Product
            <input value={product.product_name} onChange={(e) => updateProduct("product_name", e.target.value)} />
          </label>
          <label>
            One-line pitch
            <input value={product.one_liner} onChange={(e) => updateProduct("one_liner", e.target.value)} />
          </label>
          <label>
            Who is it for?
            <textarea value={product.target_audience} onChange={(e) => updateProduct("target_audience", e.target.value)} />
          </label>
          <label>
            Problem you solve
            <textarea value={product.main_problem} onChange={(e) => updateProduct("main_problem", e.target.value)} />
          </label>
          <label>
            Your solution
            <textarea value={product.solution} onChange={(e) => updateProduct("solution", e.target.value)} />
          </label>
          <label>
            Search signals
            <input value={product.keywords} onChange={(e) => updateProduct("keywords", e.target.value)} />
            <small>Separate keywords with commas</small>
          </label>
          <button className="discover-button" disabled={Boolean(busy)} onClick={findUsers}>
            {busy === "discover" ? <LoaderCircle className="spin" size={18} /> : <Search size={18} />}
            Find users
            {!busy && <ArrowRight size={17} />}
          </button>
        </section>

        <div className="safety-note">
          <ShieldCheck size={17} />
          <p><strong>Human-controlled.</strong> AIMO never sends without your review.</p>
        </div>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Bluesky outreach workspace</p>
            <h1>Review the conversations that matter.</h1>
          </div>
          <div className="header-status">
            <span className={platform?.connected ? "status-live" : "status-search"}>
              {platform?.connected ? <CheckCircle2 size={15} /> : <Eye size={15} />}
              {platform?.connected ? `@${platform.handle}` : "Search-only mode"}
            </span>
            <span className="model-pill"><Bot size={15} /> AI + safe fallback</span>
          </div>
        </header>

        <div className="progress-strip">
          <div className={queue.length ? "done" : busy ? "active" : ""}><Check size={14} /> Brief</div>
          <span />
          <div className={busy === "discover" ? "active" : queue.length ? "done" : ""}><Search size={14} /> Discover</div>
          <span />
          <div className={queue.length ? "active" : ""}><MessageSquareText size={14} /> Review</div>
          <p>{stage}</p>
        </div>

        {error && <div className="alert error-alert">{error}</div>}
        {notice && <div className="alert success-alert">{notice}</div>}
        {!platform?.configured && (
          <div className="credential-banner">
            <div><ShieldCheck size={19} /></div>
            <p>
              <strong>Live search is ready.</strong> To enable sending, create a Bluesky App Password
              and add <code>BLUESKY_HANDLE</code> and <code>BLUESKY_APP_PASSWORD</code> to the backend.
            </p>
          </div>
        )}

        {queue.length === 0 ? (
          <section className="empty-state">
            <div className="signal-orbit">
              <div><Users size={28} /></div>
              <i /><i /><i />
            </div>
            <p className="eyebrow">Your next users are already talking</p>
            <h2>Turn product context into real conversations.</h2>
            <p>
              Define your product, then AIMO searches live Bluesky posts, ranks intent,
              and prepares the five strongest replies for you.
            </p>
            <div className="empty-features">
              <span><Radio size={16} /> Live public signals</span>
              <span><Sparkles size={16} /> Context-aware drafts</span>
              <span><ShieldCheck size={16} /> You approve every send</span>
            </div>
          </section>
        ) : (
          <div className="review-layout">
            <section className="queue-panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Review queue</p>
                  <h2>{readyCount} conversations waiting</h2>
                </div>
                <span>{sentCount}/{queue.length} sent</span>
              </div>
              <div className="queue-list">
                {queue.map((item, index) => (
                  <button
                    key={item.message.id}
                    className={`queue-item ${selectedId === item.message.id ? "selected" : ""} ${item.localStatus}`}
                    onClick={() => setSelectedId(item.message.id)}
                  >
                    <div className="avatar">{(item.lead.author_name ?? "?").slice(0, 1).toUpperCase()}</div>
                    <div className="queue-copy">
                      <div>
                        <strong>@{item.lead.author_name ?? "unknown"}</strong>
                        <span>{item.lead.lead_score}% match</span>
                      </div>
                      <p>{excerpt(item.lead.social_item?.content_text ?? "")}</p>
                      <small>{formatIntent(item.lead.intent_type)} · #{index + 1}</small>
                    </div>
                    {item.localStatus === "sent" && <CheckCircle2 className="sent-icon" size={18} />}
                    {item.localStatus === "skipped" && <SkipForward className="sent-icon" size={18} />}
                  </button>
                ))}
              </div>
            </section>

            {selected && (
              <section className="review-panel">
                <div className="review-topline">
                  <div>
                    <p className="eyebrow">Original conversation</p>
                    <strong>@{selected.lead.author_name ?? "unknown"}</strong>
                  </div>
                  <div className="score-ring">{selected.lead.lead_score}<small>%</small></div>
                </div>

                <div className="original-post">
                  <p>{selected.lead.social_item?.content_text}</p>
                  <div>
                    <span>{selected.lead.social_item?.engagement_score ?? 0} engagement</span>
                    {selected.lead.social_item?.content_url && (
                      <a href={selected.lead.social_item.content_url} target="_blank" rel="noreferrer">
                        Open on Bluesky <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                </div>

                <div className="match-reason">
                  <Sparkles size={17} />
                  <div>
                    <strong>Why this person fits</strong>
                    <p>{selected.lead.reason || selected.lead.user_need}</p>
                  </div>
                </div>

                <div className="draft-heading">
                  <div>
                    <p className="eyebrow">AI-prepared reply</p>
                    <span className={`risk ${selected.message.risk_level}`}>
                      {selected.message.risk_level} risk
                    </span>
                  </div>
                  <button disabled={Boolean(busy)} onClick={regenerateSelected}>
                    {busy === "regenerate" ? <LoaderCircle className="spin" size={15} /> : <RefreshCw size={15} />}
                    Regenerate
                  </button>
                </div>
                <textarea
                  className="reply-editor"
                  value={selected.reply}
                  maxLength={300}
                  disabled={selected.localStatus === "sent"}
                  onChange={(e) => updateReply(e.target.value)}
                />
                <div className="editor-meta">
                  <span>{selected.reply.length} characters</span>
                  <span>
                    Generated by {String(selected.message.policy_notes.generator ?? "template")}
                  </span>
                </div>

                <div className="review-actions">
                  <button className="skip-button" disabled={Boolean(busy)} onClick={skipSelected}>
                    <SkipForward size={17} /> Skip
                  </button>
                  {selected.localStatus === "sent" ? (
                    <a className="sent-button" href={selected.sentUrl ?? "#"} target="_blank" rel="noreferrer">
                      <CheckCircle2 size={17} /> Sent successfully
                    </a>
                  ) : (
                    <button
                      className="send-button"
                      disabled={
                        Boolean(busy) ||
                        !platform?.connected ||
                        !selected.reply.trim() ||
                        ["high", "blocked"].includes(selected.message.risk_level)
                      }
                      onClick={approveAndSend}
                    >
                      {busy === "send" ? <LoaderCircle className="spin" size={17} /> : <Send size={17} />}
                      Approve & send
                    </button>
                  )}
                </div>
                {!platform?.connected && (
                  <p className="send-hint">Connect your Bluesky App Password to enable sending.</p>
                )}
              </section>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
