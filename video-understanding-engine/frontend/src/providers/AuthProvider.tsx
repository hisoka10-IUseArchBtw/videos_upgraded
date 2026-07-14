"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import { fetchApi } from "@/services/api";
import { useRouter, usePathname } from "next/navigation";

export interface User {
  user_id: string;
  email: string;
  username: string;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const loadUser = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      if (pathname !== "/login" && pathname !== "/signup") {
        router.push("/login");
      }
      return;
    }

    try {
      const data = await fetchApi("/users/me");
      setUser(data);
    } catch (err) {
      console.error("Failed to load user", err);
      localStorage.removeItem("token");
      setUser(null);
      if (pathname !== "/login" && pathname !== "/signup") {
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, [pathname]);

  const login = async (token: string) => {
    localStorage.setItem("token", token);
    await loadUser();
    router.push("/");
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
