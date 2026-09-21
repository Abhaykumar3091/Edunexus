import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  Sparkles,
  Send,
  Bot,
  User as UserIcon,
  ShieldCheck,
  RotateCcw,
  BookOpen,
  Database,
  ExternalLink,
  Info,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { chatService } from '@/services/chat';
import { ChatMessage, SourceCitation } from '@/types/student';

interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  data_sources?: string[];
  timestamp: string;
}

export const ChatPage: React.FC = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    "What is the minimum attendance requirement?",
    "Show my current attendance breakdown",
    "What is my pending fee balance?",
    "What are the library timings and rules?",
    "What are the hostel room change rules?",
    "How can I file a maintenance grievance?",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isLoading) return;

    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    // Format chat history for backend agent
    const historyPayload: ChatMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const response = await chatService.sendMessage(query, historyPayload);
      if (response.success && response.data) {
        const aiMsg: DisplayMessage = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: response.data.answer || (response.data as any).message || 'No response generated.',
          sources: response.data.sources,
          data_sources: response.data.data_sources,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else {
        const errorMsg: DisplayMessage = {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: response.error?.message || 'Sorry, I encountered an issue processing your request.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } catch (err: any) {
      const errorMsg: DisplayMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: err?.message || 'Unable to connect to UniAssist agent. Please ensure the backend server is running.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
    setInputQuery('');
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8.5rem)] flex flex-col">
      {/* Top Title Banner */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Ask UniAssist AI</h1>
            <p className="text-xs text-slate-500">Official University AI Agent • Grounded in Azure AI Search & Live SIS</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <Button size="sm" variant="outline" onClick={handleResetChat} className="text-xs gap-1 h-8">
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Clear Chat</span>
            </Button>
          )}
          <Badge variant="success" className="gap-1 text-xs py-1 px-2.5">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Zero-Hallucination Policy</span>
          </Badge>
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 px-1">
        {/* Assistant Initial Welcome Message */}
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-lg bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
            <Bot className="h-4 w-4" />
          </div>
          <div className="flex-1 max-w-2xl space-y-2">
            <div className="p-4 bg-white border border-slate-200 rounded-2xl rounded-tl-sm shadow-sm text-sm text-slate-800 leading-relaxed">
              <p className="font-semibold text-slate-900 mb-1">
                Hello {user?.full_name?.split(' ')[0] || 'Student'}, I am UniAssist AI 👋
              </p>
              <p className="text-slate-600">
                I am your personal university assistant. You can ask me about your university regulations, hostel guidelines, or grievance status and hostel regulations.
              </p>
            </div>
            {/* Suggested Starter Questions */}
            {messages.length === 0 && (
              <div className="pt-2">
                <p className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-1">
                  <Info className="h-3.5 w-3.5" /> Quick suggestions:
                </p>
                <div className="flex flex-wrap gap-2">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q)}
                      className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-teal-400 hover:bg-teal-50/70 text-slate-700 transition-all text-left shadow-2xs cursor-pointer"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Dynamic Messages */}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm mt-0.5 ${
                m.role === 'user' ? 'bg-slate-800 text-white' : 'bg-teal-600 text-white'
              }`}
            >
              {m.role === 'user' ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>

            <div className={`flex-1 max-w-2xl space-y-2 ${m.role === 'user' ? 'text-right' : ''}`}>
              <div
                className={`p-4 text-sm leading-relaxed inline-block text-left shadow-sm ${
                  m.role === 'user'
                    ? 'bg-teal-600 text-white rounded-2xl rounded-tr-sm'
                    : 'bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-sm'
                }`}
              >
                <div className="whitespace-pre-line">{m.content}</div>

                {/* Grounding / Citations */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                      <BookOpen className="h-3.5 w-3.5 text-teal-600" />
                      <span>Official Reference Citations:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {m.sources.map((src, sIdx) => (
                        <span
                          key={sIdx}
                          className="inline-flex items-center gap-1 text-[11px] bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-md"
                          title={`Relevance Score: ${Math.round(src.relevance_score * 100)}%`}
                        >
                          <BookOpen className="h-2.5 w-2.5" />
                          {(src as any).title || src.document_title}
                          {src.section ? ` • ${src.section}` : ''}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Live Database Data Sources */}
                {m.data_sources && m.data_sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
                    <Database className="h-3 w-3 text-emerald-600" />
                    <span className="text-[11px]">Database Tools:</span>
                    {m.data_sources.map((ds, dIdx) => (
                      <span
                        key={dIdx}
                        className="text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.2 rounded font-mono"
                      >
                        {ds}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="text-[10px] text-slate-400 px-1">{m.timestamp}</div>
            </div>
          </div>
        ))}

        {/* Thinking Indicator */}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-lg bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
              <Bot className="h-4 w-4" />
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-2xl rounded-tl-sm shadow-sm">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span>UniAssist is retrieving documents and querying your SIS data...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Bar */}
      <div className="pt-3 border-t border-slate-200 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-2 shadow-sm focus-within:border-teal-500 focus-within:ring-2 focus-within:ring-teal-100 transition-all"
        >
          <input
            type="text"
            placeholder="Ask UniAssist anything about university policies, hostel regulations, or grievances..."
            value={inputQuery}
            disabled={isLoading}
            onChange={(e) => setInputQuery(e.target.value)}
            className="flex-1 px-3 py-2 text-sm bg-transparent border-none focus:outline-none text-slate-900 placeholder:text-slate-400 disabled:opacity-50"
          />
          <Button type="submit" size="sm" disabled={isLoading || !inputQuery.trim()} className="gap-1.5 shrink-0">
            <span>Send</span>
            <Send className="h-3.5 w-3.5" />
          </Button>
        </form>
        <p className="text-[11px] text-slate-400 text-center mt-1.5">
          UniAssist verifies answers against official university regulations and provides verifiable source citations.
        </p>
      </div>
    </div>
  );
};
