'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DashboardOverview } from './DashboardOverview';
import { EmailAnalysis, FollowUps } from './FollowUps';
import { Meeting, MeetingNotes } from './MeetingNotes';
import { CalendarEvents } from './CalendarEvents';
import { Prospect } from '../ProspectModal';
import GoogleConnectButton from '../GoogleConnectButton';

export type EmailSent = {
  recipient?: string;
  subject?: string;
  body?: string;
  status?: string;
};

export type DashboardData = {
  cachedEmails: EmailAnalysis[];
  meetings: Meeting[];
  emailSent: EmailSent[];
  prospects: Prospect[];
  stats: {
    totalProspects: number;
    emailsSent: number;
    responseRate: number;
    avgResponseTime: number;
    completedMeetings: number;
  };
};

export type DashboardTabsProps = {
  dashboardData: DashboardData;
};
export function DashboardTabs({ dashboardData }: DashboardTabsProps) {
  return (
    <Tabs defaultValue="overview" className="space-y-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <TabsList className="grid w-full grid-cols-4 lg:w-[500px]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="follow-ups">Follow-ups</TabsTrigger>
          <TabsTrigger value="meetings">Meetings</TabsTrigger>
          <TabsTrigger value="calendar">Calendar</TabsTrigger>
        </TabsList>
        <GoogleConnectButton />
      </div>

      <TabsContent value="overview" className="space-y-6 focus-visible:outline-none focus-visible:ring-0">
        <DashboardOverview dashboardOverview={dashboardData} />
      </TabsContent>

      <TabsContent value="follow-ups" className="space-y-6 focus-visible:outline-none focus-visible:ring-0">
        <FollowUps initialEmails={dashboardData.cachedEmails} />
      </TabsContent>

      <TabsContent value="meetings" className="space-y-6 focus-visible:outline-none focus-visible:ring-0">
        <MeetingNotes initialMeetings={dashboardData.meetings} />
      </TabsContent>

      <TabsContent value="calendar" className="space-y-6 focus-visible:outline-none focus-visible:ring-0">
        <CalendarEvents />
      </TabsContent>
    </Tabs>
  );
}
