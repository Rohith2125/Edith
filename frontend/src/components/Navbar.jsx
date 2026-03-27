import { Link, useNavigate } from "react-router-dom";
import supabase from "../api/supabase";

const Navbar = () => {
    const navigate = useNavigate();

    const handleLogout = async () => {
        try {
            const { error } = await supabase.auth.signOut();
            if (error) throw error;
            navigate("/login");
        } catch (error) {
            console.error("Error signing out:", error.message);
        }
    };

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-100 shadow-sm backdrop-blur-md bg-white/80">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    {/* Logo */}
                    <Link to="/hr-dashboard" className="flex items-center gap-2">
                        <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                            EDITH
                        </span>
                        <span className="hidden sm:inline-block text-xs font-medium text-gray-400 border border-gray-100 px-1.5 py-0.5 rounded">
                            HR Suite
                        </span>
                    </Link>

                    {/* Navigation Links */}
                    <div className="hidden md:flex flex-1 justify-center gap-8">
                        <Link 
                            to="/hr-dashboard" 
                            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
                        >
                            HR Dashboard
                        </Link>
                        <Link 
                            to="/history" 
                            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
                        >
                            Interview History
                        </Link>
                        <Link 
                            to="/interview" 
                            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
                        >
                            Candidate View
                        </Link>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-4">
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 text-sm font-semibold text-white bg-black rounded-lg hover:bg-gray-800 transition-all shadow-sm"
                        >
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
