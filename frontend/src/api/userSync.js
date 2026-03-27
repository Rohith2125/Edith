import supabase from "./supabase";

/**
 * Syncs the authenticated user into the hr_users table.
 * @param {object} user - The user object from supabase.auth
 * @param {string} nameFromForm - Optional name provided during registration
 */
export async function syncUser(user, nameFromForm = null) {
    if (!user) return null;

    try {
        const name = 
            nameFromForm || 
            user.user_metadata?.full_name || 
            user.user_metadata?.name || 
            user.email.split('@')[0] || 
            "Unknown";

        const { data, error } = await supabase
            .from("hr_users")
            .upsert([
                {
                    id: user.id,
                    name: name,
                    email: user.email,
                }
            ], { onConflict: 'id' });

        if (error) {
            console.error("Error syncing user to hr_users:", error.message);
            return null;
        }

        console.log("✅ User synced to hr_users:", user.email);
        return data;
    } catch (err) {
        console.error("Unexpected error during user sync:", err.message);
        return null;
    }
}
