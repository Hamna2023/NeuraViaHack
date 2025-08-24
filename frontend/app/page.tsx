"use client";

import Link from "next/link";
import { useAuth } from "@/lib/authContext";
import { Brain, Activity, FileText, Headphones, MessageSquare, ArrowRight } from "lucide-react";

export default function Home() {
	const { user, loading } = useAuth();

	if (loading) {
		return (
			<div className="flex items-center justify-center h-screen">
				<div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
			</div>
		);
	}

	if (!user) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
				<div className="max-w-4xl mx-auto text-center space-y-8">
					<div className="space-y-4">
						<h1 className="text-5xl font-bold text-gray-900">
							Welcome to <span className="text-blue-600">NeuraVia</span>
						</h1>
						<p className="text-xl text-gray-600 max-w-2xl mx-auto">
							Your AI-powered neurological health companion. Get personalized assessments, hearing tests, and
							comprehensive medical reports.
						</p>
					</div>

					<div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
						<div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
							<Brain className="w-12 h-12 text-blue-600 mx-auto mb-4" />
							<h3 className="text-lg font-semibold text-gray-800 mb-2">AI Assessment</h3>
							<p className="text-gray-600 text-sm">
								Get comprehensive neurological evaluation with our AI medical attendant
							</p>
						</div>
						<div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
							<Headphones className="w-12 h-12 text-green-600 mx-auto mb-4" />
							<h3 className="text-lg font-semibold text-gray-800 mb-2">Hearing Tests</h3>
							<p className="text-gray-600 text-sm">
								Professional hearing assessment tools for comprehensive evaluation
							</p>
						</div>
						<div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
							<FileText className="w-12 h-12 text-purple-600 mx-auto mb-4" />
							<h3 className="text-lg font-semibold text-gray-800 mb-2">Smart Reports</h3>
							<p className="text-gray-600 text-sm">
								AI-generated medical reports with criticality ratings and recommendations
							</p>
						</div>
					</div>

					<div className="space-y-4">
						<Link
							href="/auth"
							className="inline-flex items-center bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors">
							Get Started
							<ArrowRight className="ml-2 w-5 h-5" />
						</Link>
						<p className="text-gray-500">
							Already have an account?{" "}
							<Link href="/auth" className="text-blue-600 hover:underline">
								Sign in here
							</Link>
						</p>
					</div>
				</div>
			</div>
		);
	}

	// User is authenticated - show dashboard
	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
			<div className="max-w-6xl mx-auto space-y-8">
				{/* Welcome Section */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-3xl font-bold text-gray-900">Welcome back, {user.name || "Patient"}! 👋</h1>
							<p className="text-gray-600 mt-2">Ready to continue your health journey? Choose your next step below.</p>
						</div>
						<div className="bg-blue-100 p-4 rounded-full">
							<Brain className="w-8 h-8 text-blue-600" />
						</div>
					</div>
				</div>

				{/* Quick Actions */}
				<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
					<Link
						href="/symptoms"
						className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 hover:shadow-xl transition-shadow group">
						<div className="flex items-center space-x-4">
							<div className="bg-blue-100 p-3 rounded-lg group-hover:bg-blue-200 transition-colors">
								<Activity className="w-6 h-6 text-blue-600" />
							</div>
							<div>
								<h3 className="font-semibold text-gray-800">Report Symptoms</h3>
								<p className="text-sm text-gray-600">Track your health concerns</p>
							</div>
						</div>
					</Link>

					<Link
						href="/chat"
						className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 hover:shadow-xl transition-shadow group">
						<div className="flex items-center space-x-4">
							<div className="bg-green-100 p-3 rounded-lg group-hover:bg-green-200 transition-colors">
								<MessageSquare className="w-6 h-6 text-green-600" />
							</div>
							<div>
								<h3 className="font-semibold text-gray-800">AI Assessment</h3>
								<p className="text-sm text-gray-600">Get medical evaluation</p>
							</div>
						</div>
					</Link>

					<Link
						href="/hearing"
						className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 hover:shadow-xl transition-shadow group">
						<div className="flex items-center space-x-4">
							<div className="bg-purple-100 p-3 rounded-lg group-hover:bg-purple-200 transition-colors">
								<Headphones className="w-6 h-6 text-purple-600" />
							</div>
							<div>
								<h3 className="font-semibold text-gray-800">Hearing Test</h3>
								<p className="text-sm text-gray-600">Assess hearing health</p>
							</div>
						</div>
					</Link>

					<Link
						href="/reports"
						className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 hover:shadow-xl transition-shadow group">
						<div className="flex items-center space-x-4">
							<div className="bg-orange-100 p-3 rounded-lg group-hover:bg-orange-200 transition-colors">
								<FileText className="w-6 h-6 text-orange-600" />
							</div>
							<div>
								<h3 className="font-semibold text-gray-800">View Reports</h3>
								<p className="text-sm text-gray-600">Check your assessments</p>
							</div>
						</div>
					</Link>
				</div>

				{/* Recommended Flow */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
					<h2 className="text-2xl font-bold text-gray-900 mb-6">Recommended Health Flow</h2>
					<div className="flex items-center justify-center space-x-4 text-gray-600">
						<div className="flex items-center space-x-2">
							<div className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
								1
							</div>
							<span>Report Symptoms</span>
						</div>
						<ArrowRight className="w-5 h-5" />
						<div className="flex items-center space-x-2">
							<div className="bg-green-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
								2
							</div>
							<span>AI Assessment</span>
						</div>
						<ArrowRight className="w-5 h-5" />
						<div className="flex items-center space-x-2">
							<div className="bg-purple-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
								3
							</div>
							<span>Hearing Test</span>
						</div>
						<ArrowRight className="w-5 h-5" />
						<div className="flex items-center space-x-2">
							<div className="bg-orange-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
								4
							</div>
							<span>Get Report</span>
						</div>
					</div>
					<div className="mt-6 text-center">
						<Link
							href="/symptoms"
							className="inline-flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
							Start Your Assessment
							<ArrowRight className="ml-2 w-4 h-4" />
						</Link>
					</div>
				</div>
				<p className="text-xs text-gray-400 mt-3">
				⚠️ Not a substitute for professional tests or medical advice.
				</p>


			</div>
		</div>
	);
}
