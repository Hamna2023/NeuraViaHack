"use client";

import { useAuth } from "@/lib/authContext";
import Link from "next/link";
import { User, LogOut, LogIn, UserPlus, Settings } from "lucide-react";

export function UserNav() {
	const { user, signOut, loading } = useAuth();

	if (loading) {
		return (
			<div className="flex items-center space-x-2">
				<div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
			</div>
		);
	}

	if (user) {
		return (
			<div className="flex items-center space-x-4">
				<div className="flex items-center space-x-2">
					<User className="w-5 h-5 text-gray-600" />
					<div className="text-sm">
						<div className="text-gray-900 font-medium">{user.name}</div>
						<div className="text-gray-500 text-xs">{user.email}</div>
						{user.age && user.gender && (
							<div className="text-gray-400 text-xs">
								{user.age} years old • {user.gender}
							</div>
						)}
					</div>
				</div>
				<button
					onClick={signOut}
					className="flex items-center space-x-1 text-gray-600 hover:text-red-600 transition-colors">
					<LogOut className="w-4 h-4" />
					<span className="text-sm">Logout</span>
				</button>
			</div>
		);
	}

	return (
		<div className="flex items-center space-x-4">
			<Link href="/auth" className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors">
				<LogIn className="w-4 h-4" />
				<span className="text-sm">Login</span>
			</Link>
			<Link
				href="/auth?mode=register"
				className="flex items-center space-x-1 bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors">
				<UserPlus className="w-4 h-4" />
				<span className="text-sm">Sign Up</span>
			</Link>
		</div>
	);
}
