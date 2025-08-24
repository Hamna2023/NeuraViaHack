"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/authContext";
import { useRouter } from "next/navigation";
import { Trash2, Plus, Save, ArrowRight, AlertCircle } from "lucide-react";
import Link from "next/link";

type Symptom = {
	id?: string;
	name: string;
	severity: number;
	description: string;
	duration_days?: number;
};

export default function SymptomForm() {
	const { user } = useAuth();
	const router = useRouter();
	const [symptoms, setSymptoms] = useState<Symptom[]>([{ name: "", severity: 5, description: "", duration_days: 1 }]);
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

	// Redirect if not authenticated
	useEffect(() => {
		if (!user) {
			router.push("/auth");
		}
	}, [user, router]);

	// Handle updating a field in one symptom
	const handleChange = (index: number, field: keyof Symptom, value: string | number) => {
		const updated = [...symptoms];
		updated[index][field] = value as never;
		setSymptoms(updated);
	};

	// Add new empty symptom
	const addSymptom = () => {
		setSymptoms([...symptoms, { name: "", severity: 5, description: "", duration_days: 1 }]);
	};

	// Remove a symptom
	const removeSymptom = (index: number) => {
		if (symptoms.length > 1) {
			const updated = symptoms.filter((_, i) => i !== index);
			setSymptoms(updated);
		}
	};

	// Submit symptoms to backend
	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!user) return;

		setIsSubmitting(true);
		setMessage(null);

		try {
			// Filter out empty symptoms
			const validSymptoms = symptoms.filter((s) => s.name.trim() !== "");

			if (validSymptoms.length === 0) {
				setMessage({ type: "error", text: "Please add at least one symptom" });
				return;
			}

			// Prepare symptoms data
			const symptomsData = validSymptoms.map((symptom) => ({
				user_id: user.id,
				symptom_name: symptom.name.trim(),
				severity: symptom.severity,
				description: symptom.description.trim(),
				duration_days: symptom.duration_days || 1,
			}));

			// Submit to backend
			const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/symptoms/batch`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ symptoms: symptomsData }),
			});

			if (response.ok) {
				setMessage({ type: "success", text: "Symptoms saved successfully!" });
				// Clear form after successful submission
				setTimeout(() => {
					setSymptoms([{ name: "", severity: 5, description: "", duration_days: 1 }]);
				}, 2000);
			} else {
				const errorData = await response.json();
				setMessage({ type: "error", text: errorData.detail || "Failed to save symptoms" });
			}
		} catch (error) {
			console.error("Error saving symptoms:", error);
			setMessage({ type: "error", text: "Network error. Please try again." });
		} finally {
			setIsSubmitting(false);
		}
	};

	if (!user) {
		return null; // Will redirect
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
			<div className="max-w-4xl mx-auto">
				{/* Header */}
				<div className="text-center mb-8">
					<div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-white mb-6">
						<h1 className="text-4xl font-bold mb-4">Report Your Symptoms</h1>
						<p className="text-xl text-blue-100 max-w-2xl mx-auto">
							Help us understand your health concerns. Be as detailed as possible for better assessment.
						</p>
					</div>

					{/* Assessment Flow Indicator */}
					<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 max-w-4xl mx-auto">
						<h2 className="text-lg font-semibold text-gray-800 mb-4">Assessment Flow</h2>
						<div className="flex items-center justify-center space-x-4 text-gray-600">
							<div className="flex items-center space-x-2">
								<div className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
									1
								</div>
								<span className="font-medium">Report Symptoms</span>
							</div>
							<ArrowRight className="w-5 h-5" />
							<div className="flex items-center space-x-2">
								<div className="bg-green-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
									2
								</div>
								<span className="font-medium">AI Assessment</span>
							</div>
							<ArrowRight className="w-5 h-5" />
							<div className="flex items-center space-x-2">
								<div className="bg-purple-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
									3
								</div>
								<span className="font-medium">Hearing Test</span>
							</div>
							<ArrowRight className="w-5 h-5" />
							<div className="flex items-center space-x-2">
								<div className="bg-orange-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
									4
								</div>
								<span className="font-medium">Get Report</span>
							</div>
						</div>
					</div>
				</div>

				{/* Message Display */}
				{message && (
					<div
						className={`mb-6 p-4 rounded-lg border ${
							message.type === "success"
								? "bg-green-50 border-green-200 text-green-700"
								: "bg-red-50 border-red-200 text-red-700"
						}`}>
						<div className="flex items-center space-x-2">
							{message.type === "success" ? <Save className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
							<span>{message.text}</span>
						</div>
					</div>
				)}

				{/* Symptoms Form */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
					<form onSubmit={handleSubmit} className="space-y-6">
						{symptoms.map((symptom, index) => (
							<div
								key={index}
								className="bg-white border border-gray-200 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 relative overflow-hidden">
								{/* Header with gradient background */}
								<div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-4 text-white">
									<div className="flex items-center justify-between">
										<div className="flex items-center space-x-3">
											<div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
												<span className="text-sm font-bold">{index + 1}</span>
											</div>
											<h3 className="text-lg font-semibold">Symptom {index + 1}</h3>
										</div>
										{symptoms.length > 1 && (
											<button
												type="button"
												onClick={() => removeSymptom(index)}
												className="text-white hover:text-red-200 transition-colors p-2 rounded-full hover:bg-white/20"
												aria-label="Remove symptom">
												<Trash2 size={20} />
											</button>
										)}
									</div>
								</div>

								{/* Symptom Content */}
								<div className="p-6">
									<div className="grid md:grid-cols-2 gap-4 mb-4">
										{/* Symptom Name */}
										<div>
											<label className="block text-sm font-medium text-gray-700 mb-2">Symptom Name *</label>
											<input
												type="text"
												value={symptom.name}
												onChange={(e) => handleChange(index, "name", e.target.value)}
												className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
												placeholder="e.g., Headache, Dizziness, Nausea"
												required
											/>
										</div>

										{/* Duration */}
										<div>
											<label className="block text-sm font-medium text-gray-700 mb-2">Duration (days)</label>
											<input
												type="number"
												value={symptom.duration_days}
												onChange={(e) => handleChange(index, "duration_days", parseInt(e.target.value) || 1)}
												min="1"
												max="365"
												className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
												placeholder="1"
											/>
										</div>
									</div>

									{/* Severity */}
									<div className="mb-4">
										<label className="block text-sm font-medium text-gray-700 mb-3">Severity Level *</label>
										<div className="flex justify-between gap-2">
											{[...Array(10)].map((_, i) => {
												const value = i + 1;
												const bgColor =
													value <= 3
														? "bg-green-400 hover:bg-green-500"
														: value <= 6
														? "bg-yellow-400 hover:bg-yellow-500"
														: value <= 8
														? "bg-orange-400 hover:bg-orange-500"
														: "bg-red-500 hover:bg-red-600";

												return (
													<button
														key={value}
														type="button"
														onClick={() => handleChange(index, "severity", value)}
														className={`flex-1 py-3 rounded-lg text-white font-medium transition-all duration-200 
                                    ${bgColor} 
                                    ${
																			symptom.severity === value
																				? "ring-2 ring-black ring-offset-2 scale-105"
																				: "opacity-80"
																		}`}>
														{value}
													</button>
												);
											})}
										</div>
										<div className="flex justify-between text-xs text-gray-600 mt-2">
											<span>Mild</span>
											<span>Moderate</span>
											<span>Severe</span>
											<span>Very Severe</span>
										</div>
									</div>

									{/* Description */}
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
										<textarea
											value={symptom.description}
											onChange={(e) => handleChange(index, "description", e.target.value)}
											className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
											placeholder="Describe your symptoms in detail (when they occur, what makes them better/worse, etc.)"
											rows={3}
										/>
									</div>
								</div>
							</div>
						))}

						{/* Add More Button */}
						<button
							type="button"
							onClick={addSymptom}
							className="w-full bg-gradient-to-r from-gray-50 to-blue-50 border-2 border-dashed border-blue-300 text-blue-700 font-medium py-6 rounded-2xl hover:from-blue-50 hover:to-blue-100 hover:border-blue-400 transition-all duration-200 group">
							<div className="flex items-center justify-center space-x-3">
								<div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center group-hover:bg-blue-200 transition-colors">
									<Plus className="w-5 h-5 text-blue-600 group-hover:scale-110 transition-transform" />
								</div>
								<span className="text-lg">Add Another Symptom</span>
							</div>
							<p className="text-sm text-blue-600 mt-2 opacity-80">
								Add as many symptoms as needed for comprehensive assessment
							</p>
						</button>

						{/* Submit and Continue */}
						<div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-2xl p-6 border border-gray-200">
							<h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">Ready to Continue?</h3>
							<div className="flex flex-col sm:flex-row gap-4">
								<button
									type="submit"
									disabled={isSubmitting}
									className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium py-4 px-6 rounded-xl shadow-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2 transform hover:scale-105">
									{isSubmitting ? (
										<>
											<div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
											<span>Saving Symptoms...</span>
										</>
									) : (
										<>
											<Save className="w-5 h-5" />
											<span>Save All Symptoms</span>
										</>
									)}
								</button>

								<Link
									href="/chat"
									className="flex-1 bg-gradient-to-r from-green-600 to-green-700 text-white font-medium py-4 px-6 rounded-xl shadow-lg hover:from-green-700 hover:to-green-800 transition-all duration-200 flex items-center justify-center space-x-2 transform hover:scale-105">
									<span>Continue to AI Assessment</span>
									<ArrowRight className="w-5 h-5" />
								</Link>
							</div>
							<p className="text-sm text-gray-600 mt-3 text-center">
								Save your symptoms first, then proceed to the AI assessment for a comprehensive evaluation.
							</p>
						</div>
					</form>
				</div>
			</div>
		</div>
	);
}
