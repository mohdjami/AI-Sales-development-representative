'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
    LayoutDashboard,
    Users,
    Mail,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Menu,
    X,
    Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState, useEffect } from 'react';
import { createClient } from '@/utils/supabase/client';
import { useRouter } from 'next/navigation';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface SidebarProps {
    user: any;
}

export function AppSidebar({ user }: SidebarProps) {
    const pathname = usePathname();
    const router = useRouter();
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const supabase = createClient();

    const routes = [
        {
            label: 'Dashboard',
            icon: LayoutDashboard,
            href: '/dashboard',
            color: 'text-sky-500',
        },
        {
            label: 'Prospects',
            icon: Users,
            href: '/prospects',
            color: 'text-violet-500',
        },
        {
            label: 'Emails',
            icon: Mail,
            href: '/dashboard?tab=follow-ups', // Temporarily query param or route
            color: 'text-pink-700',
        },
        {
            label: 'Settings',
            icon: Settings,
            href: '/settings',
            color: 'text-gray-500',
        },
    ];

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.refresh();
    };

    return (
        <>
            {/* Mobile Trigger */}
            <div className="lg:hidden fixed top-4 left-4 z-50">
                <Button variant="outline" size="icon" onClick={() => setMobileOpen(!mobileOpen)} className="bg-background/80 backdrop-blur-sm shadow-sm">
                    {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
                </Button>
            </div>

            {/* Sidebar */}
            <div
                className={cn(
                    "fixed inset-y-0 left-0 z-40 flex flex-col h-full transition-all duration-300 ease-in-out border-r border-sidebar-border bg-sidebar/95 backdrop-blur-xl supports-[backdrop-filter]:bg-sidebar/60",
                    collapsed ? "w-[80px]" : "w-72",
                    mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
                )}
            >
                <div className="flex items-center justify-between p-6">
                    <Link href="/dashboard" className={cn("flex items-center gap-2 overflow-hidden transition-all", collapsed && "justify-center w-full")}>
                        <div className="h-8 w-8 min-w-8 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-lg shadow-primary/20">
                            <Sparkles className="h-4 w-4 text-primary-foreground" />
                        </div>
                        <div className={cn("transition-all duration-300 overflow-hidden", collapsed ? "w-0 opacity-0" : "w-auto opacity-100")}>
                            <span className="text-xl font-bold bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent whitespace-nowrap">
                                AI SDR
                            </span>
                        </div>
                    </Link>
                    <Button
                        variant="ghost"
                        size="icon"
                        className={cn("hidden lg:flex h-6 w-6 rounded-full hover:bg-sidebar-accent", collapsed && "hidden")}
                        onClick={() => setCollapsed(!collapsed)}
                    >
                        <ChevronLeft className="h-3 w-3" />
                    </Button>
                </div>

                {collapsed && (
                    <div className="hidden lg:flex justify-center mb-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 rounded-full hover:bg-sidebar-accent"
                            onClick={() => setCollapsed(!collapsed)}
                        >
                            <ChevronRight className="h-3 w-3" />
                        </Button>
                    </div>
                )}

                <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                    {routes.map((route) => (
                        <Link
                            key={route.href}
                            href={route.href}
                            className={cn(
                                "group flex items-center p-3 text-sm font-medium rounded-lg transition-all relative overflow-hidden",
                                pathname === route.href || (route.href.includes('?') && pathname === route.href.split('?')[0])
                                    ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                                    : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground",
                                collapsed && "justify-center"
                            )}
                            title={collapsed ? route.label : undefined}
                        >
                            {pathname === route.href && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full" />
                            )}
                            <route.icon className={cn("h-5 w-5 transition-colors", route.color, collapsed ? "mr-0" : "mr-3")} />
                            <span className={cn("transition-all duration-300 overflow-hidden whitespace-nowrap", collapsed ? "w-0 opacity-0" : "w-auto opacity-100")}>
                                {route.label}
                            </span>
                        </Link>
                    ))}
                </div>

                <div className="p-4 border-t border-sidebar-border bg-sidebar-accent/10">
                    <div className={cn("flex items-center gap-3 transition-all", collapsed && "justify-center")}>
                        <Avatar className="h-9 w-9 border border-border/50">
                            <AvatarImage src={user?.user_metadata?.avatar_url} />
                            <AvatarFallback className="bg-primary/10 text-primary font-bold">{user?.email?.charAt(0).toUpperCase()}</AvatarFallback>
                        </Avatar>
                        <div className={cn("flex flex-col overflow-hidden transition-all duration-300", collapsed ? "w-0 opacity-0" : "w-auto opacity-100")}>
                            <span className="text-sm font-medium truncate text-foreground">{user?.email}</span>
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Sparkles className="h-3 w-3 text-amber-500" />
                                Pro Plan
                            </span>
                        </div>
                    </div>
                    <Button
                        variant="ghost"
                        className={cn(
                            "w-full mt-4 justify-start text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors",
                            collapsed ? "justify-center px-0" : "px-3"
                        )}
                        onClick={handleLogout}
                        title={collapsed ? "Logout" : undefined}
                    >
                        <LogOut className={cn("h-4 w-4", !collapsed && "mr-2")} />
                        <span className={cn("transition-all duration-300 overflow-hidden whitespace-nowrap", collapsed ? "w-0 opacity-0" : "w-auto opacity-100")}>
                            Logout
                        </span>
                    </Button>
                </div>
            </div>

            {/* Mobile Overlay */}
            {mobileOpen && (
                <div
                    className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden animate-in fade-in duration-200"
                    onClick={() => setMobileOpen(false)}
                />
            )}
        </>
    );
}
