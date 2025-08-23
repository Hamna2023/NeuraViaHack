import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-screen space-y-6">
      <h1 className="text-3xl font-bold">Welcome to NeuraVia</h1>
      <p className="text-gray-600">Start your guided workflow</p>
      <Link
        href="/symptoms"
        className="px-6 py-3 bg-blue-600 text-white rounded-lg"
      >
        Begin →
      </Link>
    </div>
  );
}
