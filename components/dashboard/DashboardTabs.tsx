'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DashboardOverview } from './DashboardOverview';
import { EmailAnalysis, FollowUps } from './FollowUps';
import { Meeting, MeetingNotes } from './MeetingNotes';
import { Prospect } from '../ProspectModal';

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
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="follow-ups">Follow-ups</TabsTrigger>
          <TabsTrigger value="meetings">Meetings</TabsTrigger>
        </TabsList>
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
    </Tabs>
  );
}
