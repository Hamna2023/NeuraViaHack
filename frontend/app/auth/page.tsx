"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/authContext";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, EyeOff, Loader2 } from "lucide-react";

export default function AuthPage() {
	const [isLogin, setIsLogin] = useState(true);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [success, setSuccess] = useState<string | null>(null);
	const [showPassword, setShowPassword] = useState(false);
	const [formData, setFormData] = useState({
		email: "",
		password: "",
		name: "",
		age: "",
		gender: "",
	});


	const { user, signIn, signUp } = useAuth();
	const router = useRouter();
	const searchParams = useSearchParams();

	// Check URL params for mode
	useEffect(() => {
		const mode = searchParams?.get("mode") ?? null;

		if (mode === "register") {
			setIsLogin(false);
		}
	}, [searchParams]);

	// Check if user is already logged in
	useEffect(() => {
		if (user) {
			router.push("/");
		}
	}, [user, router]);

	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
		setFormData((prev) => ({
			...prev,
			[e.target.name]: e.target.value,
		}));
	};

	const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		setIsLoading(true);
		setError(null);
		setSuccess(null);

		try {
			if (isLogin) {
				const { error } = await signIn(formData.email, formData.password);
				if (error) {
					setError(error.message);
				} else {
					setSuccess("Login successful! Redirecting...");
					setTimeout(() => router.push("/"), 1000);
				}
			} else {
				// Validate required fields for signup
				if (!formData.name || !formData.age || !formData.gender) {
					setError("All fields are required for registration");
					return;
				}

				const { error } = await signUp(
					formData.email,
					formData.password,
					formData.name,
					parseInt(formData.age),
					formData.gender
				);

				if (error) {
					setError(error.message);
				} else {
					setSuccess("Account created successfully! Redirecting...");
					setTimeout(() => router.push("/"), 1000);
				}
			}
		} catch (error: any) {
			setError(error.message || "An unexpected error occurred");
		} finally {
			setIsLoading(false);
		}
	};

	const toggleMode = () => {
		setIsLogin(!isLogin);
		setError(null);
		setSuccess(null);
		setFormData({ email: "", password: "", name: "", age: "", gender: "" });
	};

	return (
		<div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-100 to-blue-200 p-4">
			<div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md space-y-6 border border-gray-200">
				<div className="text-center">
					<h2 className="text-3xl font-bold text-gray-800">{isLogin ? "Welcome Back" : "Create Account"}</h2>
					<p className="text-gray-600 mt-2">
						{isLogin ? "Sign in to your NeuraVia account" : "Join NeuraVia for personalized healthcare"}
					</p>
				</div>

				{/* Error/Success Messages */}
				{error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
				{success && (
					<div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">{success}</div>
				)}

				<form onSubmit={handleSubmit} className="space-y-5">
					{/* Email */}
					<div>
						<label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
						<input
							name="email"
							type="email"
							value={formData.email}
							onChange={handleInputChange}
							required
							className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
							placeholder="Enter your email"
							disabled={isLoading}
						/>
					</div>

					{/* Password */}
					<div>
						<label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
						<div className="relative">
							<input
								name="password"
								type={showPassword ? "text" : "password"}
								value={formData.password}
								onChange={handleInputChange}
								required
								minLength={6}
								className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
								placeholder="Enter your password"
								disabled={isLoading}
							/>
							<button
								type="button"
								onClick={() => setShowPassword(!showPassword)}
								className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700">
								{showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
							</button>
						</div>
					</div>

					{/* Extra fields only for Register */}
					{!isLogin && (
						<>
							{/* Name */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
								<input
									name="name"
									type="text"
									value={formData.name}
									onChange={handleInputChange}
									required
									className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
									placeholder="Enter your full name"
									disabled={isLoading}
								/>
							</div>

							<div className="grid grid-cols-2 gap-4">
								<div>
									<label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
									<input
										name="age"
										type="number"
										value={formData.age}
										onChange={handleInputChange}
										min="1"
										max="120"
										required
										className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
										placeholder="Age"
										disabled={isLoading}
									/>
								</div>

								<div>
									<label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
									<select
										name="gender"
										value={formData.gender}
										onChange={handleInputChange}
										required
										className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
										disabled={isLoading}>
										<option value="">Select...</option>
										<option value="female">Female</option>
										<option value="male">Male</option>
										<option value="nonbinary">Non-binary</option>
										<option value="prefer_not_say">Prefer not to say</option>
									</select>
								</div>
							</div>
						</>
					)}

					{/* Submit button */}
					<button
						type="submit"
						disabled={isLoading}
						className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium">
						{isLoading ? (
							<div className="flex items-center justify-center">
								<Loader2 className="w-5 h-5 animate-spin mr-2" />
								{isLogin ? "Signing In..." : "Creating Account..."}
							</div>
						) : isLogin ? (
							"Sign In"
						) : (
							"Create Account"
						)}
					</button>
				</form>

				{/* Switch mode */}
				<div className="text-center pt-4 border-t border-gray-200">
					<p className="text-sm text-gray-600">
						{isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
						<button
							type="button"
							onClick={toggleMode}
							className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
							disabled={isLoading}>
							{isLogin ? "Sign Up" : "Sign In"}
						</button>
					</p>
				</div>
			</div>
		</div>
	);
}
