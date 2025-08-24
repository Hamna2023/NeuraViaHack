"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/authContext";
import { useRouter } from "next/navigation";
import {
	FileText,
	Activity,
	Headphones,
	Brain,
	Calendar,
	Download,
	Eye,
	AlertTriangle,
	CheckCircle,
	Clock,
} from "lucide-react";
import Link from "next/link";

interface Symptom {
	id: string;
	symptom_name: string;
	severity: number;
	description: string;
	duration_days: number;
	created_at: string;
}

interface HearingTest {
	id: string;
	test_date: string;
	left_ear_score: number;
	right_ear_score: number;
	overall_score: number;
	test_type: string;
	notes: string;
}

interface PatientReport {
	id: string;
	report_title: string;
	executive_summary: string;
	symptom_analysis: string;
	risk_assessment: string;
	hearing_assessment_summary: string;
	recommendations: string;
	follow_up_actions: string;
	assessment_stage: string;
	is_complete: boolean;
	generated_at: string;
	created_at: string;
}

export default function ReportsPage() {
	const { user } = useAuth();
	const router = useRouter();
	const [symptoms, setSymptoms] = useState<Symptom[]>([]);
	const [hearingTests, setHearingTests] = useState<HearingTest[]>([]);
	const [patientReports, setPatientReports] = useState<PatientReport[]>([]);
	const [loading, setLoading] = useState(true);
	const [activeTab, setActiveTab] = useState<"overview" | "symptoms" | "hearing" | "reports">("overview");

	// Redirect if not authenticated
	useEffect(() => {
		if (!user) {
			router.push("/auth");
		}
	}, [user, router]);

	// Load user data
	useEffect(() => {
		if (user) {
			loadUserData();
		}
	}, [user]);

	const loadUserData = async () => {
		setLoading(true);
		try {
			// Load symptoms
			const symptomsResponse = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/symptoms/user/${user?.id}`
			);
			if (symptomsResponse.ok) {
				const symptomsData = await symptomsResponse.json();
				setSymptoms(symptomsData);
			}

			// Load hearing tests
			const hearingResponse = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/hearing/user/${user?.id}`
			);
			if (hearingResponse.ok) {
				const hearingData = await hearingResponse.json();
				setHearingTests(hearingData);
			}

			// Load patient reports
			const reportsResponse = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/reports/user/${user?.id}`
			);
			if (reportsResponse.ok) {
				const reportsData = await reportsResponse.json();
				setPatientReports(reportsData);
			}
		} catch (error) {
			console.error("Error loading user data:", error);
		} finally {
			setLoading(false);
		}
	};

	const getSeverityColor = (severity: number) => {
		if (severity <= 3) return "text-green-600 bg-green-100";
		if (severity <= 6) return "text-yellow-600 bg-yellow-100";
		if (severity <= 8) return "text-orange-600 bg-orange-100";
		return "text-red-600 bg-red-100";
	};

	const getSeverityLabel = (severity: number) => {
		if (severity <= 3) return "Mild";
		if (severity <= 6) return "Moderate";
		if (severity <= 8) return "Severe";
		return "Very Severe";
	};

	const getHearingScoreColor = (score: number) => {
		if (score >= 80) return "text-green-600 bg-green-100";
		if (score >= 60) return "text-yellow-600 bg-yellow-100";
		if (score >= 40) return "text-orange-600 bg-orange-100";
		return "text-red-600 bg-red-100";
	};

	const getHearingScoreLabel = (score: number) => {
		if (score >= 80) return "Excellent";
		if (score >= 60) return "Good";
		if (score >= 40) return "Fair";
		return "Poor";
	};

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString("en-US", {
			year: "numeric",
			month: "long",
			day: "numeric",
		});
	};

	if (!user) {
		return null; // Will redirect
	}

	if (loading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
				<div className="text-center">
					<div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
					<p className="text-gray-600">Loading your health reports...</p>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
			<div className="max-w-7xl mx-auto">
				{/* Header */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-4xl font-bold text-gray-900 mb-2">Health Reports</h1>
							<p className="text-gray-600">
								Comprehensive overview of your health assessments, symptoms, and recommendations
							</p>
						</div>
						<div className="bg-blue-100 p-4 rounded-full">
							<FileText className="w-8 h-8 text-blue-600" />
						</div>
					</div>
				</div>

				{/* Navigation Tabs */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-2 mb-6">
					<div className="flex space-x-1">
						{[
							{ id: "overview", label: "Overview", icon: Eye },
							{ id: "symptoms", label: "Symptoms", icon: Activity },
							{ id: "hearing", label: "Hearing Tests", icon: Headphones },
							{ id: "reports", label: "AI Reports", icon: Brain },
						].map((tab) => {
							const Icon = tab.icon;
							return (
								<button
									key={tab.id}
									onClick={() => setActiveTab(tab.id as any)}
									className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-xl transition-colors ${
										activeTab === tab.id ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
									}`}>
									<Icon className="w-4 h-4" />
									<span className="font-medium">{tab.label}</span>
								</button>
							);
						})}
					</div>
				</div>

				{/* Tab Content */}
				<div className="space-y-6">
					{/* Overview Tab */}
					{activeTab === "overview" && (
						<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
							{/* Symptoms Summary */}
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<div className="flex items-center space-x-3 mb-4">
									<div className="bg-red-100 p-3 rounded-full">
										<Activity className="w-6 h-6 text-red-600" />
									</div>
									<div>
										<p className="text-sm text-gray-600">Active Symptoms</p>
										<p className="text-2xl font-bold text-gray-900">{symptoms.length}</p>
									</div>
								</div>
								{symptoms.length > 0 && (
									<div className="space-y-2">
										{symptoms.slice(0, 3).map((symptom) => (
											<div key={symptom.id} className="flex items-center justify-between text-sm">
												<span className="text-gray-600 truncate">{symptom.symptom_name}</span>
												<span
													className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(
														symptom.severity
													)}`}>
													{getSeverityLabel(symptom.severity)}
												</span>
											</div>
										))}
										{symptoms.length > 3 && (
											<p className="text-xs text-gray-500">+{symptoms.length - 3} more symptoms</p>
										)}
									</div>
								)}
							</div>

							{/* Hearing Tests Summary */}
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<div className="flex items-center space-x-3 mb-4">
									<div className="bg-purple-100 p-3 rounded-full">
										<Headphones className="w-6 h-6 text-purple-600" />
									</div>
									<div>
										<p className="text-sm text-gray-600">Hearing Tests</p>
										<p className="text-2xl font-bold text-gray-900">{hearingTests.length}</p>
									</div>
								</div>
								{hearingTests.length > 0 && (
									<div className="space-y-2">
										<div className="text-sm">
											<span className="text-gray-600">Latest Score: </span>
											<span
												className={`px-2 py-1 rounded-full text-xs font-medium ${getHearingScoreColor(
													hearingTests[0].overall_score
												)}`}>
												{hearingTests[0].overall_score}% - {getHearingScoreLabel(hearingTests[0].overall_score)}
											</span>
										</div>
										<p className="text-xs text-gray-500">Last test: {formatDate(hearingTests[0].test_date)}</p>
									</div>
								)}
							</div>

							{/* AI Reports Summary */}
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<div className="flex items-center space-x-3 mb-4">
									<div className="bg-green-100 p-3 rounded-full">
										<Brain className="w-6 h-6 text-green-600" />
									</div>
									<div>
										<p className="text-sm text-gray-600">AI Assessments</p>
										<p className="text-2xl font-bold text-gray-900">{patientReports.length}</p>
									</div>
								</div>
								{patientReports.length > 0 && (
									<div className="space-y-2">
										<div className="text-sm">
											<span className="text-gray-600">Status: </span>
											<span
												className={`px-2 py-1 rounded-full text-xs font-medium ${
													patientReports[0].is_complete
														? "text-green-600 bg-green-100"
														: "text-yellow-600 bg-yellow-100"
												}`}>
												{patientReports[0].is_complete ? "Complete" : "In Progress"}
											</span>
										</div>
										<p className="text-xs text-gray-500">Last updated: {formatDate(patientReports[0].created_at)}</p>
									</div>
								)}
							</div>

							{/* Quick Actions */}
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<div className="flex items-center space-x-3 mb-4">
									<div className="bg-blue-100 p-3 rounded-full">
										<FileText className="w-6 h-6 text-blue-600" />
									</div>
									<div>
										<p className="text-sm text-gray-600">Quick Actions</p>
										<p className="text-lg font-semibold text-gray-900">Get Started</p>
									</div>
								</div>
								<div className="space-y-2">
									<Link
										href="/symptoms"
										className="block w-full text-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm">
										Report Symptoms
									</Link>
									<Link
										href="/chat"
										className="block w-full text-center bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm">
										Start AI Assessment
									</Link>
									<Link
										href="/hearing"
										className="block w-full text-center bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm">
										Take Hearing Test
									</Link>
								</div>
							</div>
						</div>
					)}

					{/* Symptoms Tab */}
					{activeTab === "symptoms" && (
						<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
							<div className="flex items-center justify-between mb-6">
								<h2 className="text-2xl font-bold text-gray-900">Symptom History</h2>
								<Link
									href="/symptoms"
									className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
									<Activity className="w-4 h-4" />
									<span>Add Symptoms</span>
								</Link>
							</div>

							{symptoms.length === 0 ? (
								<div className="text-center py-12">
									<Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
									<h3 className="text-lg font-semibold text-gray-600 mb-2">No Symptoms Recorded</h3>
									<p className="text-gray-500 mb-4">Start tracking your health by reporting symptoms</p>
									<Link
										href="/symptoms"
										className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
										Report Your First Symptom
									</Link>
								</div>
							) : (
								<div className="space-y-4">
									{symptoms.map((symptom) => (
										<div
											key={symptom.id}
											className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
											<div className="flex items-center justify-between mb-2">
												<h3 className="text-lg font-semibold text-gray-800">{symptom.symptom_name}</h3>
												<span
													className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(
														symptom.severity
													)}`}>
													{getSeverityLabel(symptom.severity)}
												</span>
											</div>
											<p className="text-gray-600 mb-3">{symptom.description}</p>
											<div className="flex items-center justify-between text-sm text-gray-500">
												<span>Duration: {symptom.duration_days} days</span>
												<span>Reported: {formatDate(symptom.created_at)}</span>
											</div>
										</div>
									))}
								</div>
							)}
						</div>
					)}

					{/* Hearing Tests Tab */}
					{activeTab === "hearing" && (
						<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
							<div className="flex items-center justify-between mb-6">
								<h2 className="text-2xl font-bold text-gray-900">Hearing Test Results</h2>
								<Link
									href="/hearing"
									className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2">
									<Headphones className="w-4 h-4" />
									<span>Take New Test</span>
								</Link>
							</div>

							{hearingTests.length === 0 ? (
								<div className="text-center py-12">
									<Headphones className="w-16 h-16 text-gray-300 mx-auto mb-4" />
									<h3 className="text-lg font-semibold text-gray-600 mb-2">No Hearing Tests Taken</h3>
									<p className="text-gray-500 mb-4">Complete a hearing assessment to track your auditory health</p>
									<Link
										href="/hearing"
										className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors">
										Start Hearing Test
									</Link>
								</div>
							) : (
								<div className="space-y-6">
									{hearingTests.map((test) => (
										<div
											key={test.id}
											className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
											<div className="grid md:grid-cols-4 gap-6">
												<div className="text-center">
													<p className="text-sm text-gray-600 mb-1">Left Ear</p>
													<p className={`text-2xl font-bold ${getHearingScoreColor(test.left_ear_score)}`}>
														{test.left_ear_score}%
													</p>
												</div>
												<div className="text-center">
													<p className="text-sm text-gray-600 mb-1">Right Ear</p>
													<p className={`text-2xl font-bold ${getHearingScoreColor(test.right_ear_score)}`}>
														{test.right_ear_score}%
													</p>
												</div>
												<div className="text-center">
													<p className="text-sm text-gray-600 mb-1">Overall</p>
													<p className={`text-2xl font-bold ${getHearingScoreColor(test.overall_score)}`}>
														{test.overall_score}%
													</p>
												</div>
												<div className="text-center">
													<p className="text-sm text-gray-600 mb-1">Test Date</p>
													<p className="text-sm font-medium text-gray-800">{formatDate(test.test_date)}</p>
												</div>
											</div>
											{test.notes && (
												<div className="mt-4 pt-4 border-t border-gray-200">
													<p className="text-sm text-gray-600">{test.notes}</p>
												</div>
											)}
										</div>
									))}
								</div>
							)}
						</div>
					)}

					{/* AI Reports Tab */}
					{activeTab === "reports" && (
						<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
							<div className="flex items-center justify-between mb-6">
								<h2 className="text-2xl font-bold text-gray-900">AI Medical Reports</h2>
								<Link
									href="/chat"
									className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
									<Brain className="w-4 h-4" />
									<span>Start New Assessment</span>
								</Link>
							</div>

							{patientReports.length === 0 ? (
								<div className="text-center py-12">
									<Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
									<h3 className="text-lg font-semibold text-gray-600 mb-2">No AI Reports Generated</h3>
									<p className="text-gray-600 mb-6">
										Complete an AI medical assessment to get your personalized report. The assessment will guide you
										through a series of questions to understand your symptoms and health concerns.
									</p>
									<div className="space-y-3">
										<Link
											href="/chat"
											className="block w-full max-w-md mx-auto bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors">
											Start AI Assessment
										</Link>
										<p className="text-sm text-gray-500">The assessment typically takes 5-10 minutes and covers:</p>
										<div className="max-w-md mx-auto text-left text-sm text-gray-600 space-y-1">
											<div className="flex items-center space-x-2">
												<div className="w-2 h-2 bg-green-500 rounded-full"></div>
												<span>Symptom evaluation</span>
											</div>
											<div className="flex items-center space-x-2">
												<div className="w-2 h-2 bg-green-500 rounded-full"></div>
												<span>Medical history review</span>
											</div>
											<div className="flex items-center space-x-2">
												<div className="w-2 h-2 bg-green-500 rounded-full"></div>
												<span>Risk factor assessment</span>
											</div>
											<div className="flex items-center space-x-2">
												<div className="w-2 h-2 bg-green-500 rounded-full"></div>
												<span>Personalized recommendations</span>
											</div>
										</div>
									</div>
								</div>
							) : (
								<div className="space-y-6">
									{/* Report Generation Status */}
									{patientReports.some((r) => !r.is_complete) && (
										<div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
											<div className="flex items-center space-x-3">
												<Clock className="w-5 h-5 text-yellow-600" />
												<div>
													<h4 className="font-medium text-yellow-800">Assessment In Progress</h4>
													<p className="text-sm text-yellow-700">
														Some of your assessments are still in progress. Complete them to generate comprehensive
														reports.
													</p>
												</div>
											</div>
										</div>
									)}

									{patientReports.map((report) => (
										<div
											key={report.id}
											className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
											<div className="flex items-center justify-between mb-4">
												<h3 className="text-xl font-semibold text-gray-800">{report.report_title}</h3>
												<div className="flex items-center space-x-2">
													<span
														className={`px-3 py-1 rounded-full text-sm font-medium ${
															report.is_complete ? "text-green-600 bg-green-100" : "text-yellow-600 bg-yellow-100"
														}`}>
														{report.is_complete ? (
															<span className="flex items-center space-x-1">
																<CheckCircle className="w-4 h-4" />
																<span>Complete</span>
															</span>
														) : (
															<span className="flex items-center space-x-1">
																<Clock className="w-4 h-4" />
																<span>In Progress</span>
															</span>
														)}
													</span>
												</div>
											</div>

											<div className="grid md:grid-cols-2 gap-6 mb-4">
												{report.executive_summary && (
													<div>
														<h4 className="font-semibold text-gray-700 mb-2">Executive Summary</h4>
														<p className="text-gray-600 text-sm">{report.executive_summary}</p>
													</div>
												)}
												{report.recommendations && (
													<div>
														<h4 className="font-semibold text-gray-700 mb-2">Recommendations</h4>
														<p className="text-gray-600 text-sm">{report.recommendations}</p>
													</div>
												)}
											</div>

											<div className="flex items-center justify-between text-sm text-gray-500">
												<span>Generated: {formatDate(report.generated_at)}</span>
												<span>Stage: {report.assessment_stage}</span>
											</div>

											{/* Action Buttons */}
											{!report.is_complete && (
												<div className="mt-4 pt-4 border-t border-gray-200">
													<Link
														href="/chat"
														className="inline-flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
														<Brain className="w-4 h-4" />
														<span>Continue Assessment</span>
													</Link>
												</div>
											)}
										</div>
									))}
								</div>
							)}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
