"use client";
import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { fetchApi } from "@/services/api";
import { useAuth } from "@/providers/AuthProvider";
import Link from "next/link";
import { AiSummary } from "@/components/video/AiSummary";
import { InteractiveTimeline } from "@/components/video/InteractiveTimeline";
import { FlashcardsViewer } from "@/components/video/FlashcardsViewer";
import { QuizInteractive } from "@/components/video/QuizInteractive";
import { AiChat } from "@/components/video/AiChat";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function VideoPage() {
  const { id } = useParams();
  const { user } = useAuth();
  
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [videoMeta, setVideoMeta] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "summary" | "flashcards" | "quiz" | "chat">("timeline");
  
  const [summary, setSummary] = useState<any>(null);
  const [chapters, setChapters] = useState<any[]>([]);
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [quiz, setQuiz] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Chat state lifted here so it persists across tab switches
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi! Ask me anything about this video. I can find exact timestamps and answer complex questions." }
  ]);
  const [chatInput, setChatInput] = useState("");

  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const videoRef = useRef<HTMLVideoElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id || !user) return;

    const loadData = async () => {
      try {
        const [metaRes, urlRes, chaptersRes, summaryRes, cardsRes, quizRes] = await Promise.allSettled([
          fetchApi(`/video/${id}`),
          fetchApi(`/video/${id}/url`),
          fetchApi(`/ai/${id}/chapters`),
          fetchApi(`/ai/${id}/summary`),
          fetchApi(`/ai/${id}/flashcards`),
          fetchApi(`/ai/${id}/quiz`),
        ]);

        if (metaRes.status === "fulfilled") setVideoMeta(metaRes.value);
        if (urlRes.status === "fulfilled") setVideoUrl(urlRes.value.url);
        if (chaptersRes.status === "fulfilled") setChapters(chaptersRes.value);
        if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
        if (cardsRes.status === "fulfilled") setFlashcards(cardsRes.value);
        if (quizRes.status === "fulfilled") setQuiz(quizRes.value);

      } catch (err) {
        console.error("Error loading video data", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, user]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => setCurrentTime(video.currentTime);
    const handleDurationChange = () => setDuration(video.duration);

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("durationchange", handleDurationChange);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("durationchange", handleDurationChange);
    };
  }, [videoUrl]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is currently typing in an input/textarea
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA" || activeEl.getAttribute("contenteditable") === "true")) {
        return;
      }

      if (!videoRef.current) return;

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - 5);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        videoRef.current.currentTime = Math.min(videoRef.current.duration || 0, videoRef.current.currentTime + 5);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (videoUrl && videoRef.current) {
      const params = new URLSearchParams(window.location.search);
      const t = params.get('t');
      if (t) {
        const handleMeta = () => {
          if (videoRef.current) {
            videoRef.current.currentTime = parseFloat(t);
            videoRef.current.play().catch(() => {});
          }
        };
        videoRef.current.addEventListener('loadedmetadata', handleMeta);
        return () => videoRef.current?.removeEventListener('loadedmetadata', handleMeta);
      }
    }
  }, [videoUrl]);

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current || !videoRef.current || !duration) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, clickX / rect.width));
    const seekTime = percentage * duration;
    handleSeek(seekTime);
  };

  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background">
      <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4"></div>
      <div className="text-primary font-bold animate-pulse tracking-widest uppercase text-sm">Loading AI Knowledge...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <nav className="border-b border-border bg-card/60 backdrop-blur-xl h-16 flex items-center px-6 sticky top-0 z-50">
        <Link href="/" className="text-muted-foreground hover:text-primary transition-colors font-medium flex items-center gap-2 group">
           <span className="group-hover:-translate-x-1 transition-transform">←</span> Library
        </Link>
        <div className="mx-auto font-bold text-foreground truncate max-w-md text-center">{videoMeta?.title || "Video"}</div>
        <div className="w-24"></div> {/* spacer for centering */}
      </nav>

      <div className="flex-1 max-w-[1400px] mx-auto w-full p-4 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Video Player */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="bg-black rounded-3xl overflow-hidden aspect-video border border-border/50 shadow-2xl relative group">
            {videoUrl ? (
              <video 
                ref={videoRef}
                src={videoUrl} 
                controls 
                className="w-full h-full object-contain"
                crossOrigin="anonymous"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-muted-foreground font-medium">Video URL not found</div>
            )}
          </div>

          {/* Chapter Timeline Map & Custom Seek Bar */}
          {videoUrl && chapters.length > 0 && (
            <div className="bg-card/30 p-5 rounded-3xl border border-border/50 flex flex-col gap-3">
              <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest">Chapters Navigation Map</div>
              <div 
                ref={progressBarRef}
                className="relative h-2.5 bg-secondary hover:h-3.5 rounded-full cursor-pointer transition-all flex items-center group/bar"
                onClick={handleProgressBarClick}
              >
                {/* Progress fill */}
                <div 
                  className="h-full bg-primary rounded-full absolute left-0 top-0 transition-all duration-75"
                  style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
                />
                
                {/* Chapter Ticks */}
                {chapters.map((ch, index) => {
                  const startPercent = duration ? (ch.start_time / duration) * 100 : 0;
                  const isActive = currentTime >= ch.start_time && currentTime < ch.end_time;
                  return (
                    <div 
                      key={index}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSeek(ch.start_time);
                      }}
                      className={`absolute h-full w-0.5 border-r border-background hover:w-1.5 transition-all cursor-pointer ${isActive ? "bg-primary" : "bg-white/40 hover:bg-primary"}`}
                      style={{ left: `${startPercent}%` }}
                      title={`${ch.title} (${Math.floor(ch.start_time / 60)}:${Math.floor(ch.start_time % 60).toString().padStart(2, '0')})`}
                    />
                  );
                })}
              </div>
              
              {/* Active Chapter indicator */}
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span className="font-semibold text-foreground truncate max-w-[70%]">
                  Current Chapter: <span className="text-primary font-bold">{chapters.find(ch => currentTime >= ch.start_time && currentTime < ch.end_time)?.title || "None"}</span>
                </span>
                <span className="font-mono">
                  {Math.floor(currentTime / 60)}:{(Math.floor(currentTime % 60)).toString().padStart(2, '0')} / {Math.floor(duration / 60)}:{(Math.floor(duration % 60)).toString().padStart(2, '0')}
                </span>
              </div>
            </div>
          )}

          <div className="bg-card/50 p-6 rounded-3xl border border-border/50">
            <h2 className="text-2xl font-bold mb-2 text-foreground">{videoMeta?.title}</h2>
            <div className="text-sm font-medium text-muted-foreground flex gap-3 items-center">
              <span>{new Date(videoMeta?.created_at).toLocaleDateString()}</span>
              <span>•</span>
              <span className="uppercase tracking-wider text-[11px] font-bold px-2.5 py-1 bg-secondary rounded-md">{videoMeta?.status}</span>
            </div>
          </div>
        </div>

        {/* Right Column: AI Knowledge Panel */}
        <div className="bg-card rounded-3xl border border-border/50 flex flex-col h-[calc(100vh-140px)] sticky top-[100px] overflow-hidden shadow-2xl">
          {/* Tabs */}
          <div className="grid grid-cols-5 border-b border-border/50 bg-card/80 backdrop-blur-md shrink-0">
            {["timeline", "summary", "flashcards", "quiz", "chat"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`py-4 text-center text-[10px] sm:text-xs font-bold uppercase tracking-wider transition-all border-b-2 ${
                  activeTab === tab 
                    ? "border-primary text-primary bg-primary/5" 
                    : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab Content — always mount AiChat so it never loses state */}
          <div className="flex-1 overflow-hidden relative">
            <div className={`${activeTab === "timeline" ? "" : "hidden"} h-full overflow-hidden`}>
              <InteractiveTimeline chapters={chapters} onSeek={handleSeek} />
            </div>
            <div className={`${activeTab === "summary" ? "" : "hidden"} h-full overflow-hidden`}>
              {summary
                ? <AiSummary summary={summary.summary} topics={summary.key_topics} />
                : <div className="p-10 text-muted-foreground font-medium text-center">No summary available.</div>
              }
            </div>
            <div className={`${activeTab === "flashcards" ? "" : "hidden"} h-full overflow-hidden`}>
              <FlashcardsViewer flashcards={flashcards} />
            </div>
            <div className={`${activeTab === "quiz" ? "" : "hidden"} h-full overflow-hidden`}>
              <QuizInteractive questions={quiz} />
            </div>
            <div className={`${activeTab === "chat" ? "" : "hidden"} h-full overflow-hidden`}>
              <AiChat
                videoId={id as string}
                messages={chatMessages}
                setMessages={setChatMessages}
                input={chatInput}
                setInput={setChatInput}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
