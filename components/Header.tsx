'use client';

import { User } from '@supabase/supabase-js';
import Link from 'next/link';
import { Building2, Menu, X, Sparkles } from 'lucide-react';
import UserAccountNav from './user-account-nav';
import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from './ui/button';

export default function Header({ user }: { user: User | null }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 w-full transition-all duration-300",
        scrolled
          ? "border-b bg-background/80 backdrop-blur-md shadow-sm"
          : "bg-transparent border-transparent"
      )}
    >
      <nav className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 group">
            <div className="p-1.5 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <Link href="/" className="text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              AI SDR
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:gap-8">
            {user ? (
              <>
                <Link
                  href="/prospects"
                  className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground hover:scale-105 active:scale-95"
                >
                  Prospects
                </Link>
                <Link
                  href="/dashboard"
                  className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground hover:scale-105 active:scale-95"
                >
                  Dashboard
                </Link>
                <UserAccountNav user={user} />
              </>
            ) : (
              <div className="flex items-center gap-4">
                <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                  Log in
                </Link>
                <Button asChild className="shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all hover:-translate-y-0.5">
                  <Link href="/login">Get Started</Link>
                </Button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button className="md:hidden" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        <div className={cn(
          'md:hidden overflow-hidden transition-all duration-300 ease-in-out',
          isMenuOpen ? 'max-h-60 opacity-100' : 'max-h-0 opacity-0'
        )}>
          <div className="space-y-4 px-2 pb-6 pt-2 bg-background/95 backdrop-blur-md rounded-b-xl border-b border-border/50 shadow-lg">
            {user ? (
              <>
                <Link
                  href="/prospects"
                  className="block py-2 text-foreground/80 transition-colors hover:text-foreground"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Prospects
                </Link>
                <Link
                  href="/dashboard"
                  className="block py-2 text-foreground/80 transition-colors hover:text-foreground"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Dashboard
                </Link>
              </>
            ) : (
              <div className="flex flex-col gap-3 pt-2">
                <Button variant="ghost" asChild className="w-full justify-start">
                  <Link href="/login">Log in</Link>
                </Button>
                <Button asChild className="w-full shadow-md">
                  <Link href="/login">Get Started</Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}
