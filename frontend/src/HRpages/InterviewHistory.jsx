import { useState, useEffect } from "react";
import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
});

const InterviewHistory = () => {
    const [interviews, setInterviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedReport, setSelectedReport] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        const fetchInterviews = async () => {
            try {
                const response = await api.get("/interviews");
                setInterviews(response.data);
            } catch (err) {
                console.error("Error fetching interviews:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchInterviews();
    }, []);

    const viewReport = async (sessionId) => {
        try {
            const response = await api.get(`/interview-report/${sessionId}`);
            setSelectedReport(response.data);
            setIsModalOpen(true);
        } catch (err) {
            alert("Report not found or not yet generated.");
        }
    };

    if (loading) return <div className="text-center py-10">Loading history...</div>;

    return (
        <div className="w-full max-w-6xl mx-auto p-4">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Interview History</h2>
            
            <div className="overflow-x-auto bg-white rounded-2xl shadow-sm border border-gray-100">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50 border-b border-gray-100">
                            <th className="px-6 py-4 text-sm font-semibold text-gray-600 uppercase tracking-wider">Candidate</th>
                            <th className="px-6 py-4 text-sm font-semibold text-gray-600 uppercase tracking-wider">Role</th>
                            <th className="px-6 py-4 text-sm font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-4 text-sm font-semibold text-gray-600 uppercase tracking-wider">Score</th>
                            <th className="px-6 py-4 text-sm font-semibold text-gray-600 uppercase tracking-wider">Date</th>
                            <th className="px-6 py-4 text-sm font-semibold text-gray-600 uppercase tracking-wider text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {interviews.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="px-6 py-10 text-center text-gray-500">No interviews found.</td>
                            </tr>
                        ) : (
                            interviews.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50/50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{item.candidates?.name || "Unknown"}</div>
                                        <div className="text-xs text-gray-500">{item.candidates?.email}</div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600 font-medium">{item.role}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                                            item.status === 'completed' ? 'bg-green-100 text-green-700' : 
                                            item.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' : 
                                            'bg-blue-100 text-blue-700'
                                        }`}>
                                            {item.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-bold text-gray-800">
                                        {(Array.isArray(item.interview_reports) 
                                            ? item.interview_reports[0]?.overall_score 
                                            : item.interview_reports?.overall_score) ?? "-"}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {new Date(item.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        {item.status === 'completed' && (
                                            <button 
                                                onClick={() => viewReport(item.id)}
                                                className="px-4 py-2 bg-black text-white rounded-xl text-sm font-bold hover:scale-105 active:scale-95 transition-all shadow-md"
                                            >
                                                View Report
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Report Modal */}
            {isModalOpen && selectedReport && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white w-full max-w-3xl rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in duration-300">
                        <div className="bg-gray-900 p-6 flex justify-between items-center text-white">
                            <div>
                                <h3 className="text-xl font-bold">Interview Performance Report</h3>
                                <p className="text-gray-400 text-sm">Session ID: {selectedReport.session_id}</p>
                            </div>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-white text-2xl font-bold">&times;</button>
                        </div>
                        
                        <div className="p-8 max-h-[70vh] overflow-y-auto">
                            <div className="flex items-center gap-6 mb-8 border-b border-gray-100 pb-8">
                                <div className="w-24 h-24 bg-blue-50 rounded-2xl flex flex-col items-center justify-center border border-blue-100">
                                    <span className="text-xs font-bold text-blue-600 uppercase tracking-widest">Score</span>
                                    <span className="text-3xl font-black text-gray-900">{selectedReport.overall_score}</span>
                                    <span className="text-[10px] text-gray-500">out of 10</span>
                                </div>
                                <div className="flex-1">
                                    <div className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-1">Recommendation</div>
                                    <div className={`text-2xl font-black ${selectedReport.recommendation?.toLowerCase().includes('hire') ? 'text-green-600' : 'text-red-500'}`}>
                                        {selectedReport.recommendation}
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-8">
                                <div>
                                    <h4 className="text-sm font-bold text-blue-600 uppercase tracking-widest mb-3">Key Strengths</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedReport.strengths?.split(';').map((s, i) => (
                                            <span key={i} className="bg-green-50 text-green-700 px-4 py-2 rounded-xl text-sm font-medium border border-green-100">
                                                ✓ {s.trim()}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <h4 className="text-sm font-bold text-red-600 uppercase tracking-widest mb-3">Areas for Improvement</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedReport.weaknesses?.split(';').map((w, i) => (
                                            <span key={i} className="bg-red-50 text-red-700 px-4 py-2 rounded-xl text-sm font-medium border border-red-100">
                                                ! {w.trim()}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100">
                                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-3">Professional Summary</h4>
                                    <p className="text-gray-700 leading-relaxed italic">
                                        "{selectedReport.summary}"
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end">
                            <button 
                                onClick={() => setIsModalOpen(false)}
                                className="px-8 py-3 bg-black text-white rounded-2xl font-bold hover:scale-105 active:scale-95 transition-all shadow-lg"
                            >
                                Close Report
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InterviewHistory;
