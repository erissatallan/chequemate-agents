// src/app/layout.js

export const metadata = {
  title: 'Good Speak API Documentation',
  description: 'Translate potentially harmful messages into polite alternatives.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head />
      <body style={{ fontFamily: 'Arial, sans-serif', margin: '0', background: '#fff' }}>
        {children}
      </body>
    </html>
  );
}
