import type { Metadata } from 'next';
import './globals.css';
import ReactQueryProvider from '@/components/ReactQueryProvider';
import ThemeProvider from '@/components/ThemeProvider';

export const metadata: Metadata = {
  title: 'Smart POS — One Platform. Every Sale. Complete Control.',
  description: 'Premium multi-tenant SaaS POS and Retail Management System developed by XerexLabs.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <ReactQueryProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
