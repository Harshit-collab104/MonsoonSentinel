import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Cpu, Sparkles, Terminal, Wrench, Shield } from 'lucide-react';

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
    <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[520px] shadow-xl overflow-hidden">
      {/* Console Header */}
      <div className="p-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-600/20 text-purple-400 border border-purple-500/30">
            <Bot className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
              <span>Strands Agent Console</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                Mock SageMaker
              </span>
            </h3>
            <p className="text-[10px] text-slate-400">
              {selectedIncident ? `Context: ${selectedIncident.id} (${selectedIncident.report.ward_name})` : 'Context: General Municipal Flood Operations'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <Terminal className="w-3.5 h-3.5 text-slate-500" />
          <span>Local Strands SDK</span>
        </div>
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3.5 text-xs">
        {chatLog.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-1.5 mb-1 text-[10px] text-slate-400">
              {msg.role === 'user' ? (
                <>
                  <span>You</span>
                  <User className="w-3 h-3 text-blue-400" />
                </>
              ) : (
                <>
                  <Bot className="w-3 h-3 text-purple-400" />
                  <span>Monsoon Sentinel Agent</span>
                </>
              )}
            </div>

            <div
              className={`p-3 rounded-xl max-w-[90%] leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-slate-950/90 border border-slate-800 text-slate-200 rounded-bl-none shadow'
              }`}
            >
              {/* Agent Thought Process / Tool Traces if present */}
              {msg.thought_process?.length > 0 && (
                <div className="mb-2 pb-2 border-b border-slate-800 text-[11px] text-purple-300 font-mono space-y-0.5">
                  <div className="font-bold flex items-center gap-1 text-purple-400">
                    <Sparkles className="w-3 h-3" />
                    <span>Model Reasoning Trace:</span>
                  </div>
                  {msg.thought_process.map((t, ti) => (
                    <div key={ti} className="opacity-90">{t}</div>
                  ))}
                </div>
              )}

              {msg.tool_traces?.length > 0 && (
                <div className="mb-2 pb-2 border-b border-slate-800 text-[11px] text-cyan-300 font-mono space-y-1">
                  <div className="font-bold flex items-center gap-1 text-cyan-400">
                    <Wrench className="w-3 h-3" />
                    <span>Strands Tools Executed:</span>
                  </div>
                  {msg.tool_traces.map((trace, ti) => (
                    <div key={ti} className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                      <span className="font-bold text-white">⚙ {trace.tool}</span>
                    </div>
                  ))}
                </div>
              )}

              <div>{msg.content}</div>
            </div>
          </div>
        ))}

        {loadingChat && (
          <div className="flex items-center gap-2 text-slate-400 text-xs italic">
            <Bot className="w-4 h-4 text-purple-400 animate-spin" />
            <span>Agent consulting deterministic risk engine & tools...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts */}
      <div className="px-3 py-2 bg-slate-950/60 border-t border-slate-800/80 flex items-center gap-1.5 overflow-x-auto text-[11px]">
        <span className="text-slate-500 shrink-0">Quick prompts:</span>
        <button
          onClick={() => handleQuickPrompt(`Assess waterlogging risk for ${selectedIncident ? selectedIncident.id : 'the primary hotspot'}`)}
          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 whitespace-nowrap cursor-pointer"
        >
          Assess Risk
        </button>
        <button
          onClick={() => handleQuickPrompt(`Recommend response equipment for ${selectedIncident ? selectedIncident.id : 'active incidents'}`)}
          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 whitespace-nowrap cursor-pointer"
        >
          Recommend Action
        </button>
        <button
          onClick={() => handleQuickPrompt('List all 12 available Strands Agent tools')}
          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 whitespace-nowrap cursor-pointer"
        >
          Show Tools
        </button>
      </div>

      {/* Message Input Box */}
      <form onSubmit={handleSubmit} className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask Strands agent about risk, triage, or response actions..."
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          disabled={loadingChat || !inputMessage.trim()}
          className="p-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white transition disabled:opacity-50 cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
