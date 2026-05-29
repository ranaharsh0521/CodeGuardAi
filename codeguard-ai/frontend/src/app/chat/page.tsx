'use client';

import { FormEvent, Suspense, useEffect, useRef, useState } from 'react';
import { Bot, CheckCircle, FileSearch, LockKeyhole, Send, ShieldCheck, User } from 'lucide-react';
import { chatService, ChatMessage } from '@/lib/chat-service';
import { useSearchParams } from 'next/navigation';


const assistantRules = [
  'Only CodeGuard AI project, scan, finding, auth, report, upload, team, schedule, and debugging questions.',
  'Never expose secrets, tokens, passwords, or raw .env values.',
  'For vulnerabilities, explain risk, give fix steps, then recommend re-scan and triage.',
  'For unclear errors, ask for scan id, endpoint, file path, or latest log.',
];

const quickPrompts = [
  {
    label: 'Scan workflow',
    prompt: 'Explain the CodeGuard scan workflow and what I should check after a scan completes.',
    icon: FileSearch,
  },
  {
    label: 'OAuth error',
    prompt: 'How should I debug Google or GitHub OAuth errors in this project?',
    icon: LockKeyhole,
  },
  {
    label: 'Finding triage',
    prompt: 'How should I use open, resolved, ignored, and false positive statuses for scan findings?',
    icon: ShieldCheck,
  },
  {
    label: 'Project rules',
    prompt: 'Show the chat rules for the CodeGuard AI assistant.',
    icon: CheckCircle,
  },
];

function ChatAssistantInner() {
  const searchParams = useSearchParams();
  const endRef = useRef<HTMLDivElement | null>(null);
  const projectIdParam = searchParams?.get('projectId') || searchParams?.get('project_id');
  const projectId = projectIdParam ? Number(projectIdParam) : null;

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Namaste! Main CodeGuard AI Assistant hoon. Main project ke scans, findings, auth/OAuth, uploads, reports, teams, schedules, aur FastAPI/Next.js debugging me help karta hoon. Guest mode me bhi pooch sakte ho.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed || loading) return;

    setError('');
    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const projectNameFromParams = searchParams?.get('projectName') || searchParams?.get('project_name') || undefined;

      const response = await chatService.sendMessage({
        message: trimmed,
        context: {
          page: '/chat',
          product: 'CodeGuard AI',
          project_id: projectId,
          project_name: projectNameFromParams,
          allowed_scope: assistantRules,
          timestamp: new Date().toISOString(),
        },
      });


      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.reply,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Assistant request failed';
      setError(message);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Chat request failed: ${message}. Check backend is running on http://localhost:8000 and try again.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    sendMessage(input);
  };

  const formatMessageTime = (timestamp: string) =>
    new Intl.DateTimeFormat('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(new Date(timestamp));

  return (
    <div className="mx-auto grid min-h-[calc(100vh-64px)] max-w-7xl gap-5 px-4 py-6 text-white sm:px-6 lg:grid-cols-[280px_1fr] lg:px-8">
      <aside className="h-fit rounded-3xl border border-white/10 bg-white/[0.04] p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-emerald-300/30 bg-emerald-300/10 text-emerald-100">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="font-bold">CodeGuard Chat</h1>
            <p className="text-xs text-slate-500">
              {projectId ? `Project-scoped assistant (ID: ${projectId})` : 'Project-scoped assistant'}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          {assistantRules.map((rule) => (
            <div key={rule} className="rounded-2xl border border-white/10 bg-slate-950/50 p-3 text-xs leading-5 text-slate-300">
              {rule}
            </div>
          ))}
        </div>
      </aside>

      <main className="flex min-h-[calc(100vh-112px)] flex-col">
        <header className="mb-4 rounded-3xl border border-white/10 bg-white/[0.04] p-5">
          <h2 className="text-2xl font-bold">Security Assistant</h2>
          <p className="mt-2 text-sm text-slate-400">
            Ask about scans, vulnerabilities, OAuth, reports, uploads, schedules, teams, or project errors.
          </p>
        </header>

        <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {quickPrompts.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                onClick={() => sendMessage(item.prompt)}
                disabled={loading}
                className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-left text-sm text-slate-200 transition hover:border-cyan-300/30 hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Icon className="shrink-0 text-cyan-200" size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {error && (
          <div className="mb-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        )}

        <section className="flex-1 space-y-5 overflow-y-auto rounded-3xl border border-white/10 bg-white/[0.03] p-4 sm:p-5">
          {messages.map((msg, idx) => (
            <div key={`${msg.timestamp || 'initial'}-${idx}`} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[94%] sm:max-w-[82%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border ${
                    msg.role === 'user'
                      ? 'ml-3 border-cyan-300/30 bg-cyan-300/10 text-cyan-100'
                      : 'mr-3 border-emerald-300/30 bg-emerald-300/10 text-emerald-100'
                  }`}
                >
                  {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div
                  className={`rounded-2xl border p-4 text-sm leading-6 ${
                    msg.role === 'user'
                      ? 'border-cyan-300/30 bg-cyan-300/10 text-cyan-50'
                      : 'border-white/10 bg-slate-950/70 text-slate-200'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {msg.timestamp && (
                    <div className="mt-3 text-xs opacity-60">
                      {formatMessageTime(msg.timestamp)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="flex max-w-[82%]">
                <div className="mr-3 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-emerald-300/30 bg-emerald-300/10 text-emerald-100">
                  <Bot size={20} />
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-slate-200">
                  <div className="flex gap-1">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0.1s]" />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </section>

        <form onSubmit={handleSubmit} className="mt-4 rounded-3xl border border-white/10 bg-white/[0.04] p-3 sm:p-4">
          <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <textarea
              className="min-h-24 resize-none rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm leading-6 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
              placeholder="Paste a scan finding, backend error, endpoint, or CodeGuard workflow question..."
              value={input}
              onChange={(event) => setInput(event.target.value.slice(0, 1600))}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage(input);
                }
              }}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send size={18} />
              Send
            </button>
          </div>
          <div className="mt-2 text-right text-xs text-slate-500">{input.length}/1600</div>
        </form>
      </main>
    </div>
  );
}

export default function ChatAssistant() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
          <div className="h-12 w-12 animate-spin rounded-full border-2 border-cyan-400/20 border-t-cyan-300" />
        </div>
      }
    >
      <ChatAssistantInner />
    </Suspense>
  );
}
