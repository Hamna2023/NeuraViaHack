"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/authContext";
import { useRouter } from "next/navigation";
import {
	Send,
	MessageSquare,
	Brain,
	FileText,
	Loader2,
	AlertCircle,
	CheckCircle,
	Lock,
	User,
	Calendar,
	Activity,
	Headphones,
	Plus,
	Unlock,
} from "lucide-react";
import Link from "next/link";

interface ChatMessage {
	id: string;
	message: string;
	is_doctor: boolean;
	timestamp: string;
	session_id?: string;
	// Simplified AI system fields
	assessment_complete?: boolean;
	completion_score?: number;
	message_count?: number;
}

interface ChatSession {
	id: string;
	session_name: string;
	created_at: string;
	is_active: boolean;
	assessment_complete: boolean;
	completion_score: number;
	message_count: number;
}

interface UserContext {
	name?: string;
	age?: number;
	gender?: string;
	existing_symptoms?: string[];
	hearing_status?: string;
	previous_assessments?: number;
	last_assessment_date?: string | null;
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
	const [userContext, setUserContext] = useState<UserContext | null>(null);
	const [showUserContext, setShowUserContext] = useState(false);
	const [messageCount, setMessageCount] = useState(0);
	const [maxMessages] = useState(10);
	const [notification, setNotification] = useState<{ type: "success" | "error" | "info"; message: string } | null>(
		null
	);
	const [userContextLoading, setUserContextLoading] = useState(false);
	const [userContextError, setUserContextError] = useState<string | null>(null);
	const [sessionsLoading, setSessionsLoading] = useState(false);
	const [backendStatus, setBackendStatus] = useState<{ reachable: boolean; error?: string }>({ reachable: false });

