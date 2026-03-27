import { useEffect } from "react";
import CreateInterviewForm from "./CreateInterviewForm";
import supabase from "../api/supabase";
import { syncUser } from "../api/userSync";

const HRDashboard = () => {
    useEffect(() => {
        const checkAndSync = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                await syncUser(user);
            }
        };
        checkAndSync();
    }, []);

    return (
        <div className="p-8 max-w-4xl mx-auto flex flex-col items-center">
            <h1 className="text-3xl font-bold mb-8">HR Dashboard</h1>
            
            <div className="w-full flex justify-center">
                <CreateInterviewForm />
            </div>
        </div>
    );
};

export default HRDashboard;
