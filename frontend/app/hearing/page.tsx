"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
  } from "recharts";

type TestResult = {
  ear: "left" | "right";
  frequency: number;
  heard: boolean;
};

export default function HearingTest() {
  const frequencies = [250, 500, 1000, 2000, 4000, 8000]; // test frequencies
  const [selectedEar, setSelectedEar] = useState<"left" | "right">("left");
  const [step, setStep] = useState(0);
  const [results, setResults] = useState<TestResult[]>([]);
  const [testFinished, setTestFinished] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const playTone = (frequency: number) => {
    const audioCtx = new (window.AudioContext ||
      (window as any).webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;

    const panner = new StereoPannerNode(audioCtx, {
      pan: selectedEar === "left" ? -1 : 1,
    });

    oscillator.connect(panner).connect(audioCtx.destination);
    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 1);

    setIsPlaying(true);
    setTimeout(() => setIsPlaying(false), 1000);
  };

  const handleResponse = (heard: boolean) => {
    const frequency = frequencies[step];
    const newResult: TestResult = { ear: selectedEar, frequency, heard };
    setResults((prev) => [...prev, newResult]);

    if (step < frequencies.length - 1) {
      setStep(step + 1);
    } else if (selectedEar === "left") {
      setSelectedEar("right");
      setStep(0);
    } else {
      setTestFinished(true);
    }
  };

  const startTest = () => {
    setStep(0);
    setResults([]);
    setSelectedEar("left");
    setTestFinished(false);
    playTone(frequencies[0]);
  };

  useEffect(() => {
    if (!testFinished) {
      playTone(frequencies[step]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, selectedEar]);

  // Transform results for chart
  const chartData = frequencies.map((f) => {
    const left = results.find((r) => r.frequency === f && r.ear === "left");
    const right = results.find((r) => r.frequency === f && r.ear === "right");
    return {
      frequency: `${f} Hz`,
      Left: left ? (left.heard ? 1 : 0) : null,
      Right: right ? (right.heard ? 1 : 0) : null,
    };
  });

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 via-teal-50 to-purple-50 p-6">
      <h1 className="text-3xl font-semibold text-gray-800 mb-4">
        🎧 Interactive Hearing Test
      </h1>
      <p className="text-gray-600 mb-8">
        Relax, put on your headphones, and follow the steps.
      </p>

      {!testFinished ? (
        <div className="bg-white shadow-lg rounded-2xl p-8 max-w-md w-full text-center">
          <p className="mb-2 text-gray-700">
            Now testing your{" "}
            <span className="font-medium capitalize">{selectedEar} ear</span>
          </p>
          <p className="text-lg text-gray-900 mb-6">
            Frequency: <span className="font-semibold">{frequencies[step]} Hz</span>
          </p>

          {/* Tone animation */}
          <div className="flex justify-center mb-6">
            <div
              className={`w-20 h-20 rounded-full border-4 border-blue-300 ${
                isPlaying ? "animate-ping bg-blue-200" : "bg-blue-100"
              }`}
            ></div>
          </div>

          <div className="flex space-x-4 justify-center">
            <button
              onClick={() => handleResponse(true)}
              className="px-6 py-3 rounded-xl text-lg bg-green-100 text-green-700 hover:bg-green-200 transition"
            >
              ✅ Heard it
            </button>
            <button
              onClick={() => handleResponse(false)}
              className="px-6 py-3 rounded-xl text-lg bg-red-100 text-red-600 hover:bg-red-200 transition"
            >
              ❌ Didn’t hear
            </button>
          </div>
        </div>
      ) : (
        <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl p-6">
          <h2 className="text-xl font-bold mb-4 text-center">Your Hearing Results</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="frequency" />
              <YAxis ticks={[0, 1]} domain={[0, 1]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="Left" stroke="#4ade80" strokeWidth={3} dot={{ r: 6 }} />
              <Line type="monotone" dataKey="Right" stroke="#60a5fa" strokeWidth={3} dot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>

          <div className="flex justify-between mt-6">
            <button
              onClick={startTest}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition"
            >
              🔄 Restart Test
            </button>
            <Link
              href="/chat"
              className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition"
            >
              Continue →
            </Link>
          </div>
        </div>
      )} 

      
    </div>
  );
}