	// Test backend connectivity
	const testBackendConnectivity = async () => {
		try {
			const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`, {
				method: "HEAD",
			});
			setBackendStatus({ reachable: true });
			return true;
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : "Unknown error";
			setBackendStatus({ reachable: false, error: errorMessage });
			return false;
		}
	};

	const messagesEndRef = useRef<HTMLDivElement>(null);
	const chatContainerRef = useRef<HTMLDivElement>(null);

	// Helper function to check if assessment should be complete
	const shouldAssessmentBeComplete = (messages: ChatMessage[], completionScore: number): boolean => {
		// Only complete if we have substantial conversation and high completion score
		if (completionScore >= 90 && messages.length >= 8) {
			const lastAIMessage = messages.filter((m) => m.is_doctor).pop();
			const lastMessageIsQuestion = lastAIMessage && lastAIMessage.message.trim().endsWith("?");
			return !lastMessageIsQuestion;
		}
		return false;
	};

	// Helper function to check if there are pending questions
	const hasPendingQuestions = (messages: ChatMessage[]): boolean => {
		const lastAIMessage = messages.filter((m) => m.is_doctor).pop();
		return Boolean(lastAIMessage && lastAIMessage.message.trim().endsWith("?"));
	};

	// Helper function to check if assessment is ready for completion
	const isAssessmentReadyForCompletion = (messages: ChatMessage[], completionScore: number): boolean => {
		return completionScore >= 85 && !hasPendingQuestions(messages);
	};

	// Redirect if not authenticated
	useEffect(() => {
		if (!user) {
			router.push("/auth");
		}
	}, [user, router]);

	// Load initial data
	useEffect(() => {
		if (user) {
			testBackendConnectivity();
			loadUserContext();
			loadUserSessions();
		}
	}, [user]);

	// Refresh user context when user profile changes
	useEffect(() => {
		if (user && userContext) {
			// Check if user data has changed and refresh if needed
			if (user.name !== userContext.name) {
				loadUserContext();
			}
		}
	}, [user, userContext]);

	// Scroll to bottom when messages change
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [messages]);

	// Load user context for personalized experience
	const loadUserContext = async () => {
		try {
			setUserContextLoading(true);
			setUserContextError(null);

			// Start with user data from auth context (this is what works in the navbar)
			const baseUserData = {
				name: user?.name || "Not set",
				age: undefined,
				gender: "Not set",
				existing_symptoms: [],
				hearing_status: "Not tested",
				previous_assessments: 0,
				last_assessment_date: null,
			};

			// Try to fetch additional data from backend, but don't fail if it doesn't work
			try {
				// Check if backend is reachable first
				const backendHealthCheck = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`, {
					method: "HEAD",
				}).catch(() => null);

				if (backendHealthCheck) {
					// Backend is reachable, try to fetch additional data
					console.log("Backend is reachable, fetching additional profile data...");

					// Fetch user profile from backend
					const profileResponse = await fetch(
						`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/users/profile/${user?.id}`
					);

					if (profileResponse.ok) {
						const profileData = await profileResponse.json();
						baseUserData.name = profileData?.name || baseUserData.name;
						baseUserData.age = profileData?.age;
						baseUserData.gender = profileData?.gender || baseUserData.gender;
						console.log("Profile data loaded:", profileData);
					} else {
						console.warn(`Profile API returned ${profileResponse.status}: ${profileResponse.statusText}`);
					}

					// Fetch user symptoms from backend
					const symptomsResponse = await fetch(
						`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/symptoms/user/${user?.id}`
					);

					if (symptomsResponse.ok) {
						const symptomsData = await symptomsResponse.json();
						baseUserData.existing_symptoms =
							symptomsData.map((s: any) => s.symptom_name || s.symptom).filter(Boolean) || [];
						console.log("Symptoms data loaded:", symptomsData);
					} else {
						console.warn(`Symptoms API returned ${symptomsResponse.status}: ${symptomsResponse.statusText}`);
					}

					// Fetch user hearing tests from backend
					const hearingResponse = await fetch(
						`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/hearing/user/${user?.id}`
					);

					if (hearingResponse.ok) {
						const hearingData = await hearingResponse.json();
						if (hearingData.length > 0) {
							const latestTest = hearingData[0];
							const overallScore = latestTest.overall_score || 0;
							if (overallScore >= 80) {
								baseUserData.hearing_status = "Excellent";
							} else if (overallScore >= 60) {
								baseUserData.hearing_status = "Good";
							} else if (overallScore >= 40) {
								baseUserData.hearing_status = "Fair";
							} else {
								baseUserData.hearing_status = "Poor";
							}
						}
						console.log("Hearing data loaded:", hearingData);
					} else {
						console.warn(`Hearing API returned ${hearingResponse.status}: ${hearingResponse.statusText}`);
					}

					// Fetch user reports to get assessment count
					const reportsResponse = await fetch(
						`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/reports/user/${user?.id}`
					);

					if (reportsResponse.ok) {
						const reportsData = await reportsResponse.json();
						baseUserData.previous_assessments = reportsData.length || 0;
						baseUserData.last_assessment_date = reportsData.length > 0 ? reportsData[0]?.created_at : null;
						console.log("Reports data loaded:", reportsData);
					} else {
						console.warn(`Reports API returned ${reportsResponse.status}: ${reportsResponse.statusText}`);
					}

					// Show success notification if we loaded any additional data
					const hasAdditionalData =
						baseUserData.age ||
						baseUserData.gender !== "Not set" ||
						baseUserData.existing_symptoms.length > 0 ||
						baseUserData.hearing_status !== "Not tested" ||
						baseUserData.previous_assessments > 0;

					if (hasAdditionalData) {
						showNotification("success", "Profile data loaded successfully!");
					} else {
						showNotification("info", "Using basic profile data. Backend data not available.");
					}
				} else {
					console.warn("Backend not reachable, using basic user data only");
					showNotification("info", "Backend not available. Using basic profile data.");
				}
			} catch (backendError) {
				console.warn("Backend data fetch failed, using basic user data:", backendError);
				showNotification("info", "Some profile data unavailable. Using basic profile data.");
			}

