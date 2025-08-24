"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/lib/authContext";
import { useRouter } from "next/navigation";
import { Headphones, Play, Pause, Volume2, VolumeX, CheckCircle, AlertCircle, Loader2, FileText } from "lucide-react";
import Link from "next/link";

interface HearingTestResult {
	frequency: number;
	leftEar: number;
	rightEar: number;
	threshold: number;
}

interface TestPhase {
	name: string;
	description: string;
	frequencies: number[];
	currentFrequency: number;
	currentEar: "left" | "right";
	isComplete: boolean;
}

export default function HearingTestPage() {
	const { user } = useAuth();
	const router = useRouter();
	const [isTestActive, setIsTestActive] = useState(false);
	const [currentPhase, setCurrentPhase] = useState<TestPhase | null>(null);
	const [testResults, setTestResults] = useState<HearingTestResult[]>([]);
	const [currentVolume, setCurrentVolume] = useState(50);
	const [isPlaying, setIsPlaying] = useState(false);
	const [testProgress, setTestProgress] = useState(0);
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

	const audioContextRef = useRef<AudioContext | null>(null);
	const oscillatorRef = useRef<OscillatorNode | null>(null);
	const gainNodeRef = useRef<GainNode | null>(null);

	// Redirect if not authenticated
	useEffect(() => {
		if (!user) {
			router.push("/auth");
		}
	}, [user, router]);

	// Initialize audio context
	useEffect(() => {
		if (typeof window !== "undefined") {
			audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
		}
		return () => {
			if (audioContextRef.current) {
				audioContextRef.current.close();
			}
		};
	}, []);

	const testPhases: TestPhase[] = [
		{
			name: "Low Frequencies",
			description: "Testing your ability to hear low-pitched sounds",
			frequencies: [125, 250, 500],
			currentFrequency: 125,
			currentEar: "left",
			isComplete: false,
		},
		{
			name: "Mid Frequencies",
			description: "Testing your ability to hear mid-range sounds",
			frequencies: [1000, 2000, 3000],
			currentFrequency: 1000,
			currentEar: "left",
			isComplete: false,
		},
		{
			name: "High Frequencies",
			description: "Testing your ability to hear high-pitched sounds",
			frequencies: [4000, 6000, 8000],
			currentFrequency: 4000,
			currentEar: "left",
			isComplete: false,
		},
	];

	const startTest = () => {
		if (!audioContextRef.current) return;

		setIsTestActive(true);
		setCurrentPhase({ ...testPhases[0] });
		setTestResults([]);
		setTestProgress(0);
		setMessage(null);

		// Resume audio context if suspended
		if (audioContextRef.current.state === "suspended") {
			audioContextRef.current.resume();
		}
	};

	const playTone = (frequency: number, volume: number) => {
		if (!audioContextRef.current) return;

		// Stop any existing tone
		if (oscillatorRef.current) {
			oscillatorRef.current.stop();
		}

		// Create new oscillator and gain nodes
		const oscillator = audioContextRef.current.createOscillator();
		const gainNode = audioContextRef.current.createGain();

		// Create stereo panner to route audio to specific ear
		const panner = audioContextRef.current.createStereoPanner();

		// Set the pan based on which ear we're testing
		// -1 = left ear, 1 = right ear
		if (currentPhase) {
			panner.pan.setValueAtTime(currentPhase.currentEar === "left" ? -1 : 1, audioContextRef.current.currentTime);
		}

		oscillator.frequency.setValueAtTime(frequency, audioContextRef.current.currentTime);
		oscillator.type = "sine";

		// Convert volume (0-100) to gain (0-1)
		const gain = volume / 100;
		gainNode.gain.setValueAtTime(gain, audioContextRef.current.currentTime);

		// Connect the audio chain: oscillator -> gain -> panner -> destination
		oscillator.connect(gainNode);
		gainNode.connect(panner);
		panner.connect(audioContextRef.current.destination);

		oscillator.start();
		oscillator.stop(audioContextRef.current.currentTime + 2); // Play for 2 seconds

		oscillatorRef.current = oscillator;
		gainNodeRef.current = gainNode;
		setIsPlaying(true);

		// Stop playing indicator after 2 seconds
		setTimeout(() => {
			setIsPlaying(false);
		}, 2000);
	};

	const handleHearTone = (heard: boolean) => {
		if (!currentPhase) return;

		const result: HearingTestResult = {
			frequency: currentPhase.currentFrequency,
			leftEar: currentPhase.currentEar === "left" ? (heard ? currentVolume : 100) : 0,
			rightEar: currentPhase.currentEar === "right" ? (heard ? currentVolume : 100) : 0,
			threshold: heard ? currentVolume : 100,
		};

		setTestResults((prev) => [...prev, result]);

		// Move to next frequency or ear
		if (currentPhase.currentEar === "left") {
			// Test right ear for same frequency
			setCurrentPhase((prev) =>
				prev
					? {
							...prev,
							currentEar: "right",
					  }
					: null
			);
		} else {
			// Move to next frequency
			const currentFreqIndex = currentPhase.frequencies.indexOf(currentPhase.currentFrequency);
			if (currentFreqIndex < currentPhase.frequencies.length - 1) {
				// Next frequency, start with left ear
				setCurrentPhase((prev) =>
					prev
						? {
								...prev,
								currentFrequency: currentPhase.frequencies[currentFreqIndex + 1],
								currentEar: "left",
						  }
						: null
				);
			} else {
				// Phase complete, move to next phase
				const currentPhaseIndex = testPhases.findIndex((p) => p.name === currentPhase.name);
				if (currentPhaseIndex < testPhases.length - 1) {
					setCurrentPhase({ ...testPhases[currentPhaseIndex + 1] });
				} else {
					// All phases complete
					setIsTestActive(false);
					setCurrentPhase(null);
				}
			}
		}

		// Update progress
		const totalTests = testPhases.reduce((sum, phase) => sum + phase.frequencies.length * 2, 0);
		const completedTests = testResults.length + 1;
		setTestProgress((completedTests / totalTests) * 100);
	};

	const submitResults = async () => {
		if (!user || testResults.length === 0) return;

		// Validate user ID
		if (!user.id) {
			setMessage({ type: "error", text: "User ID not found. Please log in again." });
			return;
		}

		setIsSubmitting(true);
		setMessage(null);

		try {
			// Calculate overall scores
			const leftEarScores = testResults.filter((r) => r.leftEar > 0).map((r) => r.leftEar);
			const rightEarScores = testResults.filter((r) => r.rightEar > 0).map((r) => r.rightEar);

			const leftEarAverage =
				leftEarScores.length > 0 ? leftEarScores.reduce((sum, score) => sum + score, 0) / leftEarScores.length : 0;
			const rightEarAverage =
				rightEarScores.length > 0 ? rightEarScores.reduce((sum, score) => sum + score, 0) / rightEarScores.length : 0;

			const overallScore = Math.round((leftEarAverage + rightEarAverage) / 2);

			const testData = {
				user_id: user.id,
				test_date: new Date().toISOString(),
				left_ear_score: Math.round(leftEarAverage),
				right_ear_score: Math.round(rightEarAverage),
				overall_score: overallScore,
				test_type: "comprehensive",
				notes: "AI-guided hearing assessment",
				detailed_results: testResults,
			};

			// Debug logging
			console.log("Sending test data:", testData);
			console.log("User ID:", user.id);
			console.log("User object:", user);
			console.log("API URL:", process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

			const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
			const response = await fetch(`${apiUrl}/api/hearing/test`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(testData),
			});

			if (response.ok) {
				setMessage({ type: "success", text: "Hearing test results saved successfully!" });
				setTimeout(() => {
					router.push("/reports");
				}, 2000);
			} else {
				const errorData = await response.json();
				console.error("Error response:", errorData);
				// Handle different error response formats
				let errorMessage = "Failed to save results";
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// Handle validation errors array
						errorMessage = errorData.detail.map((err: any) => err.msg || "Validation error").join(", ");
					} else if (typeof errorData.detail === "string") {
						errorMessage = errorData.detail;
					} else {
						errorMessage = "Validation error occurred";
					}
				}
				setMessage({ type: "error", text: errorMessage });
			}
		} catch (error) {
			console.error("Error saving results:", error);
			setMessage({ type: "error", text: "Network error. Please try again." });
		} finally {
			setIsSubmitting(false);
		}
	};

	const stopTest = () => {
		setIsTestActive(false);
		setCurrentPhase(null);
		if (oscillatorRef.current) {
			oscillatorRef.current.stop();
		}
		setIsPlaying(false);
	};

	if (!user) {
		return null; // Will redirect
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 p-6">
			<div className="max-w-6xl mx-auto">
				{/* Header */}
				<div className="text-center mb-8">
					<h1 className="text-4xl font-bold text-gray-900 mb-4">Hearing Assessment</h1>
					<p className="text-lg text-gray-600 max-w-2xl mx-auto">
						Complete a comprehensive hearing test to assess your auditory health. This test will evaluate your ability
						to hear different frequencies in both ears.
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
							{message.type === "success" ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
							<span>{message.text}</span>
						</div>
					</div>
				)}

				{/* Test Instructions */}
				{!isTestActive && (
					<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
						<div className="text-center space-y-6">
							<div className="bg-purple-100 p-4 rounded-full w-20 h-20 mx-auto flex items-center justify-center">
								<Headphones className="w-10 h-10 text-purple-600" />
							</div>

							<div>
								<h2 className="text-2xl font-bold text-gray-900 mb-4">Before You Begin</h2>

								<div className="text-left max-w-2xl mx-auto space-y-3 text-gray-600">
									<div className="flex items-start space-x-3">
										<div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
										<p>Find a quiet environment with minimal background noise</p>
									</div>
									<div className="flex items-start space-x-3">
										<div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
										<p>Use headphones for accurate results (recommended)</p>
									</div>
									<div className="flex items-start space-x-3">
										<div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
										<p>You'll hear tones at different frequencies and volumes</p>
									</div>
									<div className="flex items-start space-x-3">
										<div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
										<p>Click "I can hear it" only when you're certain you hear the tone</p>
									</div>
								</div>
							</div>

							<button
								onClick={startTest}
								className="bg-purple-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-purple-700 transition-colors flex items-center space-x-2 mx-auto">
								<Headphones className="w-5 h-5" />
								<span>Start Hearing Test</span>
							</button>
						</div>
					</div>
				)}

				{/* Active Test */}
				{isTestActive && currentPhase && (
					<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
						{/* Progress Bar */}
						<div className="mb-6">
							<div className="flex justify-between items-center mb-2">
								<span className="text-sm font-medium text-gray-700">Test Progress</span>
								<span className="text-sm text-gray-500">{Math.round(testProgress)}%</span>
							</div>
							<div className="w-full bg-gray-200 rounded-full h-2">
								<div
									className="bg-purple-600 h-2 rounded-full transition-all duration-300"
									style={{ width: `${testProgress}%` }}></div>
							</div>
						</div>

						{/* Current Test Info */}
						<div className="text-center mb-8">
							<h3 className="text-2xl font-bold text-gray-900 mb-2">{currentPhase.name}</h3>
							<p className="text-gray-600 mb-4">{currentPhase.description}</p>

							{/* Prominent Ear Testing Indicator */}
							<div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 max-w-lg mx-auto border-2 border-purple-200">
								<div className="text-center mb-4">
									<p className="text-sm text-gray-600 mb-2">Currently Testing:</p>
									<div
										className={`inline-flex items-center space-x-3 px-6 py-3 rounded-full ${
											currentPhase.currentEar === "left"
												? "bg-blue-100 border-2 border-blue-300"
												: "bg-green-100 border-2 border-green-300"
										}`}>
										{currentPhase.currentEar === "left" && (
											<div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse"></div>
										)}
										<span
											className={`text-xl font-bold capitalize ${
												currentPhase.currentEar === "left" ? "text-blue-700" : "text-green-700"
											}`}>
											{currentPhase.currentEar} Ear
										</span>
										{currentPhase.currentEar === "right" && (
											<div className="w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
										)}
									</div>
								</div>

								<div className="grid grid-cols-2 gap-4 text-center">
									<div>
										<p className="text-sm text-gray-600">Frequency</p>
										<p className="text-2xl font-bold text-purple-600">{currentPhase.currentFrequency} Hz</p>
									</div>
									<div>
										<p className="text-sm text-gray-600">Test Phase</p>
										<p className="text-lg font-semibold text-gray-800">{currentPhase.name}</p>
									</div>
								</div>

								{/* Ear Testing Visual */}
								<div className="mt-4 p-4 bg-white rounded-lg border border-purple-300">
									<div className="flex items-center justify-center space-x-12">
										<div
											className={`text-center transition-all duration-300 ${
												currentPhase.currentEar === "left" ? "scale-110" : "scale-100"
											}`}>
											<div
												className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center text-white font-bold text-lg ${
													currentPhase.currentEar === "left" ? "bg-blue-500 shadow-lg" : "bg-gray-300 text-gray-600"
												}`}>
												L
											</div>
											<p
												className={`text-sm font-medium ${
													currentPhase.currentEar === "left" ? "text-blue-700" : "text-gray-500"
												}`}>
												Left Ear
											</p>
										</div>
										<div
											className={`text-center transition-all duration-300 ${
												currentPhase.currentEar === "right" ? "scale-110" : "scale-100"
											}`}>
											<div
												className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center text-white font-bold text-lg ${
													currentPhase.currentEar === "right" ? "bg-green-500 shadow-lg" : "bg-gray-300 text-gray-600"
												}`}>
												R
											</div>
											<p
												className={`text-sm font-medium ${
													currentPhase.currentEar === "right" ? "text-green-700" : "text-gray-500"
												}`}>
												Right Ear
											</p>
										</div>
									</div>
								</div>
							</div>
						</div>

						{/* Volume Control */}
						<div className="max-w-md mx-auto mb-8">
							<label className="block text-sm font-medium text-gray-700 mb-3">Volume Level: {currentVolume}%</label>
							<input
								type="range"
								min="0"
								max="100"
								value={currentVolume}
								onChange={(e) => setCurrentVolume(parseInt(e.target.value))}
								className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
							/>
							<div className="flex justify-between text-xs text-gray-500 mt-1">
								<span>Quiet</span>
								<span>Loud</span>
							</div>
						</div>

						{/* Test Controls */}
						<div className="flex justify-center space-x-4 mb-6">
							<button
								onClick={() => playTone(currentPhase.currentFrequency, currentVolume)}
								disabled={isPlaying}
								className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center space-x-2">
								{isPlaying ? (
									<>
										<Loader2 className="w-4 h-4 animate-spin" />
										<span>Playing...</span>
									</>
								) : (
									<>
										<Play className="w-4 h-4" />
										<span>Play Tone</span>
									</>
								)}
							</button>
						</div>

						{/* Response Buttons */}
						<div className="flex justify-center space-x-4">
							<button
								onClick={() => handleHearTone(true)}
								className="bg-green-600 text-white px-8 py-4 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
								<CheckCircle className="w-4 h-4" />
								<span>I Can Hear It</span>
							</button>

							<button
								onClick={() => handleHearTone(false)}
								className="bg-red-600 text-white px-8 py-4 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2">
								<VolumeX className="w-4 h-4" />
								<span>I Cannot Hear It</span>
							</button>
						</div>

						{/* Stop Test */}
						<div className="text-center mt-6">
							<button onClick={stopTest} className="text-gray-500 hover:text-gray-700 transition-colors">
								Stop Test
							</button>
						</div>
					</div>
				)}

				{/* Test Complete */}
				{!isTestActive && testResults.length > 0 && (
					<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
						<div className="text-center space-y-6">
							<div className="bg-green-100 p-4 rounded-full w-20 h-20 mx-auto flex items-center justify-center">
								<CheckCircle className="w-10 h-10 text-green-600" />
							</div>

							<div>
								<h2 className="text-2xl font-bold text-gray-900 mb-4">Test Complete!</h2>
								<p className="text-gray-600 mb-6">
									Your hearing assessment is complete. Review your results below and save them to your profile.
								</p>
							</div>

							{/* Results Summary */}
							<div className="grid md:grid-cols-3 gap-6 max-w-2xl mx-auto">
								<div className="bg-blue-50 p-4 rounded-lg text-center">
									<p className="text-sm text-gray-600">Left Ear</p>
									<p className="text-2xl font-bold text-blue-600">
										{Math.round(
											testResults.filter((r) => r.leftEar > 0).reduce((sum, r) => sum + r.leftEar, 0) /
												testResults.filter((r) => r.leftEar > 0).length || 0
										)}
										%
									</p>
								</div>
								<div className="bg-green-50 p-4 rounded-lg text-center">
									<p className="text-sm text-gray-600">Right Ear</p>
									<p className="text-2xl font-bold text-green-600">
										{Math.round(
											testResults.filter((r) => r.rightEar > 0).reduce((sum, r) => sum + r.rightEar, 0) /
												testResults.filter((r) => r.rightEar > 0).length || 0
										)}
										%
									</p>
								</div>
								<div className="bg-purple-50 p-4 rounded-lg text-center">
									<p className="text-sm text-gray-600">Overall</p>
									<p className="text-2xl font-bold text-purple-600">
										{Math.round(
											(testResults.filter((r) => r.leftEar > 0).reduce((sum, r) => sum + r.leftEar, 0) /
												testResults.filter((r) => r.leftEar > 0).length || 0) +
												(testResults.filter((r) => r.rightEar > 0).reduce((sum, r) => sum + r.rightEar, 0) /
													testResults.filter((r) => r.rightEar > 0).length || 0)
										) / 2}
										%
									</p>
								</div>
							</div>

							{/* Action Buttons */}
							<div className="flex flex-col sm:flex-row gap-4 justify-center">
								<button
									onClick={submitResults}
									disabled={isSubmitting}
									className="bg-green-600 text-white px-8 py-4 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center space-x-2">
									{isSubmitting ? (
										<>
											<Loader2 className="w-5 h-5 animate-spin" />
											<span>Saving Results...</span>
										</>
									) : (
										<>
											<FileText className="w-5 h-5" />
											<span>Save Results</span>
										</>
									)}
								</button>

								<Link
									href="/reports"
									className="bg-blue-600 text-white px-8 py-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
									<span>View Reports</span>
								</Link>
							</div>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
