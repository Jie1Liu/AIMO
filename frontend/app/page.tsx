"use client";

import {
  Activity,
  CheckCircle2,
  ClipboardList,
  Database,
  History,
  KeyRound,
  Lightbulb,
  MessageSquareText,
  Play,
  PlusCircle,
  RefreshCw,
  Search,
  Send,
  Server,
  Trash2,
  Users,
  Wand2
} from "lucide-react";
import { useMemo, useState } from "react";

type ApiState = "idle" | "ok" | "error";
type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

type ProductRead = {
  id: string;
  company_id: string;
};

type PlatformAccountRead = {
  id: string;
  platform: string;
  account_label: string;
};

type LeadRead = {
  id: string;
  platform: string;
  lead_score: number;
};

type OutreachMessageRead = {
  id: string;
  platform: string;
  status: string;
};

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

type ApiLog = {
  id: string;
  label: string;
  method: HttpMethod;
  path: string;
  ok: boolean;
  status: number | null;
  durationMs: number;
  requestBody?: unknown;
  responseBody?: unknown;
  error?: string;
  createdAt: string;
};

const defaultProduct: ProductForm = {
  company_name: "AIMO Test Company",
  product_name: "AIMO",
  one_liner: "AI CMO for early-stage founders",
  product_description:
    "AIMO helps companies discover potential customers from public social media discussions.",
  target_audience: "early-stage SaaS founders, indie hackers, small business owners",
  growth_goal: "find early users and validate product positioning",
  main_problem: "Founders do not know where to find their first users.",
  solution:
    "AIMO searches public discussions, identifies leads, and generates human-reviewed outreach drafts.",
  competitors: "Apollo, Buffer, Hootsuite",
  keywords: "find early users, startup marketing, social listening",
  negative_keywords: "job, internship, course"
};

const accountTemplates = [
  {
    platform: "reddit",
    account_label: "Founder Reddit",
    platform_username: "aimo_founder",
    auth_type: "manual",
    daily_send_limit: 5
  },
  {
    platform: "youtube",
    account_label: "AIMO YouTube",
    platform_username: "@aimo",
    auth_type: "oauth",
    daily_send_limit: 10
  },
  {
    platform: "bluesky",
    account_label: "AIMO Bluesky",
    platform_username: "aimo.bsky.social",
    auth_type: "app_password",
    daily_send_limit: 12
  }
];

