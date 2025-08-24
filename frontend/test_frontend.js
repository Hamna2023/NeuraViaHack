/**
 * Frontend Test Script for NeuraVia
 * This script tests the frontend functionality and API integration
 */

// Test configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
let TEST_USER_ID = null; // Will be set after user profile creation
const TEST_EMAIL = `test_${Date.now()}@example.com`; // Unique email each time

// Test functions
async function testBackendConnection() {
	console.log("🔍 Testing backend connection...");
	try {
		const response = await fetch(`${API_BASE_URL}/health`);
		if (response.ok) {
			const data = await response.json();
			console.log("✅ Backend is running and healthy:", data);
			return true;
		} else {
			console.log("❌ Backend health check failed:", response.status);
			return false;
		}
	} catch (error) {
		console.log("❌ Cannot connect to backend:", error.message);
		return false;
	}
}

async function testUserEndpoints() {
	console.log("\n🔍 Testing user endpoints...");

	try {
		// Test user profile creation
		console.log("Creating test user profile...");
		const profileResponse = await fetch(`${API_BASE_URL}/api/users/profile`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				email: TEST_EMAIL,
				age: 30,
				gender: "prefer_not_say",
			}),
		});

		if (profileResponse.ok) {
			const profileData = await profileResponse.json();
			TEST_USER_ID = profileData.id; // Set the actual user ID
			console.log("✅ User profile created:", TEST_USER_ID);
			return true;
		} else {
			console.log("❌ Failed to create user profile:", profileResponse.status);
			const errorText = await profileResponse.text();
			console.log("   Error details:", errorText);
			return false;
		}
	} catch (error) {
		console.log("❌ User endpoint test failed:", error.message);
		return false;
	}
}

async function testChatEndpoints() {
	console.log("\n🔍 Testing chat endpoints...");

	try {
		// Test creating a chat session
		console.log("Creating test chat session...");
		const sessionResponse = await fetch(`${API_BASE_URL}/api/chat/session`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				user_id: TEST_USER_ID,
				session_name: "Test Session",
			}),
		});

		if (sessionResponse.ok) {
			const sessionData = await sessionResponse.json();
			console.log("✅ Chat session created:", sessionData.id);

			// Test sending a message
			console.log("Sending test message...");
			const messageResponse = await fetch(`${API_BASE_URL}/api/chat/send`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					user_id: TEST_USER_ID,
					message: "Hello, I have a headache",
					session_id: sessionData.id,
				}),
			});

			if (messageResponse.ok) {
				const messageData = await messageResponse.json();
				console.log("✅ Message sent successfully");
				console.log("   AI Response:", messageData.response?.substring(0, 100) + "...");
			} else {
				console.log("❌ Failed to send message:", messageResponse.status);
				const errorText = await messageResponse.text();
				console.log("   Error details:", errorText);
			}

			return sessionData.id;
		} else {
			console.log("❌ Failed to create chat session:", sessionResponse.status);
			const errorText = await sessionResponse.text();
			console.log("   Error details:", errorText);
			return null;
		}
	} catch (error) {
		console.log("❌ Chat endpoint test failed:", error.message);
		return null;
	}
}

async function testSymptomsEndpoints() {
	console.log("\n🔍 Testing symptoms endpoints...");

	try {
		// Test adding a symptom
		console.log("Adding test symptom...");
		const symptomResponse = await fetch(`${API_BASE_URL}/api/symptoms`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				user_id: TEST_USER_ID,
				symptom_name: "Headache",
				severity: 7,
				description: "Moderate headache in the front of the head",
				duration_days: 2,
			}),
		});

		if (symptomResponse.ok) {
			const symptomData = await symptomResponse.json();
			console.log("✅ Symptom added:", symptomData.id);
		} else {
			console.log("❌ Failed to add symptom:", symptomResponse.status);
			const errorText = await symptomResponse.text();
			console.log("   Error details:", errorText);
		}
	} catch (error) {
		console.log("❌ Symptoms endpoint test failed:", error.message);
	}
}

async function testHearingEndpoints() {
	console.log("\n🔍 Testing hearing endpoints...");

	try {
		// Test adding a hearing test
		console.log("Adding test hearing test...");
		const hearingResponse = await fetch(`${API_BASE_URL}/api/hearing/test`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				user_id: TEST_USER_ID,
				left_ear_score: 85,
				right_ear_score: 90,
				overall_score: 87,
				test_type: "standard",
				notes: "Test hearing assessment",
			}),
		});

		if (hearingResponse.ok) {
			const hearingData = await hearingResponse.json();
			console.log("✅ Hearing test added:", hearingData.id);
		} else {
			console.log("❌ Failed to add hearing test:", hearingResponse.status);
			const errorText = await hearingResponse.text();
			console.log("   Error details:", errorText);
		}
	} catch (error) {
		console.log("❌ Hearing endpoint test failed:", error.message);
	}
}

async function runAllTests() {
	console.log("🚀 Starting NeuraVia Frontend Tests");
	console.log("=".repeat(50));

	// Test 1: Backend connection
	const backendConnected = await testBackendConnection();
	if (!backendConnected) {
		console.log("\n❌ Backend is not running. Please start the backend first:");
		console.log("   cd backend");
		console.log("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000");
		return;
	}

	// Test 2: User profile creation FIRST (required for other tests)
	console.log("\n📋 Creating user profile first (required for other tests)...");
	const userCreated = await testUserEndpoints();
	if (!userCreated) {
		console.log("\n❌ Cannot proceed with other tests - user profile creation failed");
		return;
	}

	// Test 3: Chat functionality (now user exists)
	await testChatEndpoints();

	// Test 4: Symptoms functionality (now user exists)
	await testSymptomsEndpoints();

	// Test 5: Hearing functionality (now user exists)
	await testHearingEndpoints();

	console.log("\n" + "=".repeat(50));
	console.log("✅ Frontend tests completed!");
}

// Run tests if this script is executed directly
if (typeof window === "undefined") {
	// Node.js environment - using native fetch (Node.js 18+)
	runAllTests().catch(console.error);
} else {
	// Browser environment
	console.log("🌐 Running in browser environment");
	console.log("Open the browser console to see test results");

	// Make test functions available globally for browser testing
	window.testNeuraVia = {
		testBackendConnection,
		testChatEndpoints,
		testUserEndpoints,
		testSymptomsEndpoints,
		testHearingEndpoints,
		runAllTests,
	};

	console.log("Test functions available at window.testNeuraVia");
}