			// Set the user context with whatever data we have
			setUserContext(baseUserData);
		} catch (error) {
			console.error("Error in loadUserContext:", error);
			setUserContextError(`Failed to load user context: ${error instanceof Error ? error.message : "Unknown error"}`);

			// Fallback to basic user data from auth context
			setUserContext({
				name: user?.name || "Not set",
				age: undefined,
				gender: "Not set",
				existing_symptoms: [],
				hearing_status: "Not tested",
				previous_assessments: 0,
				last_assessment_date: null,
			});

			showNotification("error", "Failed to load profile data. Using basic profile information.");
		} finally {
			setUserContextLoading(false);
		}
	};

	const loadUserSessions = async () => {
		try {
			setSessionsLoading(true);
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
					setAssessmentComplete(activeSession.assessment_complete);
					setAssessmentProgress(activeSession.completion_score);
					loadSessionMessages(activeSession.id);
				} else {
					await createNewSession();
				}

				// Show success notification if we loaded sessions
				if (data.length > 0) {
					showNotification("success", `Loaded ${data.length} session(s) successfully!`);
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
		} finally {
			setSessionsLoading(false);
		}
	};

	const createNewSession = async () => {
		try {
			console.log("Creating new session...");
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
				console.log("New session created:", newSession);
				setCurrentSession(newSession);
				setSessions((prev) => [newSession, ...prev]);
				setMessages([]);
				setAssessmentComplete(false);
				setReportGenerated(false);
				setAssessmentProgress(0);
				setMessageCount(0);
				setSessionError(null);

				// Load the AI-generated initial greeting
				console.log("Loading messages for new session...");
				await loadSessionMessages(newSession.id);
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
				assessment_complete: false,
				completion_score: 0,
				message_count: 0,
			};
			setCurrentSession(tempSession);
		}
	};

	const loadSessionMessages = async (sessionId: string) => {
		try {
			console.log(`Loading messages for session: ${sessionId}`);
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/session/${sessionId}/messages`
			);
			if (response.ok) {
				const data = await response.json();
				console.log(`Loaded ${data.length} messages:`, data);
				setMessages(data);
				setMessageCount(data.length); // Update message count

				// Check if assessment is complete based on session status
				const session = sessions.find((s) => s.id === sessionId);
				if (session) {
					setAssessmentComplete(session.assessment_complete);
					setAssessmentProgress(session.completion_score);
				}

				// If no messages and this is a new session, we should have a greeting
				if (data.length === 0 && sessionId && !sessionId.startsWith("temp-")) {
					console.log("No messages found, waiting for greeting...");
					// Wait a moment for the backend to process the greeting
					setTimeout(() => {
						console.log("Retrying to load messages...");
						loadSessionMessages(sessionId);
					}, 2000);
				}
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
				let isComplete = false;
				let completionScore = 0;
				let isChatLocked = false;

				// The backend now returns a ChatResponse object with the AI response in the 'response' field
				if (data.response) {
					aiResponseMessage = data.response;
				} else if (data.message) {
					// Fallback to message field if response is not available
					aiResponseMessage = data.message;
				}

				// Check for assessment completion and progress
				if (data.assessment_complete !== undefined) {
					isComplete = data.assessment_complete;
				}
				if (data.completion_score !== undefined) {
					completionScore = data.completion_score;
				}
				if (data.chat_locked !== undefined) {
					isChatLocked = data.chat_locked;
				}

				// Clean up AI response message - remove quotes if present
				if (aiResponseMessage.startsWith('"') && aiResponseMessage.endsWith('"')) {
					aiResponseMessage = aiResponseMessage.slice(1, -1);
				}
				if (aiResponseMessage.startsWith("'") && aiResponseMessage.endsWith("'")) {
					aiResponseMessage = aiResponseMessage.slice(1, -1);
				}

				// Add AI response
				const aiMessage: ChatMessage = {
					id: (Date.now() + 1).toString(),
					message: aiResponseMessage,
					is_doctor: true,
					timestamp: new Date().toISOString(),
					session_id: currentSession.id,
					assessment_complete: isComplete,
					completion_score: completionScore,
					message_count: messages.length + 1, // Increment message count
				};
				setMessages((prev) => [...prev, aiMessage]);
				setMessageCount(messages.length + 1); // Update message count

				// Update assessment progress and chat lock status
				setAssessmentProgress(completionScore);
				setAssessmentComplete(isComplete);

				// Show completion notification
				if (isComplete && !assessmentComplete) {
					setAssessmentComplete(true);
					showNotification(
						"success",
						"🎉 Assessment complete! The chat is now locked. You can generate your comprehensive medical report."
					);
					// Refresh user context to show updated assessment count
					loadUserContext();
				}

				// Check if we have enough messages for assessment completion (fallback logic)
				if (messages.length >= 10 && !assessmentComplete) {
					setAssessmentComplete(true);
					setAssessmentProgress(100);
					showNotification("success", "🎉 Assessment completed! You can now generate your report.");
				}
			} else {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || `Failed to send message: ${response.status}`);
			}
		} catch (error) {
			console.error("Error sending message:", error);
			showNotification("error", `Failed to send message: ${error instanceof Error ? error.message : "Unknown error"}`);

			// Add error message to chat
			const errorMessage: ChatMessage = {
				id: (Date.now() + 1).toString(),
				message: `Error: ${error instanceof Error ? error.message : "Failed to send message"}`,
				is_doctor: true,
				timestamp: new Date().toISOString(),
				session_id: currentSession.id,
			};
			setMessages((prev) => [...prev, errorMessage]);
		} finally {
			setIsLoading(false);
		}
	};

	const forceCompleteAssessment = async () => {
		if (!currentSession || currentSession.id.startsWith("temp-")) return;

		// Check if the last AI message was a question
		const lastAIMessage = messages.filter((m) => m.is_doctor).pop();
		const lastMessageIsQuestion = lastAIMessage && lastAIMessage.message.trim().endsWith("?");

		if (lastMessageIsQuestion) {
			showNotification("info", "Please answer the AI's question before completing the assessment.");
			return;
		}

		// Only allow completion if we have substantial conversation
		if (messages.length < 6) {
			showNotification(
				"info",
				"Please continue the conversation to gather more information before completing the assessment."
			);
			return;
		}

		try {
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/complete-assessment/${
					currentSession.id
				}`,
				{ method: "POST" }
			);

			if (response.ok) {
				setAssessmentComplete(true);
				setAssessmentProgress(100);
				showNotification("success", "🎉 Assessment completed! You can now generate your report.");
			}
		} catch (error) {
			console.error("Error forcing assessment completion:", error);
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
		setMessages([]);
	};

	const getProgressColor = (score: number) => {
		if (score < 25) return "bg-red-500";
		if (score < 50) return "bg-orange-500";
		if (score < 75) return "bg-yellow-500";
		return "bg-green-500";
	};

	const getProgressText = (score: number) => {
		if (score < 25) return "Initial Assessment";
		if (score < 50) return "Symptom Collection";
		if (score < 75) return "Medical History";
		if (score < 90) return "Risk Assessment";
		return "Final Review";
	};

	// Check if we should show the user context by default
	useEffect(() => {
		if (user && !showUserContext) {
			setShowUserContext(true);
		}
	}, [user]);

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
								onClick={() => {
									loadUserContext();
									loadUserSessions();
								}}
								disabled={userContextLoading || sessionsLoading}
								className="bg-blue-100 hover:bg-blue-200 p-3 rounded-lg transition-colors disabled:opacity-50"
								title="Refresh all data">
								<Loader2
									className={`w-5 h-5 text-blue-600 ${userContextLoading || sessionsLoading ? "animate-spin" : ""}`}
								/>
							</button>

							<button
								onClick={() => setShowUserContext(!showUserContext)}
								className="bg-gray-100 hover:bg-gray-200 p-3 rounded-lg transition-colors"
								title="View User Context">
								<User className="w-5 h-5 text-gray-600" />
							</button>

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
					{messages.length > 0 && (
						<div className="mt-4">
							<div className="flex justify-between items-center mb-2">
								<span className="text-sm font-medium text-gray-700">
									Assessment Progress: {getProgressText(assessmentProgress)}
								</span>
								<span className="text-sm text-gray-500">{Math.round(assessmentProgress)}%</span>
							</div>
							<div className="w-full bg-gray-200 rounded-full h-3">
								<div
									className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(assessmentProgress)}`}
									style={{ width: `${assessmentProgress}%` }}></div>
							</div>

							{/* Context Awareness Indicator */}
							<div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
								<div className="flex items-center space-x-2 text-blue-700 mb-2">
									<Brain className="w-4 h-4" />
									<span className="text-sm font-medium">AI Context Awareness</span>
								</div>
								<div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
									<div className="flex items-center space-x-1">
										<div className="w-2 h-2 bg-green-500 rounded-full"></div>
										<span className="text-green-700">Symptoms</span>
									</div>
									<div className="flex items-center space-x-1">
										<div className="w-2 h-2 bg-blue-500 rounded-full"></div>
										<span className="text-blue-700">Medical History</span>
									</div>
									<div className="flex items-center space-x-1">
										<div className="w-2 h-2 bg-purple-500 rounded-full"></div>
										<span className="text-purple-700">Risk Factors</span>
									</div>
									<div className="flex items-center space-x-1">
										<div className="w-2 h-2 bg-orange-500 rounded-full"></div>
										<span className="text-orange-700">Hearing</span>
									</div>
								</div>
								<p className="text-xs text-blue-600 mt-2">
									💡 The AI remembers everything you tell it and builds upon previous responses
								</p>
							</div>

							<p className="text-xs text-gray-500 mt-1">
								{assessmentProgress < 25 && "Starting assessment - describing symptoms..."}
								{assessmentProgress >= 25 && assessmentProgress < 50 && "Collecting detailed symptom information..."}
								{assessmentProgress >= 50 && assessmentProgress < 75 && "Gathering medical history and background..."}
								{assessmentProgress >= 75 && assessmentProgress < 90 && "Assessing risk factors and lifestyle..."}
								{assessmentProgress >= 90 && "Finalizing assessment and preparing report..."}
							</p>

							{/* Completion Ready Indicator */}
							{isAssessmentReadyForCompletion(messages, assessmentProgress) && !assessmentComplete && (
								<div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
									<div className="flex items-center space-x-2 text-yellow-700">
										<CheckCircle className="w-4 h-4" />
										<span className="text-sm font-medium">Assessment ready for completion! Click below to finish.</span>
									</div>
									<button
										onClick={forceCompleteAssessment}
										className="mt-2 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
										Complete Assessment
									</button>
								</div>
							)}

							{/* Progress Tips */}
							<div className="mt-2 text-xs text-blue-600">
								{assessmentProgress < 25 && "💡 Describe your main symptoms and concerns in detail"}
								{assessmentProgress >= 25 &&
									assessmentProgress < 50 &&
									"💡 Provide information about symptom severity, duration, and triggers"}
								{assessmentProgress >= 50 &&
									assessmentProgress < 75 &&
									"💡 Share relevant medical history, medications, and family history"}
								{assessmentProgress >= 75 &&
									assessmentProgress < 90 &&
									"💡 Discuss lifestyle factors, work environment, and risk factors"}
								{assessmentProgress >= 90 &&
									!assessmentComplete &&
									hasPendingQuestions(messages) &&
									"❓ Please answer the AI's question to complete your assessment"}
								{assessmentProgress >= 90 &&
									!assessmentComplete &&
									!hasPendingQuestions(messages) &&
									"💡 Assessment nearly complete - reviewing your information..."}
								{assessmentProgress >= 90 &&
									assessmentComplete &&
									"✅ Assessment complete! You can now generate your report"}
							</div>

							{/* Conversation Memory */}
							{messages.length > 2 && (
								<div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
									<div className="flex items-center space-x-2 text-gray-700 mb-2">
										<MessageSquare className="w-4 h-4" />
										<span className="text-sm font-medium">Conversation Memory</span>
									</div>
									<div className="text-xs text-gray-600 space-y-1">
										<div className="flex items-center space-x-2">
											<span>📝 Topics discussed:</span>
											<span className="font-medium">
												{messages.length >= 4 ? "Symptoms, Health concerns" : "Getting started..."}
											</span>
										</div>
										<div className="flex items-center space-x-2">
											<span>🎯 Current focus:</span>
											<span className="font-medium">
												{assessmentProgress < 25
													? "Understanding your main symptoms"
													: assessmentProgress < 50
													? "Exploring symptom details"
													: assessmentProgress < 75
													? "Medical background"
													: assessmentProgress < 90
													? "Risk factors & lifestyle"
													: "Final review"}
											</span>
										</div>
										<div className="flex items-center space-x-2">
											<span>💬 Messages exchanged:</span>
											<span className="font-medium">{messages.length}</span>
										</div>
									</div>
								</div>
							)}
						</div>
					)}
				</div>

				<div className="grid lg:grid-cols-4 gap-6">
					{/* User Context Sidebar */}
					{showUserContext && (
						<div className="lg:col-span-1">
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center justify-between">
									<div className="flex items-center space-x-2">
										<User className="w-5 h-5 text-blue-600" />
										<span>Your Profile</span>
									</div>
									<button
										onClick={loadUserContext}
										disabled={userContextLoading}
										className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
										title="Refresh profile data">
										<Loader2 className={`w-4 h-4 text-gray-600 ${userContextLoading ? "animate-spin" : ""}`} />
									</button>
								</h3>

								{userContextLoading ? (
									<div className="space-y-4">
										<div className="flex items-center justify-center py-4">
											<Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
											<span className="ml-2 text-gray-600">Loading profile data...</span>
										</div>
										<div className="space-y-2">
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
												<span>Loading profile information...</span>
											</div>
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
												<span>Loading symptoms data...</span>
											</div>
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
												<span>Loading hearing test results...</span>
											</div>
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
												<span>Loading assessment history...</span>
											</div>
										</div>
									</div>
								) : userContextError ? (
									<div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
										<AlertCircle className="w-6 h-6 text-red-600 mx-auto mb-3" />
										<p className="text-red-800 font-medium">{userContextError}</p>
										<p className="text-red-600 text-sm mt-2 mb-3">
											Please try refreshing or contact support if the issue persists.
										</p>
										<button
											onClick={loadUserContext}
											className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
											Retry
										</button>
									</div>
								) : (
									<>
										{/* Profile Summary Card */}
										<div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 mb-4">
											<div className="text-center">
												<div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
													<User className="w-8 h-8 text-blue-600" />
												</div>
												<h4 className="font-semibold text-gray-800 text-lg">{userContext?.name || "Patient"}</h4>
												<p className="text-sm text-gray-600">Medical Assessment</p>
											</div>
										</div>

										{/* Profile Details */}
										<div className="space-y-4">
											{/* Age & Gender */}
											<div className="grid grid-cols-2 gap-3">
												<div className="bg-gray-50 rounded-lg p-3 text-center">
													<Calendar className="w-5 h-5 text-gray-500 mx-auto mb-1" />
													<p className="text-xs text-gray-500">Age</p>
													<p className="font-semibold text-gray-800">
														{userContext?.age ? `${userContext.age} years` : "Not set"}
													</p>
												</div>
												<div className="bg-gray-50 rounded-lg p-3 text-center">
													<User className="w-5 h-5 text-gray-500 mx-auto mb-1" />
													<p className="text-xs text-gray-500">Gender</p>
													<p className="font-semibold text-gray-800">{userContext?.gender || "Not set"}</p>
												</div>
											</div>

											{/* Health Stats */}
											<div className="space-y-3">
												<div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
													<div className="flex items-center space-x-2">
														<Activity className="w-4 h-4 text-green-600" />
														<span className="text-sm text-gray-600">Symptoms</span>
													</div>
													<span className="font-semibold text-green-600">
														{userContext?.existing_symptoms?.length || 0}
													</span>
												</div>

												<div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
													<div className="flex items-center space-x-2">
														<Brain className="w-4 h-4 text-purple-600" />
														<span className="text-sm text-gray-600">Assessments</span>
													</div>
													<span className="font-semibold text-purple-600">
														{userContext?.previous_assessments || 0}
													</span>
												</div>

												<div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
													<div className="flex items-center space-x-2">
														<Headphones className="w-4 h-4 text-orange-600" />
														<span className="text-sm text-gray-600">Hearing</span>
													</div>
													<span className="font-semibold text-orange-600">
														{userContext?.hearing_status || "Not tested"}
													</span>
												</div>
											</div>

											{/* Last Assessment */}
											{userContext?.last_assessment_date && (
												<div className="bg-blue-50 rounded-lg p-3">
													<div className="flex items-center space-x-2 mb-2">
														<Calendar className="w-4 h-4 text-blue-600" />
														<span className="text-sm font-medium text-blue-800">Last Assessment</span>
													</div>
													<p className="text-sm text-blue-700">
														{new Date(userContext.last_assessment_date).toLocaleDateString()}
													</p>
												</div>
											)}

											{/* Symptoms List */}
											{userContext?.existing_symptoms && userContext.existing_symptoms.length > 0 && (
												<div className="bg-yellow-50 rounded-lg p-3">
													<div className="flex items-center space-x-2 mb-2">
														<Activity className="w-4 h-4 text-yellow-600" />
														<span className="text-sm font-medium text-yellow-800">Reported Symptoms</span>
													</div>
													<div className="space-y-1">
														{userContext.existing_symptoms.map((symptom, index) => (
															<div key={index} className="text-xs text-yellow-700 bg-yellow-100 px-2 py-1 rounded">
																• {symptom}
															</div>
														))}
													</div>
												</div>
											)}
										</div>

										<p className="text-xs text-gray-500 mt-4 text-center">
											This information helps personalize your assessment experience.
										</p>
									</>
								)}
							</div>
						</div>
					)}

					{/* Sessions Sidebar */}
					{showSessions && (
						<div className="lg:col-span-1">
							<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
								<div className="flex items-center space-x-2 mb-4">
									<MessageSquare className="w-5 h-5 text-purple-600" />
									<h3 className="text-lg font-semibold text-gray-800">Your Sessions</h3>
									<button
										onClick={loadUserSessions}
										disabled={sessionsLoading}
										className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
										title="Refresh sessions">
										<Loader2 className={`w-4 h-4 text-gray-600 ${sessionsLoading ? "animate-spin" : ""}`} />
									</button>
								</div>

								{sessionsLoading ? (
									<div className="space-y-4">
										<div className="flex items-center justify-center py-4">
											<Loader2 className="w-6 h-6 text-purple-600 animate-spin" />
											<span className="ml-2 text-gray-600">Loading sessions...</span>
										</div>
										<div className="space-y-2">
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
												<span>Loading session history...</span>
											</div>
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
												<span>Loading session details...</span>
											</div>
											<div className="flex items-center space-x-2 text-sm text-gray-500">
												<div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
												<span>Loading assessment status...</span>
											</div>
										</div>
									</div>
								) : sessionError ? (
									<div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
										<AlertCircle className="w-6 h-6 text-red-600 mx-auto mb-3" />
										<p className="text-red-800 font-medium">{sessionError}</p>
										<p className="text-red-600 text-sm mt-2 mb-3">
											Please try refreshing or contact support if the issue persists.
										</p>
										<button
											onClick={loadUserSessions}
											className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
											Retry
										</button>
									</div>
								) : (
									<>
										{/* Session Stats */}
										<div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-4 mb-4">
											<div className="text-center">
												<p className="text-2xl font-bold text-purple-600">{sessions.length}</p>
												<p className="text-sm text-purple-700">Total Sessions</p>
											</div>
										</div>

										{/* Sessions List */}
										<div className="space-y-3 mb-4">
											{sessions.map((session) => (
												<button
													key={session.id}
													onClick={() => {
														setCurrentSession(session);
														loadSessionMessages(session.id);
														setShowSessions(false);
													}}
													className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
														currentSession?.id === session.id
															? "border-purple-500 bg-purple-50 shadow-md"
															: "border-gray-200 hover:border-purple-300 hover:shadow-sm"
													}`}>
													<div className="flex items-start justify-between mb-2">
														<div className="font-medium text-gray-800 text-sm leading-tight">
															{session.session_name}
														</div>
														<div className={`w-3 h-3 rounded-full ${getProgressColor(session.completion_score)}`}></div>
													</div>
													<div className="text-xs text-gray-500 mb-2">
														{new Date(session.created_at).toLocaleDateString()}
													</div>
													<div className="flex items-center space-x-2">
														<div className="flex-1 bg-gray-200 rounded-full h-2">
															<div
																className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(
																	session.completion_score
																)}`}
																style={{ width: `${session.completion_score}%` }}></div>
														</div>
														<span className="text-xs font-medium text-gray-600">{session.completion_score}%</span>
													</div>
													{session.assessment_complete && (
														<div className="mt-2 flex items-center space-x-1">
															<CheckCircle className="w-3 h-3 text-green-600" />
															<span className="text-xs text-green-600 font-medium">Complete</span>
														</div>
													)}
													{session.message_count >= 10 && (
														<div className="mt-2 flex items-center space-x-1">
															<Lock className="w-3 h-3 text-blue-600" />
															<span className="text-xs text-blue-600 font-medium">Limit Reached</span>
														</div>
													)}
												</button>
											))}
										</div>

										<button
											onClick={startNewAssessment}
											className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 px-4 rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 font-medium shadow-lg">
											<Plus className="w-4 h-4 inline mr-2" />
											Start New Assessment
										</button>
									</>
								)}
							</div>
						</div>
					)}

					{/* Chat Interface */}
					<div className={`${showSessions || showUserContext ? "lg:col-span-3" : "lg:col-span-4"}`}>
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
													<span>I'll acknowledge your existing symptoms and context</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>We'll explore your symptoms in detail without repetition</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>I'll ask relevant follow-up questions based on your responses</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>Our conversation will be personalized and context-aware</span>
												</div>
												<div className="flex items-start space-x-2">
													<div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
													<span>Assessment typically takes 10-15 minutes</span>
												</div>
											</div>
										</div>

										<p className="text-sm text-gray-400 mt-4">
											Start by describing your main symptoms or health concerns below. I'll remember everything you tell
											me and build upon it.
										</p>
									</div>
								) : (
									messages.map((message) => (
										<div key={message.id} className={`flex ${message.is_doctor ? "justify-start" : "justify-end"}`}>
											<div
												className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
													message.is_doctor ? "bg-blue-100 text-gray-800" : "bg-blue-600 text-white"
												}`}>
												{/* Format AI messages with proper line breaks and natural flow */}
												{message.is_doctor ? (
													<div className="whitespace-pre-wrap text-sm leading-relaxed">{message.message}</div>
												) : (
													<p className="text-sm">{message.message}</p>
												)}

												{/* Context Awareness Indicator for AI messages */}
												{message.is_doctor && messages.length > 2 && (
													<div className="mt-2 pt-2 border-t border-blue-200">
														<div className="flex items-center space-x-1 text-xs text-blue-600">
															<Brain className="w-3 h-3" />
															<span>Context-aware response</span>
														</div>
													</div>
												)}

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
							{!assessmentComplete ? (
								<div className="border-t border-gray-200 p-4">
									{/* Message Limit Indicator */}
									<div className="mb-3 text-center">
										<div className="text-sm text-gray-600 mb-1">
											Messages: {messageCount}/{maxMessages}
										</div>
										<div className="w-full bg-gray-200 rounded-full h-2">
											<div
												className="bg-blue-600 h-2 rounded-full transition-all duration-300"
												style={{ width: `${(messageCount / maxMessages) * 100}%` }}></div>
										</div>
									</div>

									{/* Question Indicator */}
									<div className="mb-3 text-center">
										<div className="inline-flex items-center space-x-2 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
											<Brain className="w-4 h-4" />
											<span>AI Medical Assessment</span>
										</div>
									</div>

									<form onSubmit={sendMessage} className="flex space-x-3">
										<input
											type="text"
											value={inputMessage}
											onChange={(e) => setInputMessage(e.target.value)}
											placeholder="Describe your symptoms or health concerns..."
											disabled={isLoading || messageCount >= maxMessages}
											className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
										/>
										<button
											type="submit"
											disabled={isLoading || !inputMessage.trim() || messageCount >= maxMessages}
											className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2">
											<Send className="w-4 h-4" />
											<span>Send</span>
										</button>
									</form>

									{messageCount >= maxMessages && (
										<div className="mt-3 text-center text-sm text-blue-600">
											Message limit reached. You can now generate your report or start a new assessment.
										</div>
									)}
								</div>
							) : (
								<div className="border-t border-gray-200 p-6 text-center">
									<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
										<Lock className="w-12 h-12 text-blue-600 mx-auto mb-3" />
										<h3 className="text-lg font-semibold text-blue-800 mb-2">Chat Locked 🔒</h3>
										<p className="text-blue-700 mb-4">
											Your medical assessment is complete and the chat is now locked. You can generate your
											comprehensive medical report below.
										</p>
									</div>
								</div>
							)}
						</div>

						{/* Assessment Status */}
						{assessmentComplete && (
							<div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6">
								<div className="flex items-center space-x-3">
									<Lock className="w-8 h-8 text-blue-600" />
									<div>
										<h3 className="text-lg font-semibold text-blue-800">Assessment Complete & Chat Locked! 🔒</h3>
										<p className="text-blue-700">
											Your AI medical assessment is complete and the chat is now locked. You can now generate a
											comprehensive report or continue to the hearing test for additional evaluation.
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

									<button
										onClick={startNewAssessment}
										className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2">
										<span>Start New Assessment</span>
									</button>
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
