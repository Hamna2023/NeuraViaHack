"use client";

import React, { useState } from "react";
import {
	FileText,
	Activity,
	AlertTriangle,
	CheckCircle,
	Clock,
	Download,
	Printer,
	Share2,
	Eye,
	EyeOff,
	ChevronDown,
	ChevronUp,
	User,
	Calendar,
	Stethoscope,
	Heart,
	Brain,
	Shield,
	Target,
	ArrowRight,
} from "lucide-react";

interface MedicalReportViewProps {
	report: {
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
		user_context?: any;
		collected_data?: any;
	};
	onBack?: () => void;
}

export default function MedicalReportView({ report, onBack }: MedicalReportViewProps) {
	const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
		executive_summary: true,
		symptom_analysis: true,
		risk_assessment: true,
		hearing_assessment_summary: true,
		recommendations: true,
		follow_up_actions: true,
	});
	const [showFullReport, setShowFullReport] = useState(false);

	const toggleSection = (section: string) => {
		setExpandedSections((prev) => ({
			...prev,
			[section]: !prev[section],
		}));
	};

	const formatDate = (dateString: string) => {
		if (!dateString) return "Not specified";
		try {
			return new Date(dateString).toLocaleDateString("en-US", {
				year: "numeric",
				month: "long",
				day: "numeric",
				hour: "2-digit",
				minute: "2-digit",
			});
		} catch (error) {
			return "Invalid date";
		}
	};

	const getStatusColor = (isComplete: boolean) => {
		return isComplete
			? "bg-green-100 text-green-800 border-green-200"
			: "bg-yellow-100 text-yellow-800 border-yellow-200";
	};

	const getStatusIcon = (isComplete: boolean) => {
		return isComplete ? CheckCircle : Clock;
	};

	const getStageColor = (stage: string) => {
		const stageColors: Record<string, string> = {
			initial: "bg-blue-100 text-blue-800 border-blue-200",
			medical_history: "bg-purple-100 text-purple-800 border-purple-200",
			symptom_analysis: "bg-orange-100 text-orange-800 border-orange-200",
			risk_assessment: "bg-red-100 text-red-800 border-red-200",
			complete: "bg-green-100 text-green-800 border-green-200",
		};
		return stageColors[stage] || "bg-gray-100 text-gray-800 border-gray-200";
	};

	const renderMarkdownContent = (content: string) => {
		if (!content) return null;

		// Simple markdown to HTML conversion for basic formatting
		let htmlContent = content
			// Headers
			.replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-800 mt-4 mb-2">$1</h3>')
			.replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-gray-800 mt-6 mb-3">$1</h2>')
			.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mt-6 mb-4">$1</h1>')
			// Bold and italic
			.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
			.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
			// Lists
			.replace(/^\* (.*$)/gim, '<li class="ml-4 mb-1">• $1</li>')
			.replace(/^- (.*$)/gim, '<li class="ml-4 mb-1">• $1</li>')
			.replace(/^\d+\. (.*$)/gim, '<li class="ml-4 mb-1">$&</li>')
			// Paragraphs
			.replace(/\n\n/g, '</p><p class="mb-3">')
			.replace(/\n/g, "<br>");

		// Wrap in paragraph tags
		htmlContent = `<p class="mb-3">${htmlContent}</p>`;

		// Handle lists properly
		htmlContent = htmlContent
			.replace(/(<li.*?<\/li>)+/g, '<ul class="list-disc ml-6 mb-3 space-y-1">$&</ul>')
			.replace(/<\/p><ul/g, "</p><ul")
			.replace(/<\/ul><p/g, "</ul><p");

		return <div className="prose prose-gray max-w-none" dangerouslySetInnerHTML={{ __html: htmlContent }} />;
	};

	const renderSection = (
		key: string,
		title: string,
		content: string,
		icon: React.ComponentType<any>,
		color: string
	) => {
		if (!content) return null;

		const isExpanded = expandedSections[key];
		const Icon = icon;

		return (
			<div key={key} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
				<button
					onClick={() => toggleSection(key)}
					className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
					<div className="flex items-center space-x-3">
						<div className={`p-2 rounded-lg ${color}`}>
							<Icon className="w-5 h-5" />
						</div>
						<h3 className="text-lg font-semibold text-gray-900">{title}</h3>
					</div>
					{isExpanded ? (
						<ChevronUp className="w-5 h-5 text-gray-500" />
					) : (
						<ChevronDown className="w-5 h-5 text-gray-500" />
					)}
				</button>

				{isExpanded && (
					<div className="px-6 pb-4 border-t border-gray-100">
						<div className="pt-4">{renderMarkdownContent(content)}</div>
					</div>
				)}
			</div>
		);
	};

	const renderUserContext = () => {
		if (!report.user_context) return null;

		const context = report.user_context;
		return (
			<div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
				<h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center space-x-2">
					<User className="w-5 h-5 text-blue-600" />
					<span>Patient Information</span>
				</h2>
				<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
					{context.age && (
						<div className="text-center p-3 bg-blue-50 rounded-lg">
							<p className="text-sm text-gray-500">Age</p>
							<p className="font-semibold text-blue-600">{context.age} years</p>
						</div>
					)}
					{context.gender && (
						<div className="text-center p-3 bg-purple-50 rounded-lg">
							<p className="text-sm text-gray-500">Gender</p>
							<p className="font-semibold text-purple-600">{context.gender}</p>
						</div>
					)}
					{context.hearing_status && (
						<div className="text-center p-3 bg-green-50 rounded-lg">
							<p className="text-sm text-gray-500">Hearing Status</p>
							<p className="font-semibold text-green-600">{context.hearing_status}</p>
						</div>
					)}
					{context.previous_assessments && (
						<div className="text-center p-3 bg-orange-50 rounded-lg">
							<p className="text-sm text-gray-500">Previous Assessments</p>
							<p className="font-semibold text-orange-600">{context.previous_assessments}</p>
						</div>
					)}
					{/* Show additional context if available */}
					{context.existing_symptoms && context.existing_symptoms.length > 0 && (
						<div className="text-center p-3 bg-red-50 rounded-lg">
							<p className="text-sm text-gray-500">Previous Symptoms</p>
							<p className="font-semibold text-red-600">{context.existing_symptoms.length} recorded</p>
						</div>
					)}
					{context.last_assessment_date && (
						<div className="text-center p-3 bg-indigo-50 rounded-lg">
							<p className="text-sm text-gray-500">Last Assessment</p>
							<p className="font-semibold text-indigo-600">{formatDate(context.last_assessment_date)}</p>
						</div>
					)}
				</div>
			</div>
		);
	};

	const renderCollectedData = () => {
		if (!report.collected_data) return null;

		const data = report.collected_data;
		return (
			<div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
				<h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center space-x-2">
					<Activity className="w-5 h-5 text-green-600" />
					<span>Assessment Data</span>
				</h2>
				<div className="grid md:grid-cols-2 gap-6">
					{data.symptoms && data.symptoms.length > 0 && (
						<div>
							<h3 className="font-medium text-gray-700 mb-2">Identified Symptoms</h3>
							<div className="space-y-1">
								{data.symptoms.map((symptom: string, index: number) => (
									<div key={index} className="flex items-center space-x-2">
										<div className="w-2 h-2 bg-red-500 rounded-full"></div>
										<span className="text-sm text-gray-600">{symptom}</span>
									</div>
								))}
							</div>
						</div>
					)}
					{data.medical_history && data.medical_history.length > 0 && (
						<div>
							<h3 className="font-medium text-gray-700 mb-2">Medical History</h3>
							<div className="space-y-1">
								{data.medical_history.map((item: string, index: number) => (
									<div key={index} className="flex items-center space-x-2">
										<div className="w-2 h-2 bg-blue-500 rounded-full"></div>
										<span className="text-sm text-gray-600">{item}</span>
									</div>
								))}
							</div>
						</div>
					)}
					{data.risk_factors && data.risk_factors.length > 0 && (
						<div>
							<h3 className="font-medium text-gray-700 mb-2">Risk Factors</h3>
							<div className="space-y-1">
								{data.risk_factors.map((factor: string, index: number) => (
									<div key={index} className="flex items-center space-x-2">
										<div className="w-2 h-2 bg-orange-500 rounded-full"></div>
										<span className="text-sm text-gray-600">{factor}</span>
									</div>
								))}
							</div>
						</div>
					)}
					{data.hearing_concerns && data.hearing_concerns.length > 0 && (
						<div>
							<h3 className="font-medium text-gray-700 mb-2">Hearing Concerns</h3>
							<div className="space-y-1">
								{data.hearing_concerns.map((concern: string, index: number) => (
									<div key={index} className="flex items-center space-x-2">
										<div className="w-2 h-2 bg-purple-500 rounded-full"></div>
										<span className="text-sm text-gray-600">{concern}</span>
									</div>
								))}
							</div>
						</div>
					)}
				</div>
			</div>
		);
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
			<div className="max-w-6xl mx-auto">
				{/* Header */}
				<div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
					<div className="flex items-start justify-between">
						<div className="flex-1">
							<div className="flex items-center space-x-4 mb-4">
								{onBack && (
									<button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
										<ArrowRight className="w-5 h-5 text-gray-600 rotate-180" />
									</button>
								)}
								<div className="bg-blue-100 p-3 rounded-full">
									<FileText className="w-8 h-8 text-blue-600" />
								</div>
								<div>
									<h1 className="text-3xl font-bold text-gray-900">{report.report_title}</h1>
									<p className="text-gray-600">Comprehensive Medical Assessment Report</p>
								</div>
							</div>

							{/* Report Metadata */}
							<div className="grid md:grid-cols-3 gap-4 mt-6">
								<div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
									<Calendar className="w-5 h-5 text-gray-600" />
									<div>
										<p className="text-sm text-gray-500">Generated</p>
										<p className="font-medium text-gray-900">
											{report.generated_at
												? formatDate(report.generated_at)
												: new Date().toLocaleDateString("en-US", {
														year: "numeric",
														month: "long",
														day: "numeric",
														hour: "2-digit",
														minute: "2-digit",
												  })}
										</p>
									</div>
								</div>

								<div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
									<User className="w-5 h-5 text-gray-600" />
									<div>
										<p className="text-sm text-gray-500">Assessment Stage</p>
										<span
											className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStageColor(
												report.assessment_stage
											)}`}>
											{report.assessment_stage.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
										</span>
									</div>
								</div>

								<div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
									{React.createElement(getStatusIcon(report.is_complete), { className: "w-5 h-5 text-gray-600" })}
									<div>
										<p className="text-sm text-gray-500">Status</p>
										<span
											className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(
												report.is_complete
											)}`}>
											{report.is_complete ? "Complete" : "In Progress"}
										</span>
									</div>
								</div>
							</div>
						</div>

						{/* Action Buttons */}
						<div className="flex flex-col space-y-2 ml-6">
							<button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2">
								<Download className="w-4 h-4" />
								<span>Download PDF</span>
							</button>
							<button className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2">
								<Printer className="w-4 h-4" />
								<span>Print</span>
							</button>
						</div>
					</div>
				</div>

				{/* User Context and Collected Data */}
				{renderUserContext()}
				{renderCollectedData()}

				{/* Report Content */}
				<div className="space-y-6">
					{/* Executive Summary - Always visible */}
					<div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl shadow-lg p-8 text-white">
						<div className="flex items-center space-x-3 mb-4">
							<div className="bg-white/20 p-3 rounded-full">
								<Brain className="w-6 h-6" />
							</div>
							<h2 className="text-2xl font-bold">Executive Summary</h2>
						</div>
						<div className="prose prose-invert max-w-none">
							{renderMarkdownContent(report.executive_summary || "No executive summary available.")}
						</div>
					</div>

					{/* Detailed Sections */}
					<div className="space-y-4">
						{renderSection(
							"symptom_analysis",
							"Symptom Analysis",
							report.symptom_analysis,
							Activity,
							"bg-red-100 text-red-600"
						)}

						{renderSection(
							"risk_assessment",
							"Risk Assessment",
							report.risk_assessment,
							AlertTriangle,
							"bg-orange-100 text-orange-600"
						)}

						{renderSection(
							"hearing_assessment_summary",
							"Hearing Assessment",
							report.hearing_assessment_summary,
							Stethoscope,
							"bg-purple-100 text-purple-600"
						)}

						{renderSection(
							"recommendations",
							"Recommendations",
							report.recommendations,
							Target,
							"bg-green-100 text-green-600"
						)}

						{renderSection(
							"follow_up_actions",
							"Follow-up Actions",
							report.follow_up_actions,
							Heart,
							"bg-blue-100 text-blue-600"
						)}
					</div>

					{/* Quick Actions */}
					{!report.is_complete && (
						<div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
							<div className="flex items-center space-x-3 mb-4">
								<Clock className="w-6 h-6 text-yellow-600" />
								<h3 className="text-lg font-semibold text-yellow-800">Assessment In Progress</h3>
							</div>
							<p className="text-yellow-700 mb-4">
								Your medical assessment is not yet complete. Continue the assessment to generate a comprehensive report.
							</p>
							<button className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2">
								<Brain className="w-4 h-4" />
								<span>Continue Assessment</span>
							</button>
						</div>
					)}

					{/* Report Footer */}
					<div className="bg-white rounded-2xl border border-gray-200 p-6">
						<div className="flex items-center justify-between text-sm text-gray-500">
							<div className="flex items-center space-x-4">
								<span>Report ID: {report.id}</span>
								<span>Created: {formatDate(report.created_at)}</span>
							</div>
							<div className="flex items-center space-x-2">
								<Eye className="w-4 h-4" />
								<span>Medical Report View</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
