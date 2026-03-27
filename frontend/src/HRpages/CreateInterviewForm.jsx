import { useState } from "react";
import axios from "axios";
import supabase from "../api/supabase";

const CreateInterviewForm = () => {
    const [formData, setFormData] = useState({
        candidate_name: "",
        candidate_email: "",
        role: "",
        jd: "",
        cutoff_score: 7,
    });
    const [resume, setResume] = useState(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleFileChange = (e) => {
        setResume(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage({ type: "", text: "" });

        if (!resume) {
            setMessage({ type: "error", text: "Please upload a resume." });
            return;
        }

        const { data: { user } } = await supabase.auth.getUser();

        const data = new FormData();
        data.append("candidate_name", formData.candidate_name);
        data.append("candidate_email", formData.candidate_email);
        data.append("role", formData.role);
        data.append("jd", formData.jd);
        data.append("cutoff_score", formData.cutoff_score);
        data.append("resume", resume);
        
        // Add HR User Info
        if (user) {
            data.append("hr_id", user.id);
            data.append("hr_name", user.user_metadata?.full_name || user.email.split('@')[0]);
            data.append("hr_email", user.email);
        }

        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        setLoading(true);
        try {
            const response = await axios.post(`${apiUrl}/create-interview`, data, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });

            if (response.status === 200 || response.status === 201) {
                setMessage({ type: "success", text: "Interview created successfully" });
                setFormData({
                    candidate_name: "",
                    candidate_email: "",
                    role: "",
                    jd: "",
                    cutoff_score: 7,
                });
                setResume(null);
                // Reset file input
                e.target.reset();
            }
        } catch (error) {
            console.error(error);
            setMessage({
                type: "error",
                text: error.response?.data?.detail || "Error creating interview",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md w-full border border-gray-200 rounded-lg p-6 shadow-sm bg-white">
            <h2 className="text-xl font-semibold mb-6">Create Interview</h2>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Candidate Name</label>
                    <input
                        type="text"
                        name="candidate_name"
                        value={formData.candidate_name}
                        onChange={handleChange}
                        required
                        className="p-2 border border-gray-300 rounded focus:border-blue-500 focus:outline-none"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Candidate Email</label>
                    <input
                        type="email"
                        name="candidate_email"
                        value={formData.candidate_email}
                        onChange={handleChange}
                        required
                        className="p-2 border border-gray-300 rounded focus:border-blue-500 focus:outline-none"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Resume (PDF only)</label>
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        required
                        className="p-2 border border-gray-300 rounded focus:border-blue-500 focus:outline-none"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Role</label>
                    <input
                        type="text"
                        name="role"
                        value={formData.role}
                        onChange={handleChange}
                        required
                        className="p-2 border border-gray-300 rounded focus:border-blue-500 focus:outline-none"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Job Description</label>
                    <textarea
                        name="jd"
                        value={formData.jd}
                        onChange={handleChange}
                        required
                        className="p-2 border border-gray-300 rounded focus:border-blue-500 focus:outline-none min-h-32"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Cutoff Score</label>
                    <input
                        type="number"
                        name="cutoff_score"
                        value={formData.cutoff_score}
                        onChange={handleChange}
                        className="p-2 border border-gray-300 rounded focus:border-blue-500 focus:outline-none"
                    />
                </div>

                {message.text && (
                    <div className={`p-3 rounded text-sm ${message.type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                        {message.text}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white font-semibold py-2 rounded mt-2 hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
                >
                    {loading ? "Creating interview..." : "Create Interview"}
                </button>
            </form>
        </div>
    );
};

export default CreateInterviewForm;
