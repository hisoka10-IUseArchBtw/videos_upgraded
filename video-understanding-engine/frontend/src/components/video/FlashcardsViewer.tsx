import { useState } from "react";

export function FlashcardsViewer({ flashcards }: { flashcards: any[] }) {
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (!flashcards.length) return <div className="p-6 text-muted-foreground text-center mt-10">No flashcards generated.</div>;

  const card = flashcards[idx];

  const next = () => {
    setFlipped(false);
    setTimeout(() => setIdx(i => (i + 1) % flashcards.length), 150);
  };
  
  const prev = () => {
    setFlipped(false);
    setTimeout(() => setIdx(i => (i - 1 + flashcards.length) % flashcards.length), 150);
  };

  return (
    <div className="p-6 flex flex-col items-center justify-between h-full animate-in fade-in duration-500 overflow-y-auto custom-scrollbar">
      <div className="text-sm text-muted-foreground font-bold tracking-widest uppercase shrink-0">Card {idx + 1} of {flashcards.length}</div>
      
      <div 
        onClick={() => setFlipped(!flipped)}
        className="w-full max-w-md flex-1 min-h-[220px] max-h-[320px] perspective-1000 cursor-pointer group my-6 shrink-0"
      >
        <div className={`relative w-full h-full transition-transform duration-700 transform-style-3d ${flipped ? 'rotate-y-180' : ''}`}>
          {/* Front */}
          <div className="absolute inset-0 backface-hidden bg-card border border-border rounded-3xl p-6 flex flex-col justify-center items-center text-center shadow-lg group-hover:border-primary/50 group-hover:shadow-primary/10 transition-all overflow-y-auto custom-scrollbar">
            <span className="text-[10px] font-bold text-primary uppercase tracking-widest absolute top-4">Question</span>
            <h3 className="text-lg md:text-xl font-medium leading-snug pt-4">{card.question}</h3>
          </div>
          {/* Back */}
          <div className="absolute inset-0 backface-hidden bg-gradient-to-br from-primary to-purple-600 text-white border border-primary/20 rounded-3xl p-6 flex flex-col justify-center items-center text-center shadow-xl rotate-y-180 overflow-y-auto custom-scrollbar">
             <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest absolute top-4">Answer</span>
             <p className="text-lg md:text-xl font-bold leading-snug pt-4">{card.answer}</p>
          </div>
        </div>
      </div>

      <div className="flex gap-4 w-full max-w-md shrink-0">
        <button onClick={prev} className="flex-1 py-3 rounded-xl font-semibold border border-border bg-card hover:bg-secondary transition-colors text-sm">Previous</button>
        <button onClick={next} className="flex-1 py-3 rounded-xl font-semibold bg-primary text-primary-foreground shadow-lg hover:shadow-primary/25 hover:opacity-90 transition-all text-sm">Next Card</button>
      </div>
    </div>
  );
}
