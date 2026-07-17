"use client";
import { useState, useEffect, useRef } from "react";
import { fetchApi } from "@/services/api";
import { useRouter } from "next/navigation";

interface SearchResult {
  video_id: string;
  start_time: number;
  chunk_type: string;
  text: string;
  metadata?: { chapter_title?: string };
}

export function GlobalSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length > 2) {
        setLoading(true);
        setOpen(true);
        try {
          const res = await fetchApi("/search", {
            method: "POST",
            body: JSON.stringify({ query, limit: 10 })
          });
          setResults(res.results || []);
        } catch (e) {
          console.error(e);
        } finally {
          setLoading(false);
        }
      } else {
        setResults([]);
        setOpen(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  return (
    <div className="relative w-full max-w-xl mx-auto" ref={ref}>
      <div className="relative group">
        <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Semantic search across all videos (e.g., 'When did they discuss gradient descent?')"
          className="w-full bg-input/40 border border-border/80 rounded-2xl pl-11 pr-10 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all placeholder:text-muted-foreground shadow-inner"
        />
        {loading && <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>}
      </div>

      {open && query.length > 2 && (
        <div className="absolute top-[calc(100%+8px)] w-full bg-card/95 backdrop-blur-xl border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-50">
          {results.length === 0 && !loading ? (
            <div className="p-6 text-center text-sm font-medium text-muted-foreground">No results found for &ldquo;{query}&rdquo;</div>
          ) : (
            <div className="max-h-[60vh] overflow-y-auto custom-scrollbar">
              <div className="px-4 py-3 bg-secondary/30 border-b border-border/50">
                <span className="text-[10px] font-bold uppercase tracking-widest text-primary">Top Matches</span>
              </div>
              {results.map((r, i) => (
                <div 
                  key={i} 
                  onClick={() => {
                    setOpen(false);
                    router.push(`/video/${r.video_id}?t=${r.start_time}`);
                  }}
                  className="p-5 border-b border-border/50 hover:bg-primary/5 hover:border-primary/20 cursor-pointer transition-all group"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-bold text-primary uppercase tracking-widest bg-primary/10 px-2 py-0.5 rounded-sm">{r.chunk_type}</span>
                    <span className="text-[11px] font-mono font-bold bg-secondary text-secondary-foreground px-2 py-1 rounded-md shrink-0 shadow-sm">
                      {Math.floor(r.start_time/60)}:{(Math.floor(r.start_time)%60).toString().padStart(2,'0')}
                    </span>
                  </div>
                  <p className="text-[14px] line-clamp-3 text-foreground/90 font-medium group-hover:text-foreground transition-colors leading-relaxed">{r.text}</p>
                  {r.metadata?.chapter_title && <div className="text-[11px] text-muted-foreground font-semibold mt-2.5 flex items-center gap-1.5"><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> {r.metadata.chapter_title}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
