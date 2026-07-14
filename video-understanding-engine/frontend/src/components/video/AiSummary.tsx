export function AiSummary({ summary, topics }: { summary: string, topics: string[] }) {
  return (
    <div className="p-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 overflow-y-auto h-full custom-scrollbar">
      <div>
        <h3 className="font-semibold text-primary mb-3 uppercase text-[11px] tracking-widest">Key Topics</h3>
        <div className="flex flex-wrap gap-2">
          {topics.map(t => (
            <span key={t} className="px-2.5 py-1.5 bg-primary/10 text-primary border border-primary/20 rounded-lg text-xs font-semibold">{t}</span>
          ))}
        </div>
      </div>
      <div>
        <h3 className="font-semibold text-primary mb-3 uppercase text-[11px] tracking-widest">Summary</h3>
        <p className="text-foreground/80 text-[15px] leading-relaxed whitespace-pre-wrap">{summary}</p>
      </div>
    </div>
  );
}
