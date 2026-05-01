import React, { useState, useEffect } from "react";
import AnalysisForm from "./components/AnalysisForm";
import ResultsDisplay from "./components/ResultsDisplay";
import LoadingSpinner from "./components/LoadingSpinner";
import ErrorDisplay from "./components/ErrorDisplay";
import { analyzeText, healthCheck } from "./utils/api";
import "./index.css";

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastText, setLastText] = useState("");
  const [serverReady, setServerReady] = useState(false);

  // Check if backend server is ready on mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        await healthCheck();
        setServerReady(true);
      } catch (err) {
        console.warn("Backend server not ready:", err);
        setServerReady(false);
      }
    };

    checkServer();
    const interval = setInterval(checkServer, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (text) => {
    setLoading(true);
    setError(null);
    setLastText(text);

    try {
      const data = await analyzeText(text);
      setResults(data);
    } catch (err) {
      const errorMessage =
        typeof err === "string"
          ? err
          : err.message || "Failed to analyze text. Please try again.";
      setError(errorMessage);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastText) {
      handleAnalyze(lastText);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                🏛️ Political Text Analyzer
              </h1>
              <p className="text-gray-600 mt-1">
                Analyze tone, detect bias, and summarize political content
              </p>
            </div>
            <div className="text-right">
              {serverReady ? (
                <div className="flex items-center gap-2 text-green-600 font-semibold">
                  <span className="w-3 h-3 bg-green-600 rounded-full animate-pulse"></span>
                  Connected
                </div>
              ) : (
                <div className="flex items-center gap-2 text-red-600 font-semibold">
                  <span className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></span>
                  Connecting...
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Server warning */}
        {!serverReady && (
          <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
            <p className="text-yellow-800 font-semibold mb-1">
              ⚠️ Backend Server Not Ready
            </p>
            <p className="text-yellow-700 text-sm">
              Make sure the FastAPI server is running on localhost:8000. Run:
              <br />
              <code className="bg-yellow-100 px-2 py-1 rounded inline-block mt-1">
                cd backend && uvicorn main:app --reload
              </code>
            </p>
          </div>
        )}

        {/* Form section */}
        <AnalysisForm onSubmit={handleAnalyze} isLoading={loading} />

        {/* Loading spinner */}
        {loading && <LoadingSpinner />}

        {/* Error display */}
        {error && !loading && (
          <ErrorDisplay error={error} onRetry={handleRetry} />
        )}

        {/* Results display */}
        {results && !loading && !error && <ResultsDisplay results={results} />}

        {/* Empty state */}
        {!loading && !results && !error && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-700 mb-2">
              Ready to analyze?
            </h2>
            <p className="text-gray-600">
              Paste political text above to analyze its tone, detect bias, and
              generate a summary.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <p className="text-gray-400">
              Political Text Analysis © 2026 | Powered by Hugging Face
            </p>
            <div className="text-sm text-gray-500">
              <p>API: http://localhost:8000</p>
              <p>Frontend: http://localhost:3000</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
