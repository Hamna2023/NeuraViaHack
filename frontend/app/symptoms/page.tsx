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
					<h1 className="text-4xl font-bold text-gray-900 mb-4">Report Your Symptoms</h1>
					<p className="text-lg text-gray-600">
						Help us understand your health concerns. Be as detailed as possible for better assessment.
					</p>
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
							<div key={index} className="p-6 border border-gray-200 rounded-xl bg-gray-50 relative">
								<div className="flex items-center justify-between mb-4">
									<h3 className="text-lg font-semibold text-gray-800">Symptom {index + 1}</h3>
									{symptoms.length > 1 && (
										<button
											type="button"
											onClick={() => removeSymptom(index)}
											className="text-red-500 hover:text-red-700 transition-colors p-1"
											aria-label="Remove symptom">
											<Trash2 size={20} />
										</button>
									)}
								</div>

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
						))}

						{/* Add More Button */}
						<button
							type="button"
							onClick={addSymptom}
							className="w-full bg-gray-100 border-2 border-dashed border-gray-300 text-gray-700 font-medium py-4 rounded-xl hover:bg-gray-200 transition-colors group">
							<div className="flex items-center justify-center space-x-2">
								<Plus className="w-5 h-5 group-hover:scale-110 transition-transform" />
								<span>Add Another Symptom</span>
							</div>
						</button>

						{/* Submit and Continue */}
						<div className="flex flex-col sm:flex-row gap-4 pt-6">
							<button
								type="submit"
								disabled={isSubmitting}
								className="flex-1 bg-blue-600 text-white font-medium py-4 px-6 rounded-xl shadow-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2">
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
								className="flex-1 bg-green-600 text-white font-medium py-4 px-6 rounded-xl shadow-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2">
								<span>Continue to AI Assessment</span>
								<ArrowRight className="w-5 h-5" />
							</Link>
						</div>
					</form>
				</div>
			</div>
		</div>
	);
}
