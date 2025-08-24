import Link from "next/link";
import "./globals.css";
import { AuthProvider } from "@/lib/authContext";
import { UserNav } from "@/components/UserNav";

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en">
			<body className="min-h-screen bg-gray-50 text-gray-900">
				<AuthProvider>
					{/* Navbar */}
					<nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 px-6 py-4 shadow-sm sticky top-0 z-50">
						<div className="flex justify-between items-center">
							<Link href="/" className="text-xl font-bold text-gray-800 hover:text-blue-600 transition-colors">
								NeuraVia
							</Link>
							<ul className="flex gap-6 text-gray-700">
								<li>
									<Link href="/" className="hover:text-blue-600 transition-colors">
										Home
									</Link>
								</li>
								<li>
									<Link href="/chat" className="hover:text-blue-600 transition-colors">
										Medical Assessment
									</Link>
								</li>
								<li>
									<Link href="/reports" className="hover:text-blue-600 transition-colors">
										Reports
									</Link>
								</li>
								<li>
									<Link href="/symptoms" className="hover:text-blue-600 transition-colors">
										Symptoms
									</Link>
								</li>
								<li>
									<Link href="/hearing" className="hover:text-blue-600 transition-colors">
										Hearing Test
									</Link>
								</li>
							</ul>
							<UserNav />
						</div>
					</nav>

					{/* Page Content */}
					<main className="flex-1">{children}</main>
				</AuthProvider>
			</body>
		</html>
	);
}
