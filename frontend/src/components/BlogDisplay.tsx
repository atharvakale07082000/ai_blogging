import React from 'react';
import { BlogResponse } from '../services/api';
import ReactMarkdown from 'react-markdown';

interface BlogDisplayProps {
    blog: BlogResponse;
}

const BlogDisplay: React.FC<BlogDisplayProps> = ({ blog }) => {
    return (
        <div className="bg-white p-8 rounded-lg shadow-md mt-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{blog.title}</h1>

            <div className="mb-6 p-4 bg-gray-50 rounded-md">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">SEO Metadata</h3>
                <p className="text-sm text-gray-600 mb-2"><span className="font-medium">Description:</span> {blog.seo_metadata.meta_description}</p>
                <div className="flex flex-wrap gap-2">
                    {blog.seo_metadata.tags.map((tag, index) => (
                        <span key={index} className="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded-full">
                            #{tag}
                        </span>
                    ))}
                </div>
            </div>

            <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Outline</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                    {blog.outline.map((item, index) => (
                        <li key={index}>{item}</li>
                    ))}
                </ul>
            </div>

            <div className="prose max-w-none">
                <ReactMarkdown>{blog.content}</ReactMarkdown>
            </div>
        </div>
    );
};

export default BlogDisplay;
