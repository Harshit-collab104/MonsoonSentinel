import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowUp, Sparkles, Wrench, Bot, User } from 'lucide-react';

export default function AgentChatConsole({ selectedIncident, onSendMessage, chatLog, loadingChat }) {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loadingChat) return;
    onSendMessage(inputMessage.trim());
    setInputMessage('');
  };

  const handleQuickPrompt = (promptText) => {
    onSendMessage(promptText);
  };

  return (
    <div className="bg-[#09090B] flex flex-col h-full overflow-hidden select-text">
      {/* Sub-header Context Bar */}
      <div className="h-10 px-6 border-b border-[#27272A] flex items-center justify-between text-xs text-[#71717A] shrink-0 bg-[#09090B]">
        <div className="flex items-center gap-2">
          <span className="font-medium text-[#FAFAFA]">Operations Dispatcher</span>
          <span>•</span>
          <span className="text-[#A1A1AA]">
            {selectedIncident
              ? `${selectedIncident.id} (${selectedIncident.report.ward_name})`
              : 'Municipal Operations Corridor'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#10B981]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block" />
          <span className="text-[#A1A1AA]">Active</span>
        </div>
      </div>

      {/* Message Stream with generous padding */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {chatLog.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 text-sm leading-relaxed ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role !== 'user' && (
                <div className="w-7 h-7 rounded-md bg-[#18181B] border border-[#27272A] flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-[#A1A1AA]" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-[#18181B] text-[#FAFAFA] border border-[#27272A] px-4 py-3'
                    : 'text-[#E4E4E7] space-y-3'
                }`}
              >
                {/* Structured Metadata Badges if present */}
                {(msg.incident_status || msg.risk_score !== undefined || msg.severity) && (
                  <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono">
                    {msg.incident_status && (
                      <span className="px-2 py-0.5 rounded bg-[#27272A] text-zinc-200 border border-[#3F3F46]">
                        STATUS: {msg.incident_status}
                      </span>
                    )}
                    {msg.risk_score !== undefined && msg.risk_score !== null && (
                      <span className="px-2 py-0.5 rounded bg-[#27272A] text-zinc-200 border border-[#3F3F46]">
                        RISK: {msg.risk_score}/100
                      </span>
                    )}
                    {msg.severity && (
                      <span
                        className={`px-2 py-0.5 rounded border ${
                          msg.severity === 'CRITICAL'
                            ? 'bg-rose-950/60 text-rose-400 border-rose-800/60'
                            : msg.severity === 'HIGH'
                            ? 'bg-amber-950/60 text-amber-400 border-amber-800/60'
                            : 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                        }`}
                      >
                        {msg.severity}
                      </span>
                    )}
                  </div>
                )}

                {/* Reasoning Summary if provided */}
                {msg.reasoning_summary && (
                  <div className="bg-[#18181B] border border-[#27272A] rounded-md p-2.5 text-xs text-[#A1A1AA] flex items-start gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-[#10B981] shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{msg.reasoning_summary}</span>
                  </div>
                )}

                {/* Clean Markdown text */}
                <div className="terminal-markdown text-[13px] text-[#FAFAFA] leading-relaxed">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {/* Structured Actions Taken & Next Steps */}
                {msg.actions_taken?.length > 0 && (
                  <div className="bg-[#121214] border border-[#27272A] rounded-md p-2.5 text-xs space-y-1">
                    <div className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                      Authoritative Actions Completed:
                    </div>
                    {msg.actions_taken.map((act, ai) => (
                      <div key={ai} className="text-[#A1A1AA] flex items-center gap-1.5 pl-1">
                        <span className="text-[#10B981]">✓</span>
                        <span>{act}</span>
                      </div>
                    ))}
                  </div>
                )}

                {msg.next_steps?.length > 0 && (
                  <div className="bg-[#121214] border border-[#27272A] rounded-md p-2.5 text-xs space-y-1">
                    <div className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                      Operational Next Steps:
                    </div>
                    {msg.next_steps.map((step, si) => (
                      <div key={si} className="text-[#A1A1AA] flex items-center gap-1.5 pl-1">
                        <span className="text-[#F59E0B]">→</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-md bg-[#27272A] flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}

          {loadingChat && (
            <div className="flex items-center gap-2.5 text-xs text-[#A1A1AA] py-2">
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
              <span>Analyzing telemetry and formulating response plan...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Bottom Area: Clean Quick Prompts & Minimal Input Container */}
      <div className="p-4 border-t border-[#27272A] bg-[#09090B]">
        <div className="max-w-3xl mx-auto space-y-2.5">
          {/* Subtle suggestions pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs text-[#71717A]">
            <span className="text-[11px] font-medium text-[#52525B] uppercase tracking-wider mr-1">
              Suggestions:
            </span>
            <button
              onClick={() => handleQuickPrompt(`Assess waterlogging risk for ${selectedIncident ? selectedIncident.id : 'the primary hotspot'}`)}
              className="px-2.5 py-1 rounded bg-[#18181B] hover:bg-[#27272A] text-[#A1A1AA] hover:text-[#FAFAFA] border border-[#27272A] whitespace-nowrap transition cursor-pointer text-xs"
            >
              Assess Risk
            </button>
            <button
              onClick={() => handleQuickPrompt(`Recommend response equipment for ${selectedIncident ? selectedIncident.id : 'active incidents'}`)}
              className="px-2.5 py-1 rounded bg-[#18181B] hover:bg-[#27272A] text-[#A1A1AA] hover:text-[#FAFAFA] border border-[#27272A] whitespace-nowrap transition cursor-pointer text-xs"
            >
              Recommend Equipment
            </button>
            <button
              onClick={() => handleQuickPrompt(`Check operational status for ${selectedIncident ? selectedIncident.id : 'the primary hotspot'}`)}
              className="px-2.5 py-1 rounded bg-[#18181B] hover:bg-[#27272A] text-[#A1A1AA] hover:text-[#FAFAFA] border border-[#27272A] whitespace-nowrap transition cursor-pointer text-xs"
            >
              Check Status
            </button>
          </div>

          {/* Minimal Input Bar */}
          <form onSubmit={handleSubmit} className="relative flex items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Query dispatcher or enter operational command..."
              className="w-full bg-[#18181B] border border-[#27272A] rounded-md px-3.5 py-2.5 pr-10 text-sm text-[#FAFAFA] placeholder-[#71717A] outline-none focus:border-[#3F3F46] transition"
            />
            <button
              type="submit"
              disabled={loadingChat || !inputMessage.trim()}
              className="absolute right-2 p-1.5 bg-[#27272A] hover:bg-[#3F3F46] disabled:opacity-30 text-white rounded transition cursor-pointer flex items-center justify-center"
            >
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}


