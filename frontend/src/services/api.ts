import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface BlogRequest {
    topic: string;
    tone: string;
    keywords: string[];
    length: string;
    target_audience: string;
}

export interface BlogResponse {
    title: string;
    outline: string[];
    content: string;
    seo_metadata: {
        meta_description: string;
        tags: string[];
    };
}

export const generateBlog = async (data: BlogRequest): Promise<BlogResponse> => {
    try {
        const response = await axios.post<BlogResponse>(`${API_URL}/generate-blog`, data);
        return response.data;
    } catch (error) {
        console.error('Error generating blog:', error);
        throw error;
    }
};
