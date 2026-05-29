'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Send, Bot, User } from 'lucide-react';
import { chatService, ChatMessage } from '@/lib/chat-service';
import { authService } from '@/lib/auth-service';

export default function ChatAssistant() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { 
      role: 'assistant', 
      content: 'Hello! I am CodeGuard AI Assistant. Ask me about this project, scan findings, vulnerabilities, auth, uploads, reports, teams, or backend/frontend debugging.',
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check authentication
    if (!authService.isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);
    
    try {
      const response = await chatService.sendMessage({
        message: currentInput,
        context: {
          timestamp: new Date().toISOString(),
          session: 'web-chat'
        }
      });
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: unknown) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${error instanceof Error ? error.message : 'Please try again later.'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-64px)] max-w-5xl flex-col px-4 py-6 text-white sm:px-6 lg:px-8">
      <header className="mb-5 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
        <h1 className="text-3xl font-bold text-white">
          CodeGuard AI Assistant
        </h1>
        <p className="mt-2 text-slate-400">Project-only help for CodeGuard AI security analysis, scans, fixes, and debugging</p>
      </header>

      <div className="flex-1 space-y-6 overflow-y-auto rounded-3xl border border-white/10 bg-white/[0.03] p-4 sm:p-5">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[92%] sm:max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl border ${msg.role === 'user' ? 'ml-3 border-cyan-300/30 bg-cyan-300/10 text-cyan-100 sm:ml-4' : 'mr-3 border-emerald-300/30 bg-emerald-300/10 text-emerald-100 sm:mr-4'}`}>
                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className={`rounded-2xl border p-4 ${msg.role === 'user' ? 'border-cyan-300/30 bg-cyan-300/10 text-cyan-50' : 'border-white/10 bg-slate-950/70 text-slate-200'}`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.timestamp && (
                  <div className="text-xs opacity-70 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="flex max-w-[80%]">
              <div className="mr-4 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl border border-emerald-300/30 bg-emerald-300/10 text-emerald-100">
                <Bot size={20} />
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-slate-200">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-5 rounded-3xl border border-white/10 bg-white/[0.04] p-3 sm:p-4">
        <div className="relative">
          <input
            type="text"
            className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-5 py-4 pr-16 outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
            placeholder="Ask about CodeGuard scans, fixes, auth, uploads, reports..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={loading}
          />
          <button 
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="absolute right-2 top-2 rounded-xl border border-cyan-300/30 bg-cyan-300/10 p-2 text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send size={20} />
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
