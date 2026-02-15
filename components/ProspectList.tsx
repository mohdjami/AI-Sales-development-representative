'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Loader2, Search, SlidersHorizontal, Plus, Filter } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import ProspectCard from './ProspectCard';
import ProspectModal, { Prospect } from './ProspectModal';
import ProspectPreferencesForm from './ProspectPreferencesForm';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

type ProspectListProps = {
  initialProspects: Prospect[];
};

export default function ProspectList({ initialProspects }: ProspectListProps) {
  const [prospects, setProspects] = useState<Prospect[]>(initialProspects);
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('alignment');
  const [minScore, setMinScore] = useState('0.5');
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const handleGenerateNewProspects = async (preferences: { company_description: string; goal: string; job_titles: string[] }) => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app';
      const response = await fetch(`${apiUrl}/prospects/discover`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error('Failed to discover prospects');
      }

      const data = await response.json();
      if (data.prospects && data.prospects.length > 0) {
        setProspects(data.prospects);
        toast.success(`Found ${data.prospects.length} new prospects!`);
        setIsDialogOpen(false);
      } else {
        toast.info("No new prospects found with existing criteria.");
      }
    } catch (error) {
      console.error('Error generating prospects:', error);
      toast.error("Failed to generate prospects. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const filteredProspects = prospects
    .filter((prospect) => {
      const query = searchQuery.toLowerCase();
      // Safely handle potential undefined fields
      const author = prospect.author || '';
      const role = prospect.role || '';
      const company = prospect.company || '';
      const industry = prospect.industry || '';

      return (
        author.toLowerCase().includes(query) ||
        role.toLowerCase().includes(query) ||
        company.toLowerCase().includes(query) ||
        industry.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      if (sortBy === 'alignment') {
        return (b.alignment_score || 0) - (a.alignment_score || 0);
      }
      return 0;
    });


  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between bg-card/30 p-4 rounded-xl border border-border/50 backdrop-blur-sm">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name, role, or company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-background/50 border-border/50 focus:bg-background transition-colors"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-[160px] bg-background/50 border-border/50">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="alignment">Highest Score</SelectItem>
              <SelectItem value="recent">Most Recent</SelectItem>
            </SelectContent>
          </Select>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="ml-auto md:ml-0 shadow-lg shadow-primary/20">
                <Plus className="mr-2 h-4 w-4" />
                Find New Prospects
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Find New Prospects</DialogTitle>
                <DialogDescription>
                  Enter your company details and goals to find relevant leads from the web.
                </DialogDescription>
              </DialogHeader>
              <ProspectPreferencesForm onSubmit={handleGenerateNewProspects} isLoading={loading} />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {filteredProspects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-4 rounded-xl border border-dashed border-border/50 bg-card/10">
          <div className="p-4 rounded-full bg-primary/10">
            <Search className="h-8 w-8 text-primary/60" />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-semibold">No prospects found</h3>
            <p className="text-muted-foreground max-w-sm mx-auto">
              {prospects.length === 0
                ? 'Generate new prospects to start building your pipeline.'
                : 'Try adjusting your search terms or filters to find what you looking for.'}
            </p>
          </div>
          {prospects.length === 0 && (
            <Button onClick={() => setIsDialogOpen(true)} variant="outline" className="mt-4">
              Generate Prospects
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProspects.map((prospect, index) => (
            <ProspectCard
              key={index}
              prospect={prospect}
              onClick={() => setSelectedProspect(prospect)}
            />
          ))}
        </div>
      )}

      {selectedProspect && (
        <ProspectModal prospect={selectedProspect} onClose={() => setSelectedProspect(null)} />
      )}
    </div>
  );
}

