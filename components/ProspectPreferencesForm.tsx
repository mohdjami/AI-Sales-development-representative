import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Loader2, Plus, X, Sparkles, Globe, AtSign } from 'lucide-react';
import { DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';

type DiscoveryPreferences = {
    company_description: string;
    goal: string;
    job_titles: string[];
    enable_playwright: boolean;
    enable_email_discovery: boolean;
    keyword_hint: string;
};

type ProspectPreferencesFormProps = {
    onSubmit: (preferences: DiscoveryPreferences) => Promise<void>;
    isLoading: boolean;
};

export default function ProspectPreferencesForm({ onSubmit, isLoading }: ProspectPreferencesFormProps) {
    const [companyDescription, setCompanyDescription] = useState('');
    const [goal, setGoal] = useState('');
    const [jobTitleInput, setJobTitleInput] = useState('');
    const [jobTitles, setJobTitles] = useState<string[]>([]);
    const [keywordHint, setKeywordHint] = useState('');
    const [enablePlaywright, setEnablePlaywright] = useState(true);
    const [enableEmailDiscovery, setEnableEmailDiscovery] = useState(true);

    // Auto-fill state
    const [jobDescription, setJobDescription] = useState('');
    const [isAutoFilling, setIsAutoFilling] = useState(false);

    const handleAutoFill = async () => {
        if (!jobDescription.trim()) {
            toast.error("Please paste a job description first.");
            return;
        }

        setIsAutoFilling(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/prospects/autofill`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_description: jobDescription }),
            });

            if (!response.ok) throw new Error("Failed to auto-fill");

            const data = await response.json();

            if (data.company_description) setCompanyDescription(data.company_description);
            if (data.goal) setGoal(data.goal);
            if (data.job_titles && Array.isArray(data.job_titles)) {
                // Merge new titles with existing ones
                const uniqueTitles = new Set([...jobTitles, ...data.job_titles]);
                setJobTitles(Array.from(uniqueTitles));
            }

            toast.success("Preferences auto-filled from Job Description!");
        } catch (error) {
            console.error("Auto-fill error:", error);
            toast.error("Failed to auto-fill. Please try manually.");
        } finally {
            setIsAutoFilling(false);
        }
    };

    const handleAddTitle = () => {
        if (jobTitleInput.trim() && !jobTitles.includes(jobTitleInput.trim())) {
            setJobTitles([...jobTitles, jobTitleInput.trim()]);
            setJobTitleInput('');
        }
    };

    const handleRemoveTitle = (title: string) => {
        setJobTitles(jobTitles.filter((t) => t !== title));
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddTitle();
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({
            company_description: companyDescription,
            goal,
            job_titles: jobTitles,
            enable_playwright: enablePlaywright,
            enable_email_discovery: enableEmailDiscovery,
            keyword_hint: keywordHint,
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {/* Auto-fill Section */}
            <div className="p-3 bg-primary/5 rounded-lg border border-primary/10 space-y-2">
                <Label htmlFor="jd" className="flex items-center gap-2 text-primary">
                    <Sparkles className="h-4 w-4" />
                    Auto-fill with AI
                </Label>
                <Textarea
                    id="jd"
                    placeholder="Paste a Job Description here to auto-generate preferences..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    className="min-h-[80px] bg-background/50"
                />
                <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={handleAutoFill}
                    disabled={isAutoFilling || !jobDescription}
                    className="w-full"
                >
                    {isAutoFilling ? (
                        <>
                            <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                            Analyzing JD...
                        </>
                    ) : (
                        'Generate Preferences'
                    )}
                </Button>
            </div>

            <div className="space-y-2">
                <Label htmlFor="company">Company Description</Label>
                <Textarea
                    id="company"
                    placeholder="e.g. We are an AI startup building SDR agents for B2B sales teams..."
                    value={companyDescription}
                    onChange={(e) => setCompanyDescription(e.target.value)}
                    required
                    className="min-h-[80px]"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="goal">Prospecting Goal</Label>
                <Textarea
                    id="goal"
                    placeholder="e.g. Find Head of Sales at SaaS companies with 50-200 employees..."
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    required
                    className="min-h-[60px]"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="titles">Job Titles</Label>
                <div className="flex gap-2">
                    <Input
                        id="titles"
                        placeholder="e.g. VP of Sales"
                        value={jobTitleInput}
                        onChange={(e) => setJobTitleInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                    <Button type="button" variant="outline" onClick={handleAddTitle} size="icon">
                        <Plus className="h-4 w-4" />
                    </Button>
                </div>

                {jobTitles.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                        {jobTitles.map((title) => (
                            <div key={title} className="flex items-center gap-1 bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-sm">
                                <span>{title}</span>
                                <button type="button" onClick={() => handleRemoveTitle(title)} className="text-muted-foreground hover:text-foreground">
                                    <X className="h-3 w-3" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Keyword Hint */}
            <div className="space-y-2">
                <Label htmlFor="keyword" className="text-sm">Keyword Hint <span className="text-muted-foreground font-normal">(optional)</span></Label>
                <Input
                    id="keyword"
                    placeholder="e.g. AI SaaS, fintech startup, Series A"
                    value={keywordHint}
                    onChange={(e) => setKeywordHint(e.target.value)}
                    className="bg-background/50"
                />
                <p className="text-xs text-muted-foreground">Helps the AI router pick the most relevant sources.</p>
            </div>

            {/* Toggles */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                <div className="flex items-center justify-between gap-2">
                    <Label htmlFor="playwright-toggle" className="flex items-center gap-1.5 text-sm cursor-pointer">
                        <Globe className="h-3.5 w-3.5 text-primary" />
                        Web Scraping
                    </Label>
                    <Switch
                        id="playwright-toggle"
                        checked={enablePlaywright}
                        onCheckedChange={setEnablePlaywright}
                    />
                </div>
                <div className="flex items-center justify-between gap-2">
                    <Label htmlFor="email-toggle" className="flex items-center gap-1.5 text-sm cursor-pointer">
                        <AtSign className="h-3.5 w-3.5 text-primary" />
                        Email Discovery
                    </Label>
                    <Switch
                        id="email-toggle"
                        checked={enableEmailDiscovery}
                        onCheckedChange={setEnableEmailDiscovery}
                    />
                </div>
            </div>

            <DialogFooter>
                <Button type="submit" disabled={isLoading || jobTitles.length === 0 || !companyDescription || !goal}>
                    {isLoading ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Finding Prospects...
                        </>
                    ) : (
                        'Start Discovery'
                    )}
                </Button>
            </DialogFooter>
        </form>
    );
}
