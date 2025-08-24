"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/authContext";
import { useRouter } from "next/navigation";
import { Send, MessageSquare, Brain, FileText, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import Link from "next/link";

interface ChatMessage {
	id: string;
	message: string;
	is_doctor: boolean;
	timestamp: string;
	session_id?: string;
}

interface ChatSession {
	id: string;
	session_name: string;
	created_at: string;
	is_active: boolean;
}

export default function ChatPage() {
	const { user } = useAuth();
	const router = useRouter();
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [inputMessage, setInputMessage] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
	const [sessions, setSessions] = useState<ChatSession[]>([]);
	const [showSessions, setShowSessions] = useState(false);
	const [assessmentComplete, setAssessmentComplete] = useState(false);
	const [reportGenerated, setReportGenerated] = useState(false);
	const [sessionError, setSessionError] = useState<string | null>(null);
	const [assessmentProgress, setAssessmentProgress] = useState(0);
	const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(
		null
	);

	const messagesEndRef = useRef<HTMLDivElement>(null);
	const chatContainerRef = useRef<HTMLDivElement>(null);

	// Redirect if not authenticated
	useEffect(() => {
		if (!user) {
			router.push("/auth");
		}
	}, [user, router]);

	// Auto-scroll to bottom
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages]);

	// Load user sessions on mount
	useEffect(() => {
		if (user) {
			loadUserSessions();
		}
	}, [user]);

	const loadUserSessions = async () => {
		try {
			setSessionError(null);
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/sessions/${user?.id}`
			);
			if (response.ok) {
				const data = await response.json();
				setSessions(data);
				// Use most recent active session or create new one
				const activeSession = data.find((s: ChatSession) => s.is_active);
				if (activeSession) {
					setCurrentSession(activeSession);
					loadSessionMessages(activeSession.id);
				} else {
					await createNewSession();
				}
			} else {
				console.error("Failed to load sessions:", response.status);
				// Try to create a new session if loading fails
				await createNewSession();
			}
		} catch (error) {
			console.error("Error loading sessions:", error);
			setSessionError("Failed to load sessions. Creating new session...");
			// Try to create a new session if loading fails
			await createNewSession();
		}
	};

	const createNewSession = async () => {
		try {
			setSessionError(null);
			const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/session`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					user_id: user?.id,
					session_name: `Medical Assessment - ${new Date().toLocaleDateString()}`,
				}),
			});

			if (response.ok) {
				const newSession = await response.json();
				setCurrentSession(newSession);
				setSessions((prev) => [newSession, ...prev]);
				setMessages([]);
				setAssessmentComplete(false);
				setReportGenerated(false);
				setSessionError(null);
			} else {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || `Failed to create session: ${response.status}`);
			}
		} catch (error) {
			console.error("Error creating session:", error);
			setSessionError(`Failed to create session: ${error instanceof Error ? error.message : "Unknown error"}`);
			// Create a temporary local session to allow chatting
			const tempSession: ChatSession = {
				id: `temp-${Date.now()}`,
				session_name: `Local Session - ${new Date().toLocaleDateString()}`,
				created_at: new Date().toISOString(),
				is_active: true,
			};
			setCurrentSession(tempSession);
		}
	};

	const loadSessionMessages = async (sessionId: string) => {
		try {
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/session/${sessionId}/messages`
			);
			if (response.ok) {
				const data = await response.json();
				setMessages(data);
				// Check if assessment is complete
				const hasCompleteMessage = data.some(
					(msg: ChatMessage) =>
						msg.message.toLowerCase().includes("assessment complete") ||
						msg.message.toLowerCase().includes("report generated")
				);
				setAssessmentComplete(hasCompleteMessage);
			}
		} catch (error) {
			console.error("Error loading messages:", error);
		}
	};

	// Show notification helper
	const showNotification = (type: "success" | "error" | "info", message: string) => {
		setNotification({ type, message });
		setTimeout(() => setNotification(null), 5000);
	};

	const sendMessage = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!inputMessage.trim() || !currentSession || isLoading) return;

		const userMessage: ChatMessage = {
			id: Date.now().toString(),
			message: inputMessage.trim(),
			is_doctor: false,
			timestamp: new Date().toISOString(),
			session_id: currentSession.id,
		};

		setMessages((prev) => [...prev, userMessage]);
		setInputMessage("");
		setIsLoading(true);

		try {
			// If it's a temporary session, just simulate AI response
			if (currentSession.id.startsWith("temp-")) {
				setTimeout(() => {
					const aiMessage: ChatMessage = {
						id: (Date.now() + 1).toString(),
						message: "This is a local session. Please ensure your backend is running and try creating a new session.",
						is_doctor: true,
						timestamp: new Date().toISOString(),
						session_id: currentSession.id,
					};
					setMessages((prev) => [...prev, aiMessage]);
					setIsLoading(false);
					showNotification("error", "Backend connection required for AI assessment");
				}, 1000);
				return;
			}

			const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/send`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					user_id: user?.id,
					message: userMessage.message,
					session_id: currentSession.id,
				}),
			});

			if (response.ok) {
				const data = await response.json();

				// Extract the actual message content from the response
				let aiResponseMessage = "I'm sorry, I couldn't process your request.";

				// The backend now returns a ChatResponse object with the AI response in the 'response' field
				if (data.response) {
					aiResponseMessage = data.response;
				} else if (data.message) {
					// Fallback to message field if response is not available
					aiResponseMessage = data.message;
				}

				// Add AI response
				const aiMessage: ChatMessage = {
					id: (Date.now() + 1).toString(),
					message: aiResponseMessage,
					is_doctor: true,
					timestamp: new Date().toISOString(),
					session_id: currentSession.id,
				};
				setMessages((prev) => [...prev, aiMessage]);

				// Update assessment progress based on conversation length
				const newProgress = Math.min(assessmentProgress + 10, 90);
				setAssessmentProgress(newProgress);

				// Check if assessment is complete based on AI response content
				if (
					(aiResponseMessage && aiResponseMessage.toLowerCase().includes("assessment complete")) ||
					(aiResponseMessage && aiResponseMessage.toLowerCase().includes("report ready")) ||
					(aiResponseMessage && aiResponseMessage.toLowerCase().includes("comprehensive report")) ||
					(aiResponseMessage && aiResponseMessage.toLowerCase().includes("sufficient information")) ||
					(aiResponseMessage && aiResponseMessage.toLowerCase().includes("enough information"))
				) {
					setAssessmentComplete(true);
					setAssessmentProgress(100);
					showNotification("success", "Assessment complete! You can now generate your report.");
				}

				// Check if we have enough messages for assessment completion
				if (messages.length >= 8 && !assessmentComplete) {
					setAssessmentComplete(true);
					setAssessmentProgress(100);
					showNotification("success", "Assessment complete! You can now generate your report.");
				}
			} else {
				// Add error message
				const errorMessage: ChatMessage = {
					id: (Date.now() + 1).toString(),
					message: "I'm sorry, I'm having trouble processing your request. Please try again.",
					is_doctor: true,
					timestamp: new Date().toISOString(),
					session_id: currentSession.id,
				};
				setMessages((prev) => [...prev, errorMessage]);
				showNotification("error", "Failed to process message. Please try again.");
			}
		} catch (error) {
			console.error("Error sending message:", error);
			const errorMessage: ChatMessage = {
				id: (Date.now() + 1).toString(),
				message: "Network error. Please check your connection and try again.",
				is_doctor: true,
				timestamp: new Date().toISOString(),
				session_id: currentSession.id,
			};
			setMessages((prev) => [...prev, errorMessage]);
			showNotification("error", "Network error. Please check your connection.");
		} finally {
			setIsLoading(false);
		}
	};

	const generateReport = async () => {
		if (!currentSession) return;

		setIsLoading(true);
		try {
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/generate-report/${currentSession.id}`,
				{ method: "POST" }
			);

			if (response.ok) {
				setReportGenerated(true);
				// Show success message and redirect to reports page
				setTimeout(() => {
					router.push("/reports");
				}, 2000);
			} else {
				const errorData = await response.json().catch(() => ({}));
				console.error("Report generation failed:", errorData);
				// Show error message to user
				const errorMessage: ChatMessage = {
					id: (Date.now() + 1).toString(),
					message: `Failed to generate report: ${
						errorData.detail || "Unknown error"
					}. Please try again or contact support.`,
					is_doctor: true,
					timestamp: new Date().toISOString(),
					session_id: currentSession.id,
				};
				setMessages((prev) => [...prev, errorMessage]);
			}
		} catch (error) {
			console.error("Error generating report:", error);
			// Show error message to user
			const errorMessage: ChatMessage = {
				id: (Date.now() + 1).toString(),
				message: "Network error while generating report. Please check your connection and try again.",
				is_doctor: true,
				timestamp: new Date().toISOString(),
				session_id: currentSession.id,
			};
			setMessages((prev) => [...prev, errorMessage]);
		} finally {
			setIsLoading(false);
		}
	};

	const startNewAssessment = () => {
		createNewSession();
		setAssessmentProgress(0);
		setAssessmentComplete(false);
		setReportGenerated(false);
	};

	if (!user) {
		return null; // Will redirect
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
			{/* Notification */}
			{notification && (
				<div
					className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
						notification.type === "success"
							? "bg-green-500 text-white"
							: notification.type === "error"
							? "bg-red-500 text-white"
							: "bg-blue-500 text-white"
					}`}>
					<div className="flex items-center space-x-2">
						{notification.type === "success" && <CheckCircle className="w-5 h-5" />}
						{notification.type === "error" && <AlertCircle className="w-5 h-5" />}
						{notification.type === "info" && <MessageSquare className="w-5 h-5" />}
						<span>{notification.message}</span>
					</div>
				</div>
			)}

			<div className="max-w-6xl mx-auto">
				{/* Header */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-6">
					<div className="flex items-center justify-between">
						<div className="flex items-center space-x-4">
							<div className="bg-blue-100 p-3 rounded-full">
								<Brain className="w-8 h-8 text-blue-600" />
							</div>
							<div>
								<h1 className="text-3xl font-bold text-gray-900">AI Medical Assessment</h1>
								<p className="text-gray-600">
									{currentSession ? `Session: ${currentSession.session_name}` : "Starting new assessment..."}
								</p>
								{sessionError && (
									<p className="text-red-600 text-sm mt-1 flex items-center">
										<AlertCircle className="w-4 h-4 mr-1" />
										{sessionError}
									</p>
								)}
							</div>
						</div>

						<div className="flex items-center space-x-3">
							<button
								onClick={() => setShowSessions(!showSessions)}
								className="bg-gray-100 hover:bg-gray-200 p-3 rounded-lg transition-colors"
								title="View Sessions">
								<MessageSquare className="w-5 h-5 text-gray-600" />
							</button>

							{assessmentComplete && (
								<button
									onClick={generateReport}
									disabled={isLoading || reportGenerated}
									className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center space-x-2">
									{reportGenerated ? (
										<>
											<CheckCircle className="w-4 h-4" />
											<span>Report Generated</span>
										</>
									) : (
										<>
											<FileText className="w-4 h-4" />
											<span>Generate Report</span>
										</>
									)}
								</button>
							)}
						</div>
					</div>

					{/* Assessment Progress Bar */}
					{messages.length > 0 && !assessmentComplete && (
						<div className="mt-4">
							<div className="flex justify-between items-center mb-2">
								<span className="text-sm font-medium text-gray-700">Assessment Progress</span>
								<span className="text-sm text-gray-500">{Math.round(assessmentProgress)}%</span>
							</div>
							<div className="w-full bg-gray-200 rounded-full h-2">
								<div
									className="bg-blue-600 h-2 rounded-full transition-all duration-500"
									style={{ width: `${assessmentProgress}%` }}></div>
							</div>
							<p className="text-xs text-gray-500 mt-1">
								{assessmentProgress < 20 && "Starting assessment..."}
								{assessmentProgress >= 20 && assessmentProgress < 40 && "Gathering symptom information..."}
								{assessmentProgress >= 40 && assessmentProgress < 60 && "Collecting medical history..."}
								{assessmentProgress >= 60 && assessmentProgress < 80 && "Assessing risk factors..."}
								{assessmentProgress >= 80 && assessmentProgress < 90 && "Finalizing assessment..."}
								{assessmentProgress >= 90 && "Almost complete..."}
							</p>
							{/* Progress Tips */}
							<div className="mt-2 text-xs text-blue-600">
								{assessmentProgress < 20 && "💡 Describe your main symptoms and concerns"}
								{assessmentProgress >= 20 &&
									assessmentProgress < 40 &&
									"💡 Provide details about symptom severity and duration"}
								{assessmentProgress >= 40 &&
									assessmentProgress < 60 &&
									"💡 Share relevant medical history and medications"}
								{assessmentProgress >= 60 && assessmentProgress < 80 && "💡 Discuss lifestyle factors and risk factors"}
								{assessmentProgress >= 80 &&
									assessmentProgress < 90 &&
									"💡 Answer any remaining questions to complete assessment"}
							</div>
						</div>
					)}
				</div>

				<div className="grid lg:grid-cols-4 gap-6">
					{/* Sessions Sidebar */}
					{showSessions && (
						<div className="lg:col-span-1">
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<h3 className="text-lg font-semibold text-gray-800 mb-4">Your Sessions</h3>
								<div className="space-y-3">
									{sessions.map((session) => (
										<button
											key={session.id}
											onClick={() => {
												setCurrentSession(session);
												loadSessionMessages(session.id);
												setShowSessions(false);
											}}
											className={`w-full text-left p-3 rounded-lg border transition-colors ${
												currentSession?.id === session.id
													? "border-blue-500 bg-blue-50"
													: "border-gray-200 hover:border-gray-300"
											}`}>
											<div className="font-medium text-gray-800">{session.session_name}</div>
											<div className="text-sm text-gray-500">{new Date(session.created_at).toLocaleDateString()}</div>
										</button>
									))}
								</div>

								<button
									onClick={startNewAssessment}
									className="w-full mt-4 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
									Start New Assessment
								</button>
							</div>
						</div>
					)}

					{/* Chat Interface */}
					<div className={`${showSessions ? "lg:col-span-3" : "lg:col-span-4"}`}>
						<div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
							{/* Chat Messages */}
							<div ref={chatContainerRef} className="h-96 overflow-y-auto p-6 space-y-4">
								{messages.length === 0 ? (
									<div className="text-center py-12">
										<Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
										<h3 className="text-xl font-semibold text-gray-600 mb-2">Welcome to Your Medical Assessment</h3>
										<p className="text-gray-500 mb-6">
											I'm your AI medical attendant. I'll guide you through a comprehensive neurological assessment to
											understand your health concerns and create a personalized report.
										</p>

										{/* Assessment Instructions */}
										<div className="max-w-md mx-auto bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
											<h4 className="font-medium text-blue-800 mb-3">What to expect:</h4>
											<div className="space-y-2 text-sm text-blue-700">
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>I'll ask about your symptoms and health concerns</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>We'll review your medical history and medications</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>I'll assess potential risk factors and lifestyle</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>You'll receive personalized recommendations</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>Assessment typically takes 5-10 minutes</span>
												</div>
											</div>
										</div>

										<p className="text-sm text-gray-400 mt-4">
											Start by describing your main symptoms or health concerns below.
										</p>
									</div>
								) : (
									messages.map((message) => (
										<div key={message.id} className={`flex ${message.is_doctor ? "justify-start" : "justify-end"}`}>
											<div
												className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
													message.is_doctor ? "bg-blue-100 text-gray-800" : "bg-blue-600 text-white"
												}`}>
												<p className="text-sm">{message.message}</p>
												<p className={`text-xs mt-2 ${message.is_doctor ? "text-gray-500" : "text-blue-100"}`}>
													{new Date(message.timestamp).toLocaleTimeString()}
												</p>
											</div>
										</div>
									))
								)}

								{isLoading && (
									<div className="flex justify-start">
										<div className="bg-blue-100 text-gray-800 px-4 py-3 rounded-2xl">
											<div className="flex items-center space-x-2">
												<Loader2 className="w-4 h-4 animate-spin" />
												<span className="text-sm">AI is thinking...</span>
											</div>
										</div>
									</div>
								)}

								<div ref={messagesEndRef} />
							</div>

							{/* Input Area */}
							<div className="border-t border-gray-200 p-4">
								<form onSubmit={sendMessage} className="flex space-x-3">
									<input
										type="text"
										value={inputMessage}
										onChange={(e) => setInputMessage(e.target.value)}
										placeholder="Describe your symptoms or answer questions..."
										className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-gray-900 placeholder-gray-500 bg-white"
										disabled={isLoading}
									/>
									<button
										type="submit"
										disabled={isLoading || !inputMessage.trim()}
										className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2">
										<Send className="w-4 h-4" />
										<span>Send</span>
									</button>
								</form>
							</div>
						</div>

						{/* Assessment Status */}
						{assessmentComplete && (
							<div className="mt-6 bg-green-50 border border-green-200 rounded-xl p-6">
								<div className="flex items-center space-x-3">
									<CheckCircle className="w-8 h-8 text-green-600" />
									<div>
										<h3 className="text-lg font-semibold text-green-800">Assessment Complete! 🎉</h3>
										<p className="text-green-700">
											Your AI medical assessment is complete. You can now generate a comprehensive report or continue to
											the hearing test for additional evaluation.
										</p>
									</div>
								</div>

								<div className="mt-4 flex flex-wrap gap-3">
									<button
										onClick={generateReport}
										disabled={isLoading || reportGenerated}
										className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors disabled:opacity-50 flex items-center space-x-2">
										{reportGenerated ? (
											<>
												<CheckCircle className="w-4 h-4" />
												<span>Report Generated</span>
											</>
										) : (
											<>
												<FileText className="w-4 h-4" />
												<span>Generate Report</span>
											</>
										)}
									</button>

									<Link
										href="/hearing"
										className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2">
										<span>Take Hearing Test</span>
									</Link>
								</div>

								{/* Report Generation Progress */}
								{isLoading && (
									<div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
										<div className="flex items-center space-x-3">
											<Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
											<div>
												<h4 className="font-medium text-blue-800">Generating Your Report...</h4>
												<p className="text-sm text-blue-600">This may take a few moments. Please wait.</p>
											</div>
										</div>
									</div>
								)}

								{/* Report Generation Success */}
								{reportGenerated && (
									<div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
										<div className="flex items-center space-x-3">
											<CheckCircle className="w-5 h-5 text-green-600" />
											<div>
												<h4 className="font-medium text-green-800">Report Generated Successfully!</h4>
												<p className="text-sm text-green-600">Redirecting to reports page...</p>
											</div>
										</div>
									</div>
								)}
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
