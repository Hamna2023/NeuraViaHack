"use client";
import React, { useState } from "react";

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

  const playTone = (frequency: number) => {
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;

    const panner = new StereoPannerNode(audioCtx, {
      pan: selectedEar === "left" ? -1 : 1,
    });

    oscillator.connect(panner).connect(audioCtx.destination);
    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 1);
  };

  const handleResponse = (heard: boolean) => {
    const frequency = frequencies[step];
    const newResult: TestResult = { ear: selectedEar, frequency, heard };
    setResults((prev) => [...prev, newResult]);

    if (step < frequencies.length - 1) {
      // go to next frequency in the same ear
      setStep(step + 1);
    } else if (selectedEar === "left") {
      // switch to right ear
      setSelectedEar("right");
      setStep(0);
    } else {
      // test finished
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

  React.useEffect(() => {
    if (!testFinished) {
      playTone(frequencies[step]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, selectedEar]);

  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-6">Interactive Hearing Test</h1>

      {!testFinished ? (
        <div className="text-center">
          <p className="mb-4 text-lg">
            Testing <span className="font-semibold">{selectedEar.toUpperCase()} Ear</span>
          </p>
          <p className="mb-6 text-xl">Frequency: {frequencies[step]} Hz</p>

          <div className="flex space-x-6 justify-center">
            <button
              onClick={() => handleResponse(true)}
              className="bg-green-600 px-6 py-3 rounded-lg text-lg hover:bg-green-700"
            >
              ✅ I Heard It
            </button>
            <button
              onClick={() => handleResponse(false)}
              className="bg-red-600 px-6 py-3 rounded-lg text-lg hover:bg-red-700"
            >
              ❌ Didn’t Hear
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <h2 className="text-xl font-bold mb-4">Test Results</h2>
          <ul className="space-y-2 mb-6">
            {results.map((r, idx) => (
              <li key={idx}>
                {r.ear.toUpperCase()} Ear – {r.frequency} Hz:{" "}
                <span className={r.heard ? "text-green-400" : "text-red-400"}>
                  {r.heard ? "Heard" : "Not Heard"}
                </span>
              </li>
            ))}
          </ul>
          <button
            onClick={startTest}
            className="bg-blue-600 px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            🔄 Restart Test
          </button>
        </div>
      )}
    </div>
  );
}
