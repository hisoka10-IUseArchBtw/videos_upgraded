import { useState } from "react";

interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: string;
}

export function QuizInteractive({ questions }: { questions: QuizQuestion[] }) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  if (!questions.length) return <div className="p-6 text-muted-foreground text-center mt-10">No quiz generated.</div>;

  let score = 0;
  if (submitted) {
    questions.forEach((q, i) => {
      if (answers[i] === q.correct_answer) score++;
    });
  }

  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full custom-scrollbar animate-in fade-in duration-500 pb-20">
      {submitted && (
        <div className="p-6 bg-gradient-to-r from-primary/10 to-purple-600/10 border border-primary/20 rounded-2xl text-center shadow-inner">
          <h2 className="text-3xl font-bold text-primary mb-2">Score: {score} / {questions.length}</h2>
          <p className="text-sm font-medium text-foreground/80">{score === questions.length ? "Perfect score! Outstanding." : "Great effort! Keep practicing."}</p>
        </div>
      )}

      {questions.map((q, qIdx) => (
        <div key={qIdx} className="space-y-4 bg-card/50 p-6 rounded-2xl border border-border">
          <h3 className="font-bold text-[15px] leading-snug">{qIdx + 1}. {q.question}</h3>
          <div className="space-y-2.5">
            {q.options.map((opt: string) => {
              const isSelected = answers[qIdx] === opt;
              const isCorrect = opt === q.correct_answer;
              let btnClass = "w-full text-left p-4 rounded-xl border text-[14px] transition-all duration-300 ";
              
              if (!submitted) {
                btnClass += isSelected 
                  ? "border-primary bg-primary/10 text-primary font-bold shadow-sm" 
                  : "border-border/60 hover:border-primary/50 hover:bg-secondary/50 font-medium text-muted-foreground hover:text-foreground";
              } else {
                if (isCorrect) btnClass += "border-emerald-500 bg-emerald-500/10 text-emerald-500 font-bold";
                else if (isSelected && !isCorrect) btnClass += "border-destructive bg-destructive/10 text-destructive font-bold";
                else btnClass += "border-border/30 opacity-40 font-medium text-muted-foreground";
              }

              return (
                <button 
                  key={opt}
                  disabled={submitted}
                  onClick={() => setAnswers(prev => ({...prev, [qIdx]: opt}))}
                  className={btnClass}
                >
                  {opt}
                </button>
              )
            })}
          </div>
        </div>
      ))}
      
      {!submitted && Object.keys(answers).length === questions.length && (
        <button onClick={() => setSubmitted(true)} className="w-full py-4 bg-primary text-primary-foreground font-bold rounded-xl shadow-lg shadow-primary/25 hover:opacity-90 transition-all text-lg">
          Submit Answers
        </button>
      )}
    </div>
  );
}
