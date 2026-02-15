import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Search } from 'lucide-react';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';

import { createClient } from '@/utils/supabase/client';

type MeetingSource = {
  meeting_id: string;
  title: string;
  date: string;
  score: number;
};

type SearchResult = {
  status: string;
  response: string;
  sources: MeetingSource[];
};

export function MeetingSearch() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [meetings, setMeetings] = useState([]);

  const searchKnowledgeBase = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        toast.error('Please verify you are logged in');
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app';
      const response = await fetch(`${apiUrl}/search-knowledge-base`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          query: query,
          max_results: 5,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to search knowledge base');
      }

      const data = await response.json();
      setSearchResult(data);
    } catch (error) {
      console.error('Error searching knowledge base:', error);
      toast.error('Failed to search knowledge base');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchKnowledgeBase();
    }
  };

  const getMeetingData = async (meeting: any) => {
    // Implementation of getMeetingData function
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Search Meeting Knowledge Base</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center space-x-2 mb-4">
          <Input
            placeholder="Ask anything about your meetings..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1"
          />
          <Button onClick={searchKnowledgeBase} disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Search className="h-4 w-4 mr-2" />
            )}
            Search
          </Button>
        </div>

        {searchResult && (
          <div className="mt-4 space-y-4">
            <div className="bg-muted p-4 rounded-md">
              <h3 className="text-md font-medium mb-2">Answer:</h3>
              <p className="text-sm whitespace-pre-line">{searchResult.response}</p>
            </div>

            {searchResult.sources.length > 0 && (
              <div>
                <h3 className="text-md font-medium mb-2">Sources:</h3>
                <ScrollArea className="h-[150px]">
                  <div className="space-y-2">
                    {searchResult.sources.map((source, index) => (
                      <div
                        key={index}
                        className="bg-background border rounded p-3 cursor-pointer hover:bg-muted/30 transition-colors"
                        onClick={() => {
                          const meeting = meetings.find((m: any) => m.id === source.meeting_id);
                          if (meeting) {
                            getMeetingData(meeting);
                          } else {
                            toast.error('Meeting details not available');
                          }
                        }}
                      >
                        <div className="flex justify-between">
                          <h4 className="font-medium">{source.title}</h4>
                          <span className="text-xs text-muted-foreground">
                            Relevance: {Math.round(source.score * 100)}%
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">ID: {source.meeting_id}</p>
                        <p className="text-xs text-muted-foreground">
                          Date: {new Date(source.date).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-blue-500 mt-1">
                          Click to view full meeting details
                        </p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
