import { DashboardTabs } from '@/components/dashboard/DashboardTabs';
import redis from '@/utils/redis';
import { createClient } from '@/utils/supabase/server';
import { Sparkles } from 'lucide-react';

export default async function DashboardPage() {
  const supabase = await createClient();

  // Fetch emails with status for analytics
  const { data: emailsData } = await supabase.from('emails').select('*');

  // Fetch all meetings with complete data
  const { data: meetingsData } = await supabase
    .from('meetings')
    .select('*')
    .order('date', { ascending: false });

  // Fetch prospects data
  const { data: prospectsData } = await supabase.from('prospects').select('*');

  // Get analyzed emails from Redis cache
  const cachedEmails = await redis.get('analyzed_emails');

  // Calculate statistics
  const sentEmails = emailsData?.filter((email) => email.status === 'sent') || [];
  const repliedEmails = emailsData?.filter((email) => email.status === 'replied') || [];
  const responseRate =
    sentEmails.length > 0 ? Math.round((repliedEmails.length / sentEmails.length) * 100) : 0;

  // Calculate average response time (if replied_at and created_at exist)
  let totalResponseTime = 0;
  let responseCount = 0;

  repliedEmails.forEach((email) => {
    if (email.replied_at && email.created_at) {
      const repliedDate = new Date(email.replied_at);
      const sentDate = new Date(email.created_at);
      const diffHours = Math.round((repliedDate.getTime() - sentDate.getTime()) / (1000 * 60 * 60));
      totalResponseTime += diffHours;
      responseCount++;
    }
  });

  const avgResponseHours = responseCount > 0 ? Math.round(totalResponseTime / responseCount) : 24;

  const dashboardData = {
    // Email data
    cachedEmails: JSON.parse(cachedEmails || '[]'),
    emailSent: emailsData || [],

    // Meeting data
    meetings: meetingsData || [],

    // Prospect data
    prospects: prospectsData || [],

    // Statistics
    stats: {
      totalProspects: prospectsData?.length || 0,
      emailsSent: sentEmails.length,
      responseRate: responseRate,
      avgResponseTime: avgResponseHours,
      completedMeetings: meetingsData?.filter((m) => m.status === 'completed')?.length || 0,
    },
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent flex items-center gap-2">
            Dashboard
            <Sparkles className="h-6 w-6 text-primary animate-pulse" />
          </h1>
          <p className="text-muted-foreground text-lg">
            Overview of your sales pipeline and activity
          </p>
        </div>
        <DashboardTabs dashboardData={dashboardData} />
      </div>
    </div>
  );
}
