import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Loader2, Plus, X } from 'lucide-react';
import { DialogFooter } from '@/components/ui/dialog';

type ProspectPreferencesFormProps = {
    onSubmit: (preferences: { company_description: string; goal: string; job_titles: string[] }) => Promise<void>;
    isLoading: boolean;
};

export default function ProspectPreferencesForm({ onSubmit, isLoading }: ProspectPreferencesFormProps) {
    const [companyDescription, setCompanyDescription] = useState('');
    const [goal, setGoal] = useState('');
    const [jobTitleInput, setJobTitleInput] = useState('');
    const [jobTitles, setJobTitles] = useState<string[]>([]);

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
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
                <Label htmlFor="company">Company Description</Label>
                <Textarea
                    id="company"
                    placeholder="e.g. We are an AI startup building SDR agents for B2B sales teams..."
                    value={companyDescription}
                    onChange={(e) => setCompanyDescription(e.target.value)}
                    required
                    className="min-h-[100px]"
                />
                <p className="text-xs text-muted-foreground">Describe what your company does to help find relevant prospects.</p>
            </div>

            <div className="space-y-2">
                <Label htmlFor="goal">Prospecting Goal</Label>
                <Textarea
                    id="goal"
                    placeholder="e.g. Find Head of Sales at SaaS companies with 50-200 employees..."
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    required
                />
                <p className="text-xs text-muted-foreground">What kind of leads are you looking for?</p>
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
                <p className="text-xs text-muted-foreground">Press Enter to add multiple job titles.</p>
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
