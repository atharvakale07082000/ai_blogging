import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "AI Blog Generator",
    description: "Generate SEO-optimized blog posts with AI",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className="antialiased">
                {children}
            </body>
        </html>
    );
}
