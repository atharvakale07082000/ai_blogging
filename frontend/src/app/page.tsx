"use client";

import React, { useState } from 'react';
import BlogForm from '../components/BlogForm';
import BlogDisplay from '../components/BlogDisplay';
import { generateBlog, BlogRequest, BlogResponse } from '../services/api';

export default function Home() {
    const [blog, setBlog] = useState<BlogResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async (data: BlogRequest) => {
        setIsLoading(true);
        setError(null);
        try {
            const result = await generateBlog(data);
            setBlog(result);
        } catch (err) {
            setError('Failed to generate blog. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
                        AI Blog Generator
                    </h1>
                    <p className="mt-5 max-w-xl mx-auto text-xl text-gray-500">
                        Generate SEO-optimized blog posts in seconds using the power of Gemini AI.
                    </p>
                </div>

                <BlogForm onSubmit={handleGenerate} isLoading={isLoading} />

                {error && (
                    <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-600">
                        {error}
                    </div>
                )}

                {blog && <BlogDisplay blog={blog} />}
            </div>
        </main>
    );
}
