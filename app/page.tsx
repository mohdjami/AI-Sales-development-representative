import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Bot, BrainCircuit, Calendar, Mail, MessageSquare } from 'lucide-react'
import { createClient } from "@/utils/supabase/server"
import Header from "@/components/Header"

export default async function LandingPage() {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user

  return (
    <div className="flex flex-col">
      <Header user={user} />
      {/* Hero Section */}
      <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
        <div className="px-4 md:px-6">
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl">
                AI-Powered Sales Development
              </h1>
              <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
                Automate your lead generation, personalize your outreach, and close more deals with our intelligent SDR platform.
              </p>
            </div>
            <div className="space-x-4">
              <Button asChild size="lg">
                <Link href="/login">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" size="lg">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="w-full py-12 md:py-24 border-t bg-muted/50">
        <div className="px-4 md:px-6">
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-bold">Data Collection</h3>
              <p className="text-muted-foreground">
                Intelligent scraping from LinkedIn and other sources to gather potential leads
              </p>
            </div>
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <BrainCircuit className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-bold">AI Research</h3>
              <p className="text-muted-foreground">
                Advanced lead scoring and context extraction using LangChain + Groq
              </p>
            </div>
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <Mail className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-bold">Smart Outreach</h3>
              <p className="text-muted-foreground">
                Personalized email drafting based on deep lead insights
              </p>
            </div>
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <Calendar className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-bold">Follow-Up & Scheduling</h3>
              <p className="text-muted-foreground">
                Automated response tracking and meeting scheduling
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="w-full py-12 md:py-24">
        <div className="px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">
                How It Works
              </h2>
              <p className="mx-auto max-w-[600px] text-muted-foreground md:text-xl">
                Our intelligent platform streamlines your sales development process
              </p>
            </div>
          </div>
          <div className="mx-auto grid max-w-5xl gap-6 py-12 lg:grid-cols-2 lg:gap-12">
            <div className="flex flex-col justify-center space-y-4">
              <ul className="grid gap-6">
                <li className="flex items-center space-x-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <Bot className="h-6 w-6 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xl font-bold">Smart Lead Discovery</h3>
                    <p className="text-muted-foreground">
                      AI-powered scraping and filtering of potential leads
                    </p>
                  </div>
                </li>
                <li className="flex items-center space-x-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <BrainCircuit className="h-6 w-6 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xl font-bold">Lead Qualification</h3>
                    <p className="text-muted-foreground">
                      Advanced scoring and ranking of prospects
                    </p>
                  </div>
                </li>
                <li className="flex items-center space-x-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <MessageSquare className="h-6 w-6 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xl font-bold">Personalized Outreach</h3>
                    <p className="text-muted-foreground">
                      AI-generated personalized emails and follow-ups
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="flex items-center justify-center">
              <div className="relative">
                {/* Add a product screenshot or illustration here */}
                <div className="h-[400px] w-[300px] rounded-xl border bg-background shadow-lg">
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full py-12 md:py-24 border-t">
        <div className="px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">
                Ready to Transform Your Sales Process?
              </h2>
              <p className="mx-auto max-w-[600px] text-muted-foreground md:text-xl">
                Join thousands of sales professionals using our AI-powered platform
              </p>
            </div>
            <div className="space-x-4">
              <Button asChild size="lg">
                <Link href="/login">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
