"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { createClient } from "@/utils/supabase/client";
import { Mail, CheckCircle2, LogOut, Loader2 } from "lucide-react";
import { toast } from "sonner";

type GoogleStatus = {
    connected: boolean;
    email?: string;
    scopes?: string[];
    last_refreshed?: string;
};

export default function GoogleConnectButton() {
    const [status, setStatus] = useState<GoogleStatus>({ connected: false });
    const [loading, setLoading] = useState(true);
    const supabase = createClient();

    const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        "https://ai-sdr-production.up.railway.app";

    useEffect(() => {
        checkStatus();
        // Check URL params for callback result
        const params = new URLSearchParams(window.location.search);
        if (params.get("google_connected") === "true") {
            toast.success("Google account connected successfully!");
            checkStatus();
            // Clean up URL
            window.history.replaceState({}, "", window.location.pathname);
        }
        if (params.get("google_error")) {
            toast.error(`Google connection failed: ${params.get("google_error")}`);
            window.history.replaceState({}, "", window.location.pathname);
        }
    }, []);

    const checkStatus = async () => {
        try {
            const {
                data: { session },
            } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`${apiUrl}/auth/google/status`, {
                headers: { Authorization: `Bearer ${session.access_token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
            }
        } catch (error) {
            console.error("Error checking Google status:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleConnect = async () => {
        try {
            setLoading(true);
            const {
                data: { session },
            } = await supabase.auth.getSession();
            if (!session) {
                toast.error("Please sign in first");
                return;
            }

            const res = await fetch(`${apiUrl}/auth/google`, {
                headers: { Authorization: `Bearer ${session.access_token}` },
            });
            if (!res.ok) throw new Error("Failed to get auth URL");

            const { auth_url } = await res.json();
            window.location.href = auth_url;
        } catch (error) {
            console.error("Error connecting Google:", error);
            toast.error("Failed to connect Google account");
        } finally {
            setLoading(false);
        }
    };

    const handleDisconnect = async () => {
        try {
            setLoading(true);
            const {
                data: { session },
            } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`${apiUrl}/auth/google/disconnect`, {
                method: "POST",
                headers: { Authorization: `Bearer ${session.access_token}` },
            });
            if (res.ok) {
                setStatus({ connected: false });
                toast.success("Google account disconnected");
            }
        } catch (error) {
            console.error("Error disconnecting Google:", error);
            toast.error("Failed to disconnect");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Button variant="outline" size="sm" disabled>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Checking...
            </Button>
        );
    }

    if (status.connected) {
        return (
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-600 dark:text-green-400 text-sm">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                <span className="hidden sm:inline">{status.email}</span>
                                <span className="sm:hidden">Connected</span>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                                onClick={handleDisconnect}
                            >
                                <LogOut className="h-3.5 w-3.5" />
                            </Button>
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Google account connected as {status.email}</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        );
    }

    return (
        <Button
            variant="outline"
            size="sm"
            onClick={handleConnect}
            className="gap-2 border-blue-500/20 hover:bg-blue-500/5 hover:border-blue-500/30 text-blue-600 dark:text-blue-400"
        >
            <Mail className="h-4 w-4" />
            Connect Gmail
        </Button>
    );
}
