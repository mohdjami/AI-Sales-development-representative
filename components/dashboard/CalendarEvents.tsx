"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/utils/supabase/client";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
    CalendarPlus,
    Clock,
    ExternalLink,
    Loader2,
    Users,
    Video,
    Mail,
} from "lucide-react";
import { toast } from "sonner";

type CalendarEvent = {
    id: string;
    summary: string;
    description: string;
    start: string;
    end: string;
    location: string;
    htmlLink: string;
    attendees: { email: string; status: string }[];
    meetLink?: string;
};

type NewEvent = {
    summary: string;
    start_time: string;
    end_time: string;
    description: string;
    attendees: string;
    location: string;
};

export function CalendarEvents() {
    const [events, setEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [connected, setConnected] = useState(false);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [creating, setCreating] = useState(false);
    const [newEvent, setNewEvent] = useState<NewEvent>({
        summary: "",
        start_time: "",
        end_time: "",
        description: "",
        attendees: "",
        location: "",
    });

    const supabase = createClient();
    const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        "https://ai-sdr-production.up.railway.app";

    useEffect(() => {
        fetchEvents();
    }, []);

    const getSession = async () => {
        const {
            data: { session },
        } = await supabase.auth.getSession();
        return session;
    };

    const fetchEvents = async () => {
        try {
            setLoading(true);
            const session = await getSession();
            if (!session) return;

            // Check connection status first
            const statusRes = await fetch(`${apiUrl}/auth/google/status`, {
                headers: { Authorization: `Bearer ${session.access_token}` },
            });
            const statusData = await statusRes.json();
            setConnected(statusData.connected);

            if (!statusData.connected) {
                setLoading(false);
                return;
            }

            const res = await fetch(`${apiUrl}/calendar/events?max_results=15`, {
                headers: { Authorization: `Bearer ${session.access_token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setEvents(data.events || []);
            }
        } catch (error) {
            console.error("Error fetching calendar events:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateEvent = async () => {
        if (!newEvent.summary || !newEvent.start_time || !newEvent.end_time) {
            toast.error("Please fill in event title, start time, and end time");
            return;
        }

        try {
            setCreating(true);
            const session = await getSession();
            if (!session) return;

            const payload = {
                summary: newEvent.summary,
                start_time: new Date(newEvent.start_time).toISOString(),
                end_time: new Date(newEvent.end_time).toISOString(),
                description: newEvent.description,
                location: newEvent.location,
                attendees: newEvent.attendees
                    ? newEvent.attendees
                        .split(",")
                        .map((e) => e.trim())
                        .filter(Boolean)
                    : [],
            };

            const res = await fetch(`${apiUrl}/calendar/events`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${session.access_token}`,
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to create event");
            }

            const data = await res.json();
            toast.success("Meeting scheduled successfully!");
            setShowCreateDialog(false);
            setNewEvent({
                summary: "",
                start_time: "",
                end_time: "",
                description: "",
                attendees: "",
                location: "",
            });
            fetchEvents();
        } catch (error: any) {
            console.error("Error creating event:", error);
            toast.error(error.message || "Failed to schedule meeting");
        } finally {
            setCreating(false);
        }
    };

    const formatEventTime = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
            hour12: true,
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-primary/50" />
            </div>
        );
    }

    if (!connected) {
        return (
            <Card className="glass-card border-dashed border-2 border-muted-foreground/20">
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="p-4 rounded-full bg-blue-500/10 mb-4">
                        <CalendarPlus className="h-8 w-8 text-blue-500" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">
                        Connect Google Calendar
                    </h3>
                    <p className="text-muted-foreground max-w-md mb-4">
                        Connect your Google account to view upcoming events and schedule
                        meetings with prospects directly from your dashboard.
                    </p>
                    <p className="text-sm text-muted-foreground">
                        Use the &quot;Connect Gmail&quot; button in the header to get
                        started.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold">Upcoming Events</h2>
                    <p className="text-sm text-muted-foreground">
                        {events.length} events on your calendar
                    </p>
                </div>
                <Button
                    onClick={() => setShowCreateDialog(true)}
                    className="gap-2 shadow-lg shadow-primary/20"
                >
                    <CalendarPlus className="h-4 w-4" />
                    Schedule Meeting
                </Button>
            </div>

            {events.length === 0 ? (
                <Card className="glass-card">
                    <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                        <Clock className="h-8 w-8 text-muted-foreground/50 mb-3" />
                        <p className="text-muted-foreground">No upcoming events</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-3">
                    {events.map((event) => (
                        <Card
                            key={event.id}
                            className="glass-card hover:border-primary/20 transition-all"
                        >
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-medium truncate">
                                            {event.summary || "No title"}
                                        </h3>
                                        <div className="flex items-center gap-4 mt-1.5 text-sm text-muted-foreground">
                                            <span className="flex items-center gap-1">
                                                <Clock className="h-3.5 w-3.5" />
                                                {formatEventTime(event.start)}
                                            </span>
                                            {event.attendees?.length > 0 && (
                                                <span className="flex items-center gap-1">
                                                    <Users className="h-3.5 w-3.5" />
                                                    {event.attendees.length} attendee
                                                    {event.attendees.length > 1 ? "s" : ""}
                                                </span>
                                            )}
                                        </div>
                                        {event.description && (
                                            <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                                                {event.description}
                                            </p>
                                        )}
                                    </div>
                                    <div className="flex gap-2 shrink-0">
                                        {event.meetLink && (
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="gap-1.5"
                                                asChild
                                            >
                                                <a
                                                    href={event.meetLink}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    <Video className="h-3.5 w-3.5" />
                                                    Join
                                                </a>
                                            </Button>
                                        )}
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="gap-1.5"
                                            asChild
                                        >
                                            <a
                                                href={event.htmlLink}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                <ExternalLink className="h-3.5 w-3.5" />
                                            </a>
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Create Event Dialog */}
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogContent className="sm:max-w-[500px] glass-card border-primary/10 p-0 overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />

                    <DialogHeader className="px-6 py-4 bg-muted/20 border-b border-border/50">
                        <DialogTitle className="flex items-center gap-2">
                            <CalendarPlus className="h-5 w-5 text-primary" />
                            Schedule Meeting
                        </DialogTitle>
                    </DialogHeader>

                    <div className="p-6 space-y-4">
                        <div className="space-y-2">
                            <Label>Meeting Title *</Label>
                            <Input
                                placeholder="e.g., Product Demo with Acme Corp"
                                value={newEvent.summary}
                                onChange={(e) =>
                                    setNewEvent({ ...newEvent, summary: e.target.value })
                                }
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Start Time *</Label>
                                <Input
                                    type="datetime-local"
                                    value={newEvent.start_time}
                                    onChange={(e) =>
                                        setNewEvent({ ...newEvent, start_time: e.target.value })
                                    }
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>End Time *</Label>
                                <Input
                                    type="datetime-local"
                                    value={newEvent.end_time}
                                    onChange={(e) =>
                                        setNewEvent({ ...newEvent, end_time: e.target.value })
                                    }
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label className="flex items-center gap-2">
                                <Mail className="h-3.5 w-3.5" />
                                Attendees
                            </Label>
                            <Input
                                placeholder="Comma-separated emails (e.g., john@acme.com, jane@acme.com)"
                                value={newEvent.attendees}
                                onChange={(e) =>
                                    setNewEvent({ ...newEvent, attendees: e.target.value })
                                }
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Description</Label>
                            <Textarea
                                placeholder="Meeting agenda or notes..."
                                value={newEvent.description}
                                onChange={(e) =>
                                    setNewEvent({ ...newEvent, description: e.target.value })
                                }
                                className="min-h-[80px]"
                            />
                        </div>
                    </div>

                    <DialogFooter className="px-6 py-4 bg-muted/20 border-t border-border/50 gap-2">
                        <Button
                            variant="outline"
                            onClick={() => setShowCreateDialog(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleCreateEvent}
                            disabled={creating}
                            className="gap-2 shadow-lg shadow-primary/20"
                        >
                            {creating ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" /> Creating...
                                </>
                            ) : (
                                <>
                                    <CalendarPlus className="h-4 w-4" /> Schedule with Meet
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
