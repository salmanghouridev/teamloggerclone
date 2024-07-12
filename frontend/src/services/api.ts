// src/services/api.ts

export async function fetchUserData(username: string) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const response = await fetch(`${apiUrl}/utl/v1/user/${username}/combined`);

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to fetch user data');
    }

    const data = await response.json();
    return data;
}
