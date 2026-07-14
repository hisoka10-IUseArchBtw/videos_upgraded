export function InteractiveTimeline({ chapters, onSeek }: { chapters: any[], onSeek: (time: number) => void }) {
  if (!chapters.length) return <div className="p-6 text-muted-foreground text-center mt-10">No chapters found for this video.</div>;
  
  return (
    <div className="p-4 space-y-3 h-full overflow-y-auto custom-scrollbar animate-in fade-in slide-in-from-bottom-4 duration-500">
      {chapters.map((ch, idx) => {
        const m = Math.floor(ch.start_time / 60);
        const s = Math.floor(ch.start_time % 60).toString().padStart(2, '0');
        return (
          <div 
            key={idx} 
            onClick={() => onSeek(ch.start_time)}
            className="group p-4 rounded-2xl border border-border bg-card/50 hover:bg-card hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 cursor-pointer transition-all duration-300"
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-bold text-sm leading-snug group-hover:text-primary transition-colors pr-2">{ch.title}</h4>
              <span className="text-xs font-mono font-bold bg-primary/10 text-primary px-2 py-1 rounded-md shrink-0">{m}:{s}</span>
            </div>
            {ch.summary && <p className="text-[13px] text-muted-foreground line-clamp-2 leading-relaxed">{ch.summary}</p>}
          </div>
        );
      })}
    </div>
  );
}
