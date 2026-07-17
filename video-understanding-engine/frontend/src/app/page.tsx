"use client";
import { useEffect, useState, useRef } from "react";
import { fetchApi } from "@/services/api";
import { useAuth } from "@/providers/AuthProvider";
import Link from "next/link";
import { GlobalSearch } from "@/components/GlobalSearch";

interface Video {
  id: string;
  title: string;
  status: string;
  duration?: number;
  thumbnail_url?: string | null;
  created_at: string;
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const loadVideos = async () => {
    try {
      const data = await fetchApi("/video/list");
      setVideos(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVideos();
    // Poll for status updates every 5 seconds
    const interval = setInterval(loadVideos, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      await fetchApi("/video/upload", {
        method: "POST",
        body: formData,
        // The API service does not set Content-Type if body is FormData
      });
      await loadVideos();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Upload failed. Ensure it is a valid video file.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteConfirm = async (videoId: string) => {
    setConfirmId(null);
    setDeletingId(videoId);
    try {
      await fetchApi(`/video/${videoId}`, { method: "DELETE" });
      setVideos(prev => prev.filter(v => v.id !== videoId));
    } catch (err) {
      console.error("Delete failed", err);
      alert("Failed to delete video. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case "COMPLETED": return <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">Ready</span>;
      case "PROCESSING": return <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20 animate-pulse">Processing</span>;
      case "FAILED": return <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-red-500/10 text-red-500 border border-red-500/20">Failed</span>;
      default: return <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">Pending</span>;
    }
  };

  if (!user) return null; // Wait for AuthProvider to redirect

  return (
    <div className="min-h-screen bg-background">
      {/* Confirmation Modal */}
      {confirmId && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setConfirmId(null)}
        >
          <div
            className="bg-card border border-border rounded-2xl p-8 max-w-sm w-full mx-4 shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-center mb-2">Delete Video?</h3>
            <p className="text-sm text-muted-foreground text-center mb-6">
              This will permanently delete the video, its AI analysis, and all associated data. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmId(null)}
                className="flex-1 py-2.5 rounded-xl border border-border text-sm font-semibold hover:bg-secondary/50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteConfirm(confirmId)}
                className="flex-1 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-semibold transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navbar */}
      <nav className="border-b border-border bg-card/60 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 h-20 flex items-center justify-between gap-8">
          <div className="font-bold text-xl text-foreground tracking-tight flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white shadow-lg shadow-primary/20">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            AI Video Engine
          </div>
          
          <div className="flex-1 max-w-3xl hidden md:block">
            <GlobalSearch />
          </div>

          <div className="flex items-center gap-6 shrink-0">
            <span className="text-sm text-muted-foreground hidden sm:inline-block">Logged in as <strong className="text-foreground">{user.username}</strong></span>
            <button onClick={logout} className="text-sm font-semibold text-muted-foreground hover:text-destructive transition-colors">Sign out</button>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Upload Zone */}
        <section className="mb-14">
          <div 
            className="border-2 border-dashed border-border/60 rounded-3xl p-14 text-center bg-card/30 hover:bg-card/80 hover:border-primary/50 transition-all duration-300 cursor-pointer group relative overflow-hidden"
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              accept="video/*" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleUpload}
            />
            <div className="relative z-10">
              <div className="w-20 h-20 bg-primary/10 text-primary rounded-full flex items-center justify-center mx-auto mb-5 group-hover:scale-110 group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
                <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold mb-2">Upload a new video</h3>
              <p className="text-muted-foreground text-sm">Drag and drop or click to browse files</p>
            </div>
            {uploading && (
              <div className="absolute inset-0 bg-background/90 backdrop-blur-sm z-20 flex flex-col items-center justify-center">
                <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4"></div>
                <p className="font-semibold text-lg animate-pulse tracking-wide">Uploading and Deduplicating...</p>
              </div>
            )}
          </div>
        </section>

        {/* Video List */}
        <section>
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
            Your Library 
            <span className="bg-primary/20 text-primary text-sm px-3 py-1 rounded-full font-bold">{videos.length}</span>
          </h2>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[1, 2, 3].map(i => <div key={i} className="h-[280px] bg-card/50 animate-pulse rounded-3xl border border-border/50"></div>)}
            </div>
          ) : videos.length === 0 ? (
            <div className="text-center py-24 border border-border/50 rounded-3xl bg-card/30">
              <p className="text-muted-foreground text-lg">You haven&apos;t uploaded any videos yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {videos.map(video => (
                <div key={video.id} className="relative group/card">
                  {/* Delete button — visible on card hover */}
                  <button
                    id={`delete-video-${video.id}`}
                    onClick={e => { e.preventDefault(); e.stopPropagation(); setConfirmId(video.id); }}
                    disabled={deletingId === video.id}
                    className="absolute top-3 left-3 z-20 w-8 h-8 rounded-full bg-black/60 border border-white/10 flex items-center justify-center opacity-0 group-hover/card:opacity-100 hover:bg-red-500/80 hover:border-red-400/30 transition-all duration-200 disabled:opacity-50"
                    title="Delete video"
                  >
                    {deletingId === video.id ? (
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                  </button>

                  <Link href={`/video/${video.id}`}>
                    <div className={`bg-card border border-border/60 rounded-3xl overflow-hidden hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 group cursor-pointer flex flex-col h-[280px] ${deletingId === video.id ? 'opacity-50 pointer-events-none' : ''}`}>
                      <div className="h-40 bg-zinc-900/80 relative flex items-center justify-center overflow-hidden">
                        {video.thumbnail_url ? (
                          <img
                            src={video.thumbnail_url}
                            alt={video.title}
                            className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                            onError={(e) => {
                              // Fallback to play icon on error
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <svg className="w-12 h-12 text-zinc-800 group-hover:scale-110 group-hover:text-zinc-700 transition-all duration-500" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z" />
                          </svg>
                        )}
                        <div className="absolute top-4 right-4 z-10 shadow-sm">
                          {getStatusBadge(video.status)}
                        </div>
                        {/* Gradient overlay for aesthetic */}
                        <div className="absolute inset-0 bg-gradient-to-t from-card to-transparent opacity-50"></div>
                      </div>
                      <div className="p-6 flex-1 flex flex-col bg-card relative">
                        <h3 className="font-bold text-[17px] leading-snug line-clamp-2 mb-3 group-hover:text-primary transition-colors">{video.title}</h3>
                        <div className="mt-auto flex justify-between items-center text-sm font-medium text-muted-foreground">
                          <span>{new Date(video.created_at).toLocaleDateString()}</span>
                          {video.duration && <span>{Math.round(video.duration / 60)}m</span>}
                        </div>
                      </div>
                    </div>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
