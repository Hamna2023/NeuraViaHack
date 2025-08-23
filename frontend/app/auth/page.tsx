"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const router = useRouter();

  const handleRegister = async (
    email: string,
    password: string,
    age: number,
    gender: string
  ) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { age, gender } },
    });

    if (error) {
      console.error(error.message);
      alert("Registration failed: " + error.message);
    } else {
      console.log("Registered user:", data.user);
      alert("Registered successfully!");
      router.push("/"); // redirect to home
    }
  };

  const handleLogin = async (email: string, password: string) => {
    // 🚨 Fake mode: skip Supabase completely
    const fakeMode = true;

    if (fakeMode) {
      console.log("Pretend login success:", email);
      alert("Login successful! (FAKE)");
      router.push("/"); // redirect to home
      return { user: { email, name: "Test User" } };
    }

    // 🔑 Real Supabase login
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      console.error(error.message);
      alert("Login failed: " + error.message);
      return null;
    } else {
      console.log("Logged in:", data.user);
      
      router.push("/"); // redirect to home
      return data.user;
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-indigo-100 to-blue-200">
      <form
        className="bg-white p-8 rounded-2xl shadow-xl w-96 space-y-5 border border-gray-200"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget as HTMLFormElement;
          const email = (form.elements.namedItem("email") as HTMLInputElement)
            .value;
          const password = (
            form.elements.namedItem("password") as HTMLInputElement
          ).value;

          if (isLogin) {
            await handleLogin(email, password);
          } else {
            const age = parseInt(
              (form.elements.namedItem("age") as HTMLInputElement).value,
              10
            );
            const gender = (
              form.elements.namedItem("gender") as HTMLSelectElement
            ).value;
            await handleRegister(email, password, age, gender);
          }
        }}
      >
        <h2 className="text-2xl font-bold text-center text-gray-800">
          {isLogin ? "Login" : "Register"}
        </h2>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            name="email"
            type="email"
            required
            className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none"
          />
        </div>

        {/* Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            name="password"
            type="password"
            required
            className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none"
          />
        </div>

        {/* Extra fields only for Register */}
        {!isLogin && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Age
              </label>
              <input
                name="age"
                type="number"
                min="0"
                required
                className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Gender
              </label>
              <select
                name="gender"
                required
                className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400 focus:outline-none"
              >
                <option value="">Select...</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="nonbinary">Non-binary</option>
                <option value="prefer_not_say">Prefer not to say</option>
              </select>
            </div>
          </>
        )}

        {/* Submit button */}
        <button
          type="submit"
          className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          {isLogin ? "Login" : "Register"}
        </button>

        {/* Switch link */}
        <p className="text-center text-sm text-gray-600">
          {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:underline font-medium"
          >
            {isLogin ? "Register" : "Login"}
          </button>
        </p>
      </form>
    </div>
  );
}
