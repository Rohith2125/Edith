import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
});

const InterviewPage = () => {
    const { sessionId } = useParams();
    
    // State
    const [status, setStatus] = useState("loading"); // loading, welcome, interviewing, thinking, completed, error
    const [sessionData, setSessionData] = useState(null);
    const [currentQuestion, setCurrentQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [isThinking, setIsThinking] = useState(false);
    const [error, setError] = useState(null);

    // 🔄 Fetch initial session data
    useEffect(() => {
        const fetchSession = async () => {
            try {
                const response = await api.get(`/interview/${sessionId}`);
                setSessionData(response.data);
                setStatus("welcome");
            } catch (err) {
                console.error("Error fetching session:", err);
                setError("Interview session not found or link has expired.");
                setStatus("error");
            }
        };
        fetchSession();
    }, [sessionId]);

    // 🎯 Start Interview
    const startInterview = async () => {
        setIsThinking(true);
        setStatus("thinking");
        try {
            const response = await api.post("/start-interview", { session_id: sessionId });
            setCurrentQuestion(response.data.question);
            setStatus("interviewing");
        } catch (err) {
            console.error("Error starting interview:", err);
            setError("Failed to start interview. Please try again.");
            setStatus("error");
        } finally {
            setIsThinking(false);
        }
    };

    // 🔄 Submit Answer & Get Next Question
    const handleNext = async () => {
        if (!answer.trim()) return;

        setIsThinking(true);
        const previousStatus = status;
        setStatus("thinking");

        try {
            const response = await api.post("/next-question", {
                session_id: sessionId,
                answer: answer
            });

            if (response.data.message === "interview_completed") {
                setStatus("completed");
            } else {
                setCurrentQuestion(response.data.response);
                setAnswer("");
                setStatus("interviewing");
            }
        } catch (err) {
            console.error("Error submitting answer:", err);
            setError("Something went wrong. Please try clicking 'Next' again.");
            setStatus(previousStatus); // Fallback
        } finally {
            setIsThinking(false);
        }
    };

    if (status === "loading") {
        return (
            <div className="min-h-[80vh] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-gray-500 font-medium animate-pulse">Initializing your interview session...</p>
                </div>
            </div>
        );
    }

    if (status === "error") {
        return (
            <div className="min-h-[80vh] flex items-center justify-center px-4 text-center">
                <div className="max-w-md w-full bg-red-50 p-8 rounded-2xl border border-red-100">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button 
                        onClick={() => window.location.reload()}
                        className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-[80vh] container mx-auto px-4 py-12 max-w-4xl">
            {/* Header Info */}
            <div className="mb-12 text-center">
                <div className="inline-block px-4 py-1.5 mb-4 rounded-full bg-blue-50 text-blue-600 text-sm font-semibold tracking-wide uppercase">
                    AI Interview Protocol
                </div>
                <h1 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
                    Welcome, <span className="text-blue-600">{sessionData?.candidate?.name}</span>
                </h1>
                <p className="text-lg text-gray-600">
                    Applying for <span className="font-semibold text-gray-900">{sessionData?.role}</span>
                </p>
            </div>

            <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden min-h-[400px] flex flex-col">
                {/* Progress/Session Context */}
                <div className="bg-gray-50 border-b border-gray-100 px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isThinking ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`}></div>
                        <span className="text-sm font-medium text-gray-500 uppercase tracking-widest">
                            {status === "thinking" ? "EDITH is thinking..." : "System Active"}
                        </span>
                    </div>
                </div>

                <div className="flex-1 p-8 md:p-12 flex flex-col items-center justify-center">
                    {status === "welcome" && (
                        <div className="text-center max-w-lg">
                            <h3 className="text-2xl font-bold text-gray-900 mb-4">Ready to start?</h3>
                            <p className="text-gray-600 mb-8 leading-relaxed">
                                We've analyzed your resume summary based on the {sessionData?.role} role. 
                                Click the button below when you are ready to begin the interview.
                            </p>
                            <button 
                                onClick={startInterview}
                                className="group relative w-full md:w-auto px-10 py-4 bg-black text-white rounded-2xl font-bold text-lg hover:scale-105 active:scale-95 transition-all shadow-lg hover:shadow-2xl overflow-hidden"
                            >
                                <span className="relative z-10">Initiate Interview</span>
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            </button>
                        </div>
                    )}

                    {(status === "interviewing" || status === "thinking") && (
                        <div className="w-full">
                            {/* Question Container */}
                            <div className="mb-10 bg-blue-50/50 p-6 md:p-8 rounded-2xl border-l-4 border-blue-600 animate-in fade-in slide-in-from-left duration-500">
                                <span className="text-blue-600 text-xs font-bold uppercase tracking-widest block mb-2">Current Question</span>
                                <h2 className="text-xl md:text-2xl font-bold text-gray-900 leading-snug lg:leading-normal">
                                    {currentQuestion}
                                </h2>
                            </div>

                            {/* Answer Area */}
                            <div className="space-y-4">
                                <label className="text-sm font-semibold text-gray-500 uppercase tracking-widest ml-1">Your Response</label>
                                <textarea
                                    value={answer}
                                    onChange={(e) => setAnswer(e.target.value)}
                                    placeholder="Type your answer here..."
                                    className="w-full min-h-[160px] p-6 text-lg border-2 border-gray-100 rounded-2xl focus:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-100 transition-all bg-gray-50/30 resize-none placeholder:text-gray-300"
                                    disabled={isThinking}
                                />
                                <div className="flex justify-end pt-4">
                                    <button 
                                        onClick={handleNext}
                                        disabled={isThinking || !answer.trim()}
                                        className="px-12 py-4 bg-blue-600 text-white rounded-2xl font-bold text-lg hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-all shadow-md active:scale-95"
                                    >
                                        {isThinking ? "Sending..." : "Next Question →"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {status === "completed" && (
                        <div className="text-center py-10 animate-in zoom-in duration-500">
                            <div className="text-6xl mb-6">🏆</div>
                            <h2 className="text-3xl font-bold text-gray-900 mb-4">Interview Completed!</h2>
                            <p className="text-gray-600 mb-8 text-lg max-w-md mx-auto leading-relaxed">
                                Thank you for your time. Your responses have been recorded and will be reviewed by the HR team. We'll get back to you soon.
                            </p>
                            <div className="p-6 bg-green-50 rounded-2xl border border-green-100 text-green-800 font-medium inline-block">
                                Status: Response Successfully Logged
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Privacy Note */}
            <p className="mt-8 text-center text-gray-400 text-sm italic">
                Powered by EDITH AI • Your session data is encrypted and handled securely.
            </p>
        </div>
    );
};

export default InterviewPage;
