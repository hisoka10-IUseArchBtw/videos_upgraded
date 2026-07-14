import { useRef, useEffect } from "react";
import { fetchApi } from "@/services/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface AiChatProps {
  videoId: string;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
}

export function AiChat({ videoId, messages, setMessages, input, setInput }: AiChatProps) {
  const loadingRef = useRef(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isLoading = messages.at(-1)?.role === "user";

  const handleSend = async () => {
    if (!input.trim() || loadingRef.current) return;
    
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    loadingRef.current = true;

    try {
      const data = await fetchApi(`/chat/${videoId}`, {
        method: "POST",
        body: JSON.stringify({ question: userMsg })
      });
      
      setMessages(prev => [...prev, { role: "assistant", content: data.answer }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error answering that." }]);
    } finally {
      loadingRef.current = false;
    }
  };

  return (
    <div className="flex flex-col h-full bg-card/20">
      <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar pb-24">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-xs font-bold mr-3 shrink-0 mt-1 shadow-sm">AI</div>
            )}
            <div className={`max-w-[80%] p-4 rounded-2xl text-[14px] leading-relaxed shadow-sm ${
              msg.role === "user" 
                ? "bg-primary text-primary-foreground rounded-tr-sm" 
                : "bg-secondary/80 text-foreground rounded-tl-sm border border-border/50 whitespace-pre-wrap"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-xs font-bold mr-3 shrink-0 mt-1 shadow-sm opacity-70 animate-pulse">AI</div>
            <div className="max-w-[80%] p-4 rounded-2xl bg-secondary/80 text-secondary-foreground rounded-tl-sm border border-border/50 flex items-center gap-1.5 h-[52px]">
              <div className="w-2 h-2 rounded-full bg-primary/60 animate-bounce"></div>
              <div className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '0.2s'}}></div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      
      <div className="p-4 border-t border-border/50 bg-card/80 backdrop-blur-md absolute bottom-0 w-full">
        <div className="relative flex items-center">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask a question about this video..."
            className="w-full bg-input border border-border/60 rounded-xl pl-4 pr-14 py-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-muted-foreground shadow-inner"
          />
          <button 
            onClick={handleSend}
            disabled={!input.trim()}
            className="absolute right-2 p-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50 hover:opacity-90 transition-all shadow-md"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
