import React from "react";

/**
 * Skeleton loader for the Profile page that mimics the actual profile card layout
 */
export default function ProfileSkeleton() {
    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-pulse">
            {/* Header Skeleton */}
            <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-[var(--bg-secondary)] rounded-full"></div>
                <div className="space-y-2">
                    <div className="h-6 w-32 bg-[var(--bg-secondary)] rounded"></div>
                    <div className="h-4 w-48 bg-[var(--bg-secondary)] rounded"></div>
                </div>
            </div>

            {/* Personal Details Card Skeleton */}
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] shadow-sm p-6">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
                    {/* Avatar Skeleton */}
                    <div className="w-24 h-24 rounded-full bg-[var(--bg-secondary)]"></div>

                    {/* Info Skeleton */}
                    <div className="flex-1 space-y-3 w-full">
                        <div className="h-6 w-40 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="h-4 w-24 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="flex gap-4 pt-2">
                            <div className="h-4 w-20 bg-[var(--bg-secondary)] rounded"></div>
                            <div className="h-4 w-20 bg-[var(--bg-secondary)] rounded"></div>
                            <div className="h-4 w-32 bg-[var(--bg-secondary)] rounded"></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Face Image Upload Card Skeleton */}
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] shadow-sm p-6 space-y-4">
                <div className="flex justify-between items-start">
                    <div className="space-y-2 flex-1">
                        <div className="h-5 w-32 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="h-3 w-64 bg-[var(--bg-secondary)] rounded"></div>
                    </div>
                    <div className="w-20 h-20 bg-[var(--bg-secondary)] rounded-md"></div>
                </div>
            </div>

            {/* Attendance Summary Card Skeleton */}
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] shadow-sm p-6 space-y-6">
                <div className="flex justify-between items-center">
                    <div className="h-5 w-40 bg-[var(--bg-secondary)] rounded"></div>
                    <div className="h-6 w-24 bg-[var(--bg-secondary)] rounded-full"></div>
                </div>

                <div className="space-y-2">
                    <div className="flex justify-between items-end mb-1">
                        <div className="h-4 w-24 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="h-6 w-16 bg-[var(--bg-secondary)] rounded"></div>
                    </div>
                    <div className="h-3 w-full bg-[var(--bg-secondary)] rounded-full"></div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                    <div className="space-y-2">
                        <div className="h-3 w-16 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="h-6 w-12 bg-[var(--bg-secondary)] rounded"></div>
                    </div>
                    <div className="space-y-2">
                        <div className="h-3 w-16 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="h-6 w-12 bg-[var(--bg-secondary)] rounded"></div>
                    </div>
                </div>

                <div className="h-12 w-full bg-[var(--bg-secondary)] rounded-xl"></div>
            </div>

            {/* Subjects Section Skeleton */}
            <div className="space-y-4">
                <div className="flex justify-between items-start">
                    <div className="space-y-2">
                        <div className="h-5 w-32 bg-[var(--bg-secondary)] rounded"></div>
                        <div className="h-3 w-48 bg-[var(--bg-secondary)] rounded"></div>
                    </div>
                    <div className="h-8 w-24 bg-[var(--bg-secondary)] rounded-lg"></div>
                </div>

                {/* Subject Cards Grid Skeleton */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <div
                            key={i}
                            className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4 space-y-3"
                        >
                            <div className="h-5 w-32 bg-[var(--bg-secondary)] rounded"></div>
                            <div className="h-3 w-full bg-[var(--bg-secondary)] rounded-full"></div>
                            <div className="flex justify-between">
                                <div className="h-4 w-16 bg-[var(--bg-secondary)] rounded"></div>
                                <div className="h-4 w-12 bg-[var(--bg-secondary)] rounded"></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
