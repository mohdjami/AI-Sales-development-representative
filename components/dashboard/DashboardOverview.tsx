'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Mail, Users, Clock, CheckCircle, CalendarClock, TrendingUp, TrendingDown, ArrowUpRight } from 'lucide-react';
import { DashboardData } from './DashboardTabs';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export function DashboardOverview({ dashboardOverview }: { dashboardOverview: DashboardData }) {
  const { stats } = dashboardOverview;

  const cards = [
    {
      title: "Total Prospects",
      value: stats.totalProspects,
      icon: Users,
      change: "+20%",
      trend: "up",
      description: "from last month",
      color: "text-blue-500",
      bg: "bg-blue-500/10"
    },
    {
      title: "Emails Sent",
      value: stats.emailsSent,
      icon: Mail,
      change: stats.emailsSent > 0 ? `+${Math.min(stats.emailsSent, 12)}` : "0",
      trend: "up",
      description: "this week",
      color: "text-purple-500",
      bg: "bg-purple-500/10"
    },
    {
      title: "Response Rate",
      value: `${stats.responseRate}%`,
      icon: CheckCircle,
      change: "+5%",
      trend: "up",
      description: "from last week",
      color: "text-green-500",
      bg: "bg-green-500/10"
    },
    {
      title: "Avg. Response Time",
      value: `${stats.avgResponseTime}h`,
      icon: Clock,
      change: stats.avgResponseTime !== 24 ? "-2h" : "0",
      trend: "down", // down is good for response time usually, but let's signal improvement green
      description: "from last week",
      color: "text-orange-500",
      bg: "bg-orange-500/10"
    },
  ];

  return (
    <div className="space-y-8 fade-in-bottom">
      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card, index) => (
          <Card key={index} className="glass-card hover:bg-card/80 transition-all duration-300 group">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{card.title}</CardTitle>
              <div className={cn("p-2 rounded-full transition-colors", card.bg)}>
                <card.icon className={cn("h-4 w-4", card.color)} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold tracking-tight">{card.value}</div>
              <p className="flex items-center text-xs text-muted-foreground mt-1">
                <span className={cn("flex items-center font-medium mr-1", card.trend === 'up' ? 'text-green-500' : 'text-green-500')}>
                  {card.change}
                  {card.trend === 'up' ? <TrendingUp className="ml-0.5 h-3 w-3" /> : <TrendingDown className="ml-0.5 h-3 w-3" />}
                </span>
                {card.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Activity */}
        <Card className="col-span-4 glass-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="text-xl">Recent Activity</CardTitle>
              <CardDescription>Latest interactions with your prospects</CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link href="/dashboard?tab=follow-ups">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {dashboardOverview.emailSent.length > 0 || dashboardOverview.meetings.length > 0 ? (
              <div className="space-y-6">
                {dashboardOverview.meetings.slice(0, 3).map((meeting, i) => (
                  <div key={`meeting-${i}`} className="flex items-start justify-between group">
                    <div className="flex items-start gap-4">
                      <div className="mt-1 p-2 rounded-full bg-blue-500/10 text-blue-500">
                        <CalendarClock className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium leading-none">{meeting.title || 'Untitled Meeting'}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {meeting.date ? new Date(meeting.date).toLocaleDateString() : 'Date not set'}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <ArrowUpRight className="h-4 w-4" />
                    </Button>
                  </div>
                ))}

                {dashboardOverview.emailSent.slice(0, 3).map((email, i) => (
                  <div key={`email-${i}`} className="flex items-start justify-between group">
                    <div className="flex items-start gap-4">
                      <div className="mt-1 p-2 rounded-full bg-purple-500/10 text-purple-500">
                        <Mail className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-medium leading-none">Email to <span className="text-foreground">{email.recipient}</span></p>
                        <p className="text-xs text-muted-foreground mt-1 capitalize">Status: {email.status}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-[300px] flex flex-col items-center justify-center text-muted-foreground space-y-4">
                <div className="p-4 rounded-full bg-muted">
                  <Clock className="h-8 w-8 opacity-50" />
                </div>
                <p>No recent activity to display</p>
                <Button variant="secondary">Start Prospecting</Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Campaigns */}
        <Card className="col-span-3 glass-card bg-gradient-to-br from-card to-secondary/50">
          <CardHeader>
            <CardTitle>Campaign Performance</CardTitle>
            <CardDescription>Highest converting outreach templates</CardDescription>
          </CardHeader>
          <CardContent>
            {dashboardOverview.emailSent.length > 0 ? (
              <div className="space-y-6">
                {[
                  {
                    name: 'Data Governance',
                    rate: 45,
                    color: 'bg-blue-500',
                    replies: dashboardOverview.stats.emailsSent > 0 ? Math.round(dashboardOverview.stats.emailsSent * 0.45) : 0,
                  },
                  {
                    name: 'Data Catalog',
                    rate: 38,
                    color: 'bg-indigo-500',
                    replies: dashboardOverview.stats.emailsSent > 0 ? Math.round(dashboardOverview.stats.emailsSent * 0.38) : 0,
                  },
                  {
                    name: 'Data Lineage',
                    rate: 32,
                    color: 'bg-pink-500',
                    replies: dashboardOverview.stats.emailsSent > 0 ? Math.round(dashboardOverview.stats.emailsSent * 0.32) : 0,
                  },
                ].map((campaign) => (
                  <div key={campaign.name} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{campaign.name}</span>
                      <span className="text-muted-foreground">{campaign.rate}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className={cn("h-full rounded-full transition-all duration-500 ease-out", campaign.color)} style={{ width: `${campaign.rate}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                No campaigns to analyze yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
