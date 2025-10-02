// frontend/src/app/layout.js
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import Layout from '@/components/layout/Layout';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

// Separate metadata export
export const metadata = {
  title: 'Indian Court Case & Cause List Tracker',
  description: 'Track Indian court cases and daily cause lists from official eCourts portals',
  keywords: 'Indian courts, case tracking, cause list, eCourts, legal, judiciary',
  authors: [{ name: 'Court Tracker Team' }],
};

// Separate viewport export (as required by Next.js 15)
export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Layout>
          {children}
        </Layout>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4ade80',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </body>
    </html>
  );
}
