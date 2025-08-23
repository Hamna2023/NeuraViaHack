"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react"; 
import Link from "next/link";

type Symptom = {
  name: string;
  severity: number;
  description: string;
};

export default function SymptomForm() {
  const [symptoms, setSymptoms] = useState<Symptom[]>([
    { name: "", severity: 5, description: "" },
  ]);

  // Handle updating a field in one symptom
  const handleChange = (index: number, field: keyof Symptom, value: string | number) => {
    const updated = [...symptoms];
    updated[index][field] = value as never;
    setSymptoms(updated);
  };

  // Add new empty symptom
  const addSymptom = () => {
    setSymptoms([...symptoms, { name: "", severity: 5, description: "" }]);
  };

  // Remove a symptom
  const removeSymptom = (index: number) => {
    const updated = symptoms.filter((_, i) => i !== index);
    setSymptoms(updated);
  };

  // Submit handler (connect to backend later)
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Submitting symptoms:", symptoms);
    // TODO: POST to backend API
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-2xl shadow-lg border border-gray-300">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Report Symptoms</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {symptoms.map((symptom, index) => (
          <div key={index} className="p-4 border border-gray-300 rounded-lg bg-gray-50 relative">
            <h3 className="font-semibold text-gray-800 mb-2">Symptom {index + 1}</h3>

            {/* Symptom Name */}
            <label className="block text-sm font-medium text-gray-900 mb-1">
              Name
            </label>
            <input
              type="text"
              value={symptom.name}
              onChange={(e) => handleChange(index, "name", e.target.value)}
              className="w-full rounded-lg border border-gray-400 px-3 py-2 mb-2 text-gray-900
                         focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="e.g. Headache"
            />

            {/* Severity */}
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Severity
            </label>
            <div className="flex justify-between gap-2">
              {[...Array(10)].map((_, i) => {
                const value = i + 1;
                // Color gradient from green → yellow → red
                const bgColor =
                  value <= 3 ? "bg-green-400" :
                  value <= 6 ? "bg-yellow-400" :
                  value <= 8 ? "bg-orange-400" :
                  "bg-red-500";

                return (
                  <button
                    key={value}
                    type="button"
                    onClick={() => handleChange(index, "severity", value)}
                    className={`flex-1 py-2 rounded-md text-white font-medium transition 
                              ${bgColor} 
                              ${symptom.severity === value ? "ring-2 ring-black scale-105" : "opacity-70 hover:opacity-100"}`}
                  >
                    {value}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {symptom.severity <= 3 && "Mild"} 
              {symptom.severity >= 4 && symptom.severity <= 6 && "Moderate"} 
              {symptom.severity >= 7 && symptom.severity <= 8 && "Severe"} 
              {symptom.severity >= 9 && "Very Severe"}
            </p>


            {/* Description */}
            <label className="block text-sm font-medium text-gray-900 mb-1">
              Description
            </label>
            <textarea
              value={symptom.description}
              onChange={(e) => handleChange(index, "description", e.target.value)}
              className="w-full rounded-lg border border-gray-400 px-3 py-2 text-gray-900
                         focus:outline-none focus:ring-2 focus:ring-indigo-600"
              placeholder="Add details..."
            />

            {/* Remove Button */}
            {symptoms.length > 1 && (
              <button
              type="button"
              onClick={() => removeSymptom(index)}
              className="text-red-500 hover:text-red-700 transition"
              aria-label="Remove symptom"
            >
              <Trash2 size={18} />
            </button>
            )}
          </div>
        ))}

        {/* Add More Button */}
        <button
          type="button"
          onClick={addSymptom}
          className="w-full bg-gray-100 border border-gray-400 text-gray-700 font-medium py-2 rounded-lg
                     hover:bg-gray-200 transition"
        >
          + Add Another Symptom
        </button>

        {/* Submit */}
        <button
          type="submit"
          className="w-full bg-indigo-600 text-white font-medium py-2 px-4 rounded-lg shadow-md
                     hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Submit All Symptoms
        </button>
        <div className="mt-6 flex justify-end">
        <Link
          href="/hearing"
          className="bg-green-600 text-white px-6 py-2 rounded-lg"
        >
          Continue →
        </Link>
      </div>
      </form>
    </div>
  );
}
