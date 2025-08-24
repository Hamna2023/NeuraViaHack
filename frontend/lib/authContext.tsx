"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

// User interface matching the backend
interface User {
	id: string;
	email: string;
	name: string;
	age?: number;
	gender?: string;
	created_at?: string;
	updated_at?: string;
}

interface AuthContextType {
	user: User | null;
	loading: boolean;
	signIn: (email: string, password: string) => Promise<{ error: any }>;
	signUp: (email: string, password: string, name: string, age: number, gender: string) => Promise<{ error: any }>;
	signOut: () => Promise<void>;
	updateProfile: (updates: { name?: string; age?: number; gender?: string }) => Promise<{ error: any }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// API base URL - configurable for different environments
const API_BASE =
	typeof window !== "undefined"
		? window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
			? "http://localhost:8000"
			: window.location.origin
		: "http://localhost:8000";

export function AuthProvider({ children }: { children: ReactNode }) {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		// Check if user exists in localStorage (simple session persistence)
		const savedUser = localStorage.getItem("neuravia_user");
		if (savedUser) {
			try {
				const userData = JSON.parse(savedUser);
				setUser(userData);
			} catch (error) {
				console.error("Error parsing saved user:", error);
				localStorage.removeItem("neuravia_user");
			}
		}
		setLoading(false);
	}, []);

	const signIn = async (email: string, password: string) => {
		try {
			const response = await fetch(`${API_BASE}/api/users/login`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ email, password }),
			});

			const data = await response.json();

			if (!response.ok) {
				return { error: { message: data.detail || "Login failed" } };
			}

			// Store user in state and localStorage
			setUser(data);
			localStorage.setItem("neuravia_user", JSON.stringify(data));
			return { error: null };
		} catch (error: any) {
			console.error("Sign in error:", error);
			return { error: { message: error.message || "Sign in failed" } };
		}
	};

	const signUp = async (email: string, password: string, name: string, age: number, gender: string) => {
		try {
			const response = await fetch(`${API_BASE}/api/users/signup`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ email, password, name, age, gender }),
			});

			const data = await response.json();

			if (!response.ok) {
				return { error: { message: data.detail || "Sign up failed" } };
			}

			// Store user in state and localStorage
			setUser(data);
			localStorage.setItem("neuravia_user", JSON.stringify(data));
			return { error: null };
		} catch (error: any) {
			console.error("Sign up error:", error);
			return { error: { message: error.message || "Sign up failed" } };
		}
	};

	const signOut = async () => {
		try {
			setUser(null);
			localStorage.removeItem("neuravia_user");
		} catch (error) {
			console.error("Sign out error:", error);
		}
	};

	const updateProfile = async (updates: { name?: string; age?: number; gender?: string }) => {
		if (!user) {
			return { error: { message: "No user logged in" } };
		}

		try {
			const response = await fetch(`${API_BASE}/api/users/profile/${user.id}`, {
				method: "PUT",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(updates),
			});

			const data = await response.json();

			if (!response.ok) {
				return { error: { message: data.detail || "Profile update failed" } };
			}

			// Update user in state and localStorage
			const updatedUser = { ...user, ...data };
			setUser(updatedUser);
			localStorage.setItem("neuravia_user", JSON.stringify(updatedUser));
			return { error: null };
		} catch (error: any) {
			console.error("Profile update error:", error);
			return { error: { message: error.message || "Profile update failed" } };
		}
	};

	const value = {
		user,
		loading,
		signIn,
		signUp,
		signOut,
		updateProfile,
	};

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
	const context = useContext(AuthContext);
	if (context === undefined) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
}