function splitList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function HomePage() {
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
  );
  const [apiState, setApiState] = useState<ApiState>("idle");
  const [busy, setBusy] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<unknown>(null);
  const [lastLabel, setLastLabel] = useState("Response");
  const [logs, setLogs] = useState<ApiLog[]>([]);
  const [productForm, setProductForm] = useState<ProductForm>(defaultProduct);
  const [companyId, setCompanyId] = useState("");
  const [productId, setProductId] = useState("");
  const [leadId, setLeadId] = useState("");
  const [messageId, setMessageId] = useState("");
  const [accountIds, setAccountIds] = useState<Record<string, string>>({});
  const [manualMethod, setManualMethod] = useState<HttpMethod>("GET");
  const [manualPath, setManualPath] = useState("/health");
  const [manualBody, setManualBody] = useState("{\n\n}");

  const statusText = useMemo(() => {
    if (apiState === "ok") return "Connected";
    if (apiState === "error") return "Request failed";
    return "Idle";
  }, [apiState]);

  const canUseBody = manualMethod === "POST" || manualMethod === "PATCH";

  function updateProductField(field: keyof ProductForm, value: string) {
    setProductForm((current) => ({ ...current, [field]: value }));
  }

  function buildProductPayload() {
    return {
      company_name: productForm.company_name,
      product_name: productForm.product_name,
      one_liner: productForm.one_liner,
      product_description: productForm.product_description,
      target_audience: productForm.target_audience,
      growth_goal: productForm.growth_goal,
      main_problem: productForm.main_problem,
      solution: productForm.solution,
      competitors: splitList(productForm.competitors),
      keywords: splitList(productForm.keywords),
      negative_keywords: splitList(productForm.negative_keywords)
    };
  }

  function requireValue(value: string, label: string) {
    if (!value.trim()) {
      throw new Error(`${label} is required`);
    }
    return value.trim();
  }

  async function apiRequest<T>(
    label: string,
    method: HttpMethod,
    path: string,
    body?: unknown
  ): Promise<T> {
    const started = performance.now();
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    const url = `${apiUrl.replace(/\/$/, "")}${normalizedPath}`;
    let status: number | null = null;
    let responseBody: unknown;
    let errorText: string | undefined;

    try {
      const response = await fetch(url, {
        method,
        headers: body === undefined ? undefined : { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body)
      });
      status = response.status;
      const text = await response.text();
      responseBody = text ? JSON.parse(text) : null;
      if (!response.ok) {
        errorText =
          typeof responseBody === "object" && responseBody && "detail" in responseBody
            ? String((responseBody as { detail: unknown }).detail)
            : response.statusText;
        throw new Error(errorText);
      }
      setApiState("ok");
      return responseBody as T;
    } catch (error) {
      errorText = error instanceof Error ? error.message : "Request failed";
      setApiState("error");
      throw error;
    } finally {
      const entry: ApiLog = {
        id: makeId(),
        label,
        method,
        path: normalizedPath,
        ok: !errorText,
        status,
        durationMs: Math.round(performance.now() - started),
        requestBody: body,
        responseBody,
        error: errorText,
        createdAt: new Date().toLocaleTimeString()
      };
      setLogs((current) => [entry, ...current].slice(0, 30));
      setLastLabel(label);
      setLastResult(errorText ? { error: errorText, response: responseBody } : responseBody);
    }
  }

  async function run(label: string, action: () => Promise<unknown>) {
    setBusy(label);
    try {
      await action();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Request failed";
      setLastLabel(label);
      setLastResult({ error: message });
    } finally {
      setBusy(null);
    }
  }

  async function createProduct() {
    const product = await apiRequest<ProductRead>("Create Product", "POST", "/api/products", buildProductPayload());
    setCompanyId(product.company_id);
    setProductId(product.id);
    return product;
  }

  async function createDemoAccounts(targetCompanyId = requireValue(companyId, "Company ID")) {
    const accounts: PlatformAccountRead[] = [];
    const nextAccountIds: Record<string, string> = {};
    for (const template of accountTemplates) {
      const account = await apiRequest<PlatformAccountRead>(
        `Create ${template.platform} Account`,
        "POST",
        "/api/platform-accounts",
        { ...template, company_id: targetCompanyId }
      );
      accounts.push(account);
      nextAccountIds[account.platform] = account.id;
    }
    setAccountIds((current) => ({ ...current, ...nextAccountIds }));
    setLastLabel("Create Demo Accounts");
    setLastResult(accounts);
    return accounts;
  }

  async function generateStrategies(targetProductId = requireValue(productId, "Product ID")) {
    return apiRequest("Generate Strategies", "POST", `/api/products/${targetProductId}/generate-search-strategies`);
  }

  async function runSearch(targetProductId = requireValue(productId, "Product ID")) {
    return apiRequest("Run Search", "POST", `/api/products/${targetProductId}/run-search`, {
      process_now: true
    });
  }

  async function loadLeads(targetProductId = requireValue(productId, "Product ID")) {
    const leads = await apiRequest<LeadRead[]>(
      "Load Leads",
      "GET",
      `/api/products/${targetProductId}/leads?min_score=40`
    );
    setLeadId(leads[0]?.id ?? "");
    return leads;
  }

  async function createOutreach(targetLeadId = requireValue(leadId, "Lead ID")) {
    const message = await apiRequest<OutreachMessageRead>(
      "Create Outreach",
      "POST",
      `/api/leads/${targetLeadId}/outreach-message`,
      { message_type: "reply", tone: "helpful" }
    );
    setMessageId(message.id);
    return message;
  }

  async function approveOutreach(targetMessageId = requireValue(messageId, "Message ID")) {
    return apiRequest("Approve Outreach", "POST", `/api/outreach-messages/${targetMessageId}/approve`);
  }

  async function sendOutreach(targetMessageId = requireValue(messageId, "Message ID")) {
    return apiRequest("Send Outreach", "POST", `/api/outreach-messages/${targetMessageId}/send`);
  }

  async function generateInsights(targetProductId = requireValue(productId, "Product ID")) {
    return apiRequest("Generate Insights", "POST", `/api/products/${targetProductId}/generate-insights`);
  }

  async function runHappyPath() {
    const product = await createProduct();
    await createDemoAccounts(product.company_id);
    await generateStrategies(product.id);
    await runSearch(product.id);
    const leads = await loadLeads(product.id);
    if (!leads[0]) throw new Error("No leads returned");
    const message = await createOutreach(leads[0].id);
    await approveOutreach(message.id);
    const sendResult = await sendOutreach(message.id);
    const advisorResult = await generateInsights(product.id);
    setLastLabel("Full Flow Complete");
    setLastResult({ product, first_lead: leads[0], message, send_result: sendResult, advisor_result: advisorResult });
  }

  async function sendManualRequest() {
    let body: unknown = undefined;
    if (canUseBody && manualBody.trim()) {
      body = JSON.parse(manualBody);
    }
    return apiRequest("Manual Request", manualMethod, manualPath, body);
  }

  function clearLocalState() {
    setCompanyId("");
    setProductId("");
    setLeadId("");
    setMessageId("");
    setAccountIds({});
    setLogs([]);
    setLastLabel("Response");
    setLastResult(null);
    setApiState("idle");
  }

  return (
    <main className="page">
      <div className="shell">
        <header className="topbar">
          <div>
            <h1>AIMO Backend Testbench</h1>
            <div className="subline">
              <span>FastAPI</span>
              <span>Aurora PostgreSQL flow</span>
              <span>Human-reviewed outreach</span>
            </div>
          </div>
          <div className={`status ${apiState}`}>
            <Activity size={16} />
            {statusText}
          </div>
        </header>

        <section className="column left-column">
          <div className="panel">
            <div className="panel-title">
              <Server size={17} />
              Connection
            </div>
            <div className="grid two">
              <label className="field wide">
                <span>API URL</span>
                <input value={apiUrl} onChange={(event) => setApiUrl(event.target.value)} />
              </label>
              <button className="icon-button" title="Check backend health" disabled={Boolean(busy)} onClick={() => run("Health", () => apiRequest("Health", "GET", "/health"))}>
                <RefreshCw size={18} />
              </button>
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <Database size={17} />
              Product Profile
            </div>
            <div className="grid two">
              <label className="field">
                <span>Company</span>
                <input value={productForm.company_name} onChange={(event) => updateProductField("company_name", event.target.value)} />
              </label>
              <label className="field">
                <span>Product</span>
                <input value={productForm.product_name} onChange={(event) => updateProductField("product_name", event.target.value)} />
              </label>
              <label className="field wide">
                <span>One-liner</span>
                <input value={productForm.one_liner} onChange={(event) => updateProductField("one_liner", event.target.value)} />
              </label>
              <label className="field wide">
                <span>Description</span>
                <textarea value={productForm.product_description} onChange={(event) => updateProductField("product_description", event.target.value)} />
              </label>
              <label className="field wide">
                <span>Target audience</span>
                <input value={productForm.target_audience} onChange={(event) => updateProductField("target_audience", event.target.value)} />
              </label>
              <label className="field wide">
                <span>Growth goal</span>
                <input value={productForm.growth_goal} onChange={(event) => updateProductField("growth_goal", event.target.value)} />
              </label>
              <label className="field wide">
                <span>Main problem</span>
                <input value={productForm.main_problem} onChange={(event) => updateProductField("main_problem", event.target.value)} />
              </label>
              <label className="field wide">
                <span>Solution</span>
                <textarea value={productForm.solution} onChange={(event) => updateProductField("solution", event.target.value)} />
              </label>
              <label className="field">
                <span>Competitors</span>
                <input value={productForm.competitors} onChange={(event) => updateProductField("competitors", event.target.value)} />
              </label>
              <label className="field">
                <span>Keywords</span>
                <input value={productForm.keywords} onChange={(event) => updateProductField("keywords", event.target.value)} />
              </label>
              <label className="field wide">
                <span>Negative keywords</span>
                <input value={productForm.negative_keywords} onChange={(event) => updateProductField("negative_keywords", event.target.value)} />
              </label>
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <KeyRound size={17} />
              Working IDs
            </div>
            <div className="grid two">
              <label className="field">
                <span>Company ID</span>
                <input value={companyId} onChange={(event) => setCompanyId(event.target.value)} />
              </label>
              <label className="field">
                <span>Product ID</span>
                <input value={productId} onChange={(event) => setProductId(event.target.value)} />
              </label>
              <label className="field">
                <span>Lead ID</span>
                <input value={leadId} onChange={(event) => setLeadId(event.target.value)} />
              </label>
              <label className="field">
                <span>Message ID</span>
                <input value={messageId} onChange={(event) => setMessageId(event.target.value)} />
              </label>
            </div>
            <div className="chips">
              {["reddit", "youtube", "bluesky"].map((platform) => (
                <span key={platform} className="chip" title={accountIds[platform] || "No account ID"}>
                  {platform}: {accountIds[platform] ? "ready" : "empty"}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="column right-column">
          <div className="panel workflow">
            <div className="panel-title">
              <Wand2 size={17} />
              Workflow
            </div>
            <div className="button-grid">
              <button className="primary span" disabled={Boolean(busy)} onClick={() => run("Full Flow", runHappyPath)}>
                <Play size={18} />
                Run Full Flow
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Create Product", createProduct)}>
                <PlusCircle size={17} />
                Product
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Create Demo Accounts", () => createDemoAccounts())}>
                <Users size={17} />
                Accounts
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Generate Strategies", () => generateStrategies())}>
                <ClipboardList size={17} />
                Strategies
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Run Search", () => runSearch())}>
                <Search size={17} />
                Search
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Load Leads", () => loadLeads())}>
                <Users size={17} />
                Leads
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Create Outreach", () => createOutreach())}>
                <MessageSquareText size={17} />
                Outreach
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Approve Outreach", () => approveOutreach())}>
                <CheckCircle2 size={17} />
                Approve
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Send Outreach", () => sendOutreach())}>
                <Send size={17} />
                Send
              </button>
              <button disabled={Boolean(busy)} onClick={() => run("Generate Insights", () => generateInsights())}>
                <Lightbulb size={17} />
                Insights
              </button>
              <button className="quiet" disabled={Boolean(busy)} onClick={clearLocalState}>
                <Trash2 size={17} />
                Clear UI
              </button>
            </div>
          </div>

          <div className="panel playground">
            <div className="panel-title">
              <Send size={17} />
              Manual Request
            </div>
            <div className="manual-row">
              <select value={manualMethod} onChange={(event) => setManualMethod(event.target.value as HttpMethod)}>
                <option>GET</option>
                <option>POST</option>
                <option>PATCH</option>
                <option>DELETE</option>
              </select>
              <input value={manualPath} onChange={(event) => setManualPath(event.target.value)} />
              <button className="primary" disabled={Boolean(busy)} onClick={() => run("Manual Request", sendManualRequest)}>
                <Send size={17} />
                Send
              </button>
            </div>
            <textarea
              className="body-editor"
              disabled={!canUseBody}
              value={manualBody}
              onChange={(event) => setManualBody(event.target.value)}
            />
          </div>

          <div className="split">
            <div className="panel response-panel">
              <div className="result-bar">
                <div>
                  <div className="panel-title compact">{lastLabel}</div>
                  <div className="small">{busy ? `Running ${busy}` : "Ready"}</div>
                </div>
              </div>
              {lastResult ? (
                <pre className="json">{formatJson(lastResult)}</pre>
              ) : (
                <div className="empty">No response yet.</div>
              )}
            </div>

            <div className="panel history-panel">
              <div className="panel-title">
                <History size={17} />
                Request History
              </div>
              <div className="history-list">
                {logs.length === 0 ? (
                  <div className="empty small-empty">No requests yet.</div>
                ) : (
                  logs.map((log) => (
                    <button
                      key={log.id}
                      className={`history-row ${log.ok ? "success" : "failed"}`}
                      onClick={() => {
                        setLastLabel(log.label);
                        setLastResult(log.ok ? log.responseBody : { error: log.error, response: log.responseBody });
                      }}
                    >
                      <span className="method">{log.method}</span>
                      <span className="history-main">
                        <strong>{log.label}</strong>
                        <small>{log.path}</small>
                      </span>
                      <span className="history-meta">
                        {log.status ?? "-"} · {log.durationMs}ms
                      </span>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
