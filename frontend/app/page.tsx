import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-[80vh] space-y-6">
      <h1 className="text-4xl font-bold">Welcome to NeuraVia</h1>
      <p className="text-gray-600">Choose a feature to get started:</p>
      <div className="space-x-4">
        <Link href="/symptoms" className="px-4 py-2 bg-blue-500 text-white rounded-lg">Symptoms</Link>
        <Link href="/hearing" className="px-4 py-2 bg-green-500 text-white rounded-lg">Hearing</Link>
        <Link href="/chat" className="px-4 py-2 bg-purple-500 text-white rounded-lg">Chat</Link>
      </div>
    </div>
  );
}
