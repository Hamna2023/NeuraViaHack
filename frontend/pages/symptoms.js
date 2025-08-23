import React, { useState, useEffect } from "react";
import { symptomsAPI } from "../services/api";

export default function Symptoms() {
	const [symptoms, setSymptoms] = useState([]);
	const [newSymptom, setNewSymptom] = useState({
		user_id: "user_1",
		symptom_name: "",
		severity: 5,
		description: "",
		category: "neurological",
	});
	const [report, setReport] = useState(null);

	useEffect(() => {
		loadSymptoms();
		loadReport();
	}, []);

	const loadSymptoms = async () => {
		try {
			const response = await symptomsAPI.getUserSymptoms("user_1");
			setSymptoms(response.data);
		} catch (error) {
			console.error("Error loading symptoms:", error);
		}
	};

	const loadReport = async () => {
		try {
			const response = await symptomsAPI.getReport("user_1");
			setReport(response.data);
		} catch (error) {
			console.error("Error loading report:", error);
		}
	};

	const handleSubmit = async (e) => {
		e.preventDefault();
		try {
			await symptomsAPI.addSymptom(newSymptom);
			setNewSymptom({
				user_id: "user_1",
				symptom_name: "",
				severity: 5,
				description: "",
				category: "neurological",
			});
			loadSymptoms();
			loadReport();
		} catch (error) {
			console.error("Error adding symptom:", error);
		}
	};

	const deleteSymptom = async (id) => {
		try {
			await symptomsAPI.deleteSymptom(id);
			loadSymptoms();
			loadReport();
		} catch (error) {
			console.error("Error deleting symptom:", error);
		}
	};

	return (
		<div className="min-h-screen bg-gray-50 py-8">
			<div className="container mx-auto px-4">
				<h1 className="text-4xl font-bold text-gray-800 mb-8 text-center">Symptom Tracking</h1>

				<div className="grid md:grid-cols-2 gap-8">
					{/* Add Symptom Form */}
					<div className="bg-white p-6 rounded-lg shadow-lg">
						<h2 className="text-2xl font-semibold mb-6 text-blue-600">Add New Symptom</h2>
						<form onSubmit={handleSubmit} className="space-y-4">
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">Symptom Name</label>
								<input
									type="text"
									value={newSymptom.symptom_name}
									onChange={(e) => setNewSymptom({ ...newSymptom, symptom_name: e.target.value })}
									className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
									required
								/>
							</div>

							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">Severity (1-10)</label>
								<input
									type="range"
									min="1"
									max="10"
									value={newSymptom.severity}
									onChange={(e) => setNewSymptom({ ...newSymptom, severity: parseInt(e.target.value) })}
									className="w-full"
								/>
								<span className="text-sm text-gray-500">{newSymptom.severity}/10</span>
							</div>

							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
								<select
									value={newSymptom.category}
									onChange={(e) => setNewSymptom({ ...newSymptom, category: e.target.value })}
									className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
									<option value="neurological">Neurological</option>
									<option value="hearing">Hearing</option>
									<option value="vision">Vision</option>
									<option value="motor">Motor</option>
									<option value="cognitive">Cognitive</option>
								</select>
							</div>

							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
								<textarea
									value={newSymptom.description}
									onChange={(e) => setNewSymptom({ ...newSymptom, description: e.target.value })}
									className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
									rows="3"
								/>
							</div>

							<button
								type="submit"
								className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
								Add Symptom
							</button>
						</form>
					</div>

					{/* Symptom Report */}
					<div className="bg-white p-6 rounded-lg shadow-lg">
						<h2 className="text-2xl font-semibold mb-6 text-green-600">Health Report</h2>
						{report ? (
							<div className="space-y-4">
								<div className="bg-blue-50 p-4 rounded-lg">
									<h3 className="font-semibold text-blue-800">Overall Assessment</h3>
									<p className="text-blue-600">{report.recommendation}</p>
								</div>
								<div className="grid grid-cols-2 gap-4">
									<div className="text-center">
										<div className="text-2xl font-bold text-gray-800">{report.total_symptoms}</div>
										<div className="text-sm text-gray-600">Total Symptoms</div>
									</div>
									<div className="text-center">
										<div className="text-2xl font-bold text-gray-800">{report.average_severity}</div>
										<div className="text-sm text-gray-600">Avg Severity</div>
									</div>
								</div>
								<div className="text-center">
									<div className="text-lg font-semibold text-gray-800">{report.most_common}</div>
									<div className="text-sm text-gray-600">Most Common Category</div>
								</div>
							</div>
						) : (
							<p className="text-gray-500">No report available yet. Add some symptoms to generate a report.</p>
						)}
					</div>
				</div>

				{/* Symptoms List */}
				<div className="mt-8 bg-white p-6 rounded-lg shadow-lg">
					<h2 className="text-2xl font-semibold mb-6 text-purple-600">Your Symptoms</h2>
					{symptoms.length > 0 ? (
						<div className="space-y-4">
							{symptoms.map((symptom) => (
								<div
									key={symptom.id}
									className="border border-gray-200 rounded-lg p-4 flex justify-between items-center">
									<div>
										<h3 className="font-semibold text-gray-800">{symptom.symptom_name}</h3>
										<p className="text-sm text-gray-600">{symptom.description}</p>
										<div className="flex items-center space-x-4 mt-2">
											<span className="text-sm text-gray-500">Severity: {symptom.severity}/10</span>
											<span className="text-sm text-gray-500">Category: {symptom.category}</span>
											<span className="text-sm text-gray-500">{new Date(symptom.timestamp).toLocaleDateString()}</span>
										</div>
									</div>
									<button
										onClick={() => deleteSymptom(symptom.id)}
										className="bg-red-500 text-white px-3 py-1 rounded-md hover:bg-red-600 transition-colors">
										Delete
									</button>
								</div>
							))}
						</div>
					) : (
						<p className="text-gray-500 text-center">No symptoms recorded yet.</p>
					)}
				</div>
			</div>
		</div>
	);
}
