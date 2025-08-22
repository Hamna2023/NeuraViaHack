import Link from "next/link";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        {/* Navbar */}
        <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 px-6 py-4 shadow-sm">
  <div className="flex justify-between items-center">
    <h1 className="text-xl font-bold text-gray-800">NeuraVia</h1>
    <ul className="flex gap-6 text-gray-700">
      <li><a href="/" className="hover:text-blue-600">Home</a></li>
      <li><a href="/symptoms" className="hover:text-blue-600">Symptoms</a></li>
      <li><a href="/reports" className="hover:text-blue-600">Reports</a></li>
    </ul>
  </div>
</nav>




        {/* Page Content */}
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
