'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, Bot, X, FileText, BrainCircuit, Calendar, Video, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { MeetingSearch } from './MeetingSearch';
import { cn } from '@/lib/utils';

export type Meeting = {
  id: string;
  bot_id: string;
  meeting_url: string;
  status?: 'active' | 'completed';
  date?: string;
  title?: string;
  duration?: string;
  description?: string;
  participants?: string[];
  transcript?: string;
  ai_summary?: string;
  action_items?: string | string[];
  insights?: string | string[];
};

type MeetingData = {
  transcript: string;
  summary: string;
  actionItems: string[];
  keyInsights: string[];
  sentiment: string;
};

export function MeetingNotes({ initialMeetings }: { initialMeetings: Meeting[] }) {
  const [meetings, setMeetings] = useState<Meeting[]>(initialMeetings);
  const [loading, setLoading] = useState(false);
  const [meetingUrl, setMeetingUrl] = useState('');
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [meetingData, setMeetingData] = useState<MeetingData | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [meetingTitle, setMeetingTitle] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const addBot = async () => {
    setLoading(true);
    try {
      const meetingData = {
        meeting_url: meetingUrl,
        title: meetingTitle,
      };
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app';
      const response = await fetch(`${apiUrl}/add-bot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: meetingData.title,
          meeting_url: meetingData.meeting_url,
        }),
      });
      const data = await response.json();
      console.log(data.meeting.botId);
      const newMeeting: Meeting = {
        id: data.meeting.id,
        bot_id: data.meeting.botId,
        ...meetingData,
        status: 'active',
      };
      setMeetings([newMeeting, ...meetings]);
      setShowAddDialog(false);
      resetForm();
      toast.success('Bot added successfully!');
    } catch (error) {
      console.log(error);
      toast.error('Failed to add bot');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setMeetingUrl('');
    setMeetingTitle('');
  };

  const removeBot = async (meeting: Meeting) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app';
      const response = await fetch(`${apiUrl}/remove-bot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-meeting-baas-api-key': process.env.MEETING_BASS_API!,
        },
        body: JSON.stringify(meeting),
      });
      console.log(response);
      if (!response.ok) {
        throw new Error('Failed to delete bot');
      }

      // Update the state to remove the meeting from the list
      setMeetings(meetings.filter((m) => m.id !== meeting.id));
      toast.success('Bot removed successfully!');
    } catch (error) {
      toast.error('Failed to remove bot');
    }
  };

  const getMeetingData = async (meeting: Meeting) => {
    setLoading(true);
    try {
      // Extract action items and key insights from meeting data if available
      let actionItems: string[] = [];
      let keyInsights: string[] = [];

      // Try to parse action_items from meeting data
      try {
        if (meeting.action_items) {
          if (typeof meeting.action_items === 'string') {
            actionItems = JSON.parse(meeting.action_items);
          } else if (Array.isArray(meeting.action_items)) {
            actionItems = meeting.action_items;
          }
        }
      } catch (e) {
        console.error('Error parsing action items:', e);
      }

      // Try to parse insights from meeting data
      try {
        if (meeting.insights) {
          if (typeof meeting.insights === 'string') {
            keyInsights = JSON.parse(meeting.insights);
          } else if (Array.isArray(meeting.insights)) {
            keyInsights = meeting.insights;
          }
        }
      } catch (e) {
        console.error('Error parsing insights:', e);
      }

      // If we don't have action items or insights, provide some generic ones
      if (actionItems.length === 0) {
        actionItems = ['No action items recorded for this meeting'];
      }

      if (keyInsights.length === 0) {
        keyInsights = ['No insights recorded for this meeting'];
      }

      // Create the meeting data from actual meeting
      setMeetingData({
        transcript: meeting.transcript || 'No transcript available for this meeting.',
        summary: meeting.ai_summary || 'No summary available for this meeting.',
        actionItems: actionItems,
        keyInsights: keyInsights,
        sentiment: 'Neutral', // Default sentiment
      });

      setSelectedMeeting(meeting);
    } catch (error) {
      toast.error('Failed to fetch meeting data');
    } finally {
      setLoading(false);
    }
  };

  const refreshCompletedMeetings = async () => {
    setRefreshing(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app';
      const response = await fetch(`${apiUrl}/meetings`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch completed meetings');
      }

      const data = await response.json();

      if (data?.meetings) {
        // Merge new meetings with existing active ones
        setMeetings((prev) => {
          const activeMeetings = prev.filter((m) => m.status === 'active');
          return [...activeMeetings, ...data.meetings];
        });
        toast.success('Meetings refreshed successfully!');
      } else {
        toast.info('No new meetings found');
      }
    } catch (error) {
      toast.error('Failed to refresh meetings');
      console.error(error);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="grid gap-6 fade-in-bottom">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Meeting Notes</h2>
          <p className="text-muted-foreground">Manage your meeting bots and view insights</p>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="shadow-lg hover:shadow-primary/20 transition-all">
              <Plus className="mr-2 h-4 w-4" />
              Add Meeting Bot
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px] glass-card border-none shadow-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                Add Meeting Bot
              </DialogTitle>
              <DialogDescription>
                Paste a meeting link to have our AI bot join, record, and analyze the conversation.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <label className="text-sm font-medium">Meeting Title</label>
                <Input
                  placeholder="e.g. Q3 Sales Sync"
                  value={meetingTitle}
                  onChange={(e) => setMeetingTitle(e.target.value)}
                  className="bg-background/50"
                  autoFocus
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Meeting URL</label>
                <Input
                  placeholder="https://meet.google.com/..."
                  value={meetingUrl}
                  onChange={(e) => setMeetingUrl(e.target.value)}
                  className="bg-background/50"
                />
                <p className="text-xs text-muted-foreground">Supports Google Meet, Zoom, and Teams.</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
              <Button onClick={addBot} disabled={loading || !meetingUrl}>
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Bot className="mr-2 h-4 w-4" />
                )}
                Add Bot
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <MeetingSearch />

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="glass-card flex flex-col h-[400px]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-4 w-4 text-blue-500" />
              Active Meetings
            </CardTitle>
            <CardDescription>Currently monitored meetings</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <ScrollArea className="h-full pr-4">
              {meetings
                .filter((m) => m.status === 'active')
                .length > 0 ? (
                meetings.filter((m) => m.status === 'active').map((meeting) => (
                  <div
                    key={meeting.id}
                    className="flex items-center justify-between p-4 mb-3 rounded-lg border bg-card/50 hover:bg-card/80 transition-all group"
                  >
                    <div className="grid gap-1">
                      <div className="font-medium flex items-center gap-2">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        {meeting.title || "Untitled Meeting"}
                      </div>
                      <div className="text-xs text-muted-foreground font-mono">ID: {meeting.bot_id}</div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => removeBot(meeting)} className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10">
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center h-[200px] text-muted-foreground">
                  <Video className="h-8 w-8 mb-2 opacity-20" />
                  <p className="text-sm">No active meetings</p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="glass-card flex flex-col h-[400px]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Completed Meetings
                </CardTitle>
                <CardDescription>Past meetings with analysis</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={refreshCompletedMeetings}
                disabled={refreshing}
                className="h-8"
              >
                {refreshing ? (
                  <Loader2 className="h-3 w-3 animate-spin mr-2" />
                ) : (
                  <Bot className="h-3 w-3 mr-2 text-muted-foreground" />
                )}
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <ScrollArea className="h-full pr-4">
              {meetings
                .filter((m) => m.status === 'completed')
                .length > 0 ? (
                meetings.filter((m) => m.status === 'completed').map((meeting) => (
                  <div
                    key={meeting.id}
                    className="flex items-center justify-between p-4 mb-3 rounded-lg border bg-card/50 hover:bg-card/80 transition-all cursor-pointer group"
                    onClick={() => getMeetingData(meeting)}
                  >
                    <div className="grid gap-1">
                      <div className="font-medium group-hover:text-primary transition-colors">{meeting.title || 'Untitled'}</div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(meeting.date || '').toLocaleDateString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {meeting.duration || 'N/A'}
                        </span>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="text-muted-foreground group-hover:text-primary">
                      <BrainCircuit className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center h-[200px] text-muted-foreground">
                  <CheckCircle2 className="h-8 w-8 mb-2 opacity-20" />
                  <p className="text-sm">No completed meetings</p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {selectedMeeting && meetingData && (
        <Card className="glass-card animate-in slide-in-from-bottom-4 duration-500">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div className="space-y-1">
                <CardTitle className="text-xl">{selectedMeeting.title}</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <Calendar className="h-3 w-3" />
                  {new Date(selectedMeeting.date || '').toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </CardDescription>
              </div>
              <Badge variant="secondary" className="px-3 py-1 bg-primary/10 text-primary border-primary/20">
                {meetingData.sentiment} Sentiment
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full" defaultValue="summary">
              <AccordionItem value="summary" className="border-b-0 mb-4 bg-muted/30 rounded-lg px-4 border">
                <AccordionTrigger className="hover:no-underline py-4">
                  <div className="flex items-center gap-2 font-semibold">
                    <BrainCircuit className="h-4 w-4 text-purple-500" />
                    AI Summary & Insights
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-4">
                  <div className="space-y-6">
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Executive Summary</h4>
                      <p className="leading-relaxed bg-background/50 p-3 rounded-md border">{meetingData.summary}</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                          <AlertCircle className="h-3 w-3" /> Key Insights
                        </h4>
                        <ul className="space-y-2">
                          {meetingData.keyInsights.map((insight, index) => (
                            <li key={index} className="text-sm p-2 rounded bg-blue-500/5 border-l-2 border-blue-500">
                              {insight}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                          <CheckCircle2 className="h-3 w-3" /> Action Items
                        </h4>
                        <ul className="space-y-2">
                          {meetingData.actionItems.map((item, index) => (
                            <li key={index} className="text-sm p-2 rounded bg-green-500/5 border-l-2 border-green-500">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="transcript" className="border-b-0 bg-muted/30 rounded-lg px-4 border">
                <AccordionTrigger className="hover:no-underline py-4">
                  <div className="flex items-center gap-2 font-semibold">
                    <FileText className="h-4 w-4 text-blue-500" />
                    Full Transcript
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <ScrollArea className="h-[300px] w-full rounded-md border bg-background/50 p-4">
                    <p className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-muted-foreground">{meetingData.transcript}</p>
                  </ScrollArea>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
