'use client';

import React, { useState } from 'react';
import { fetchUserData } from '../services/api';
import Image from 'next/image';

const UserPage: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [userData, setUserData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('logs'); // State for managing active tab

    const handleLogin = () => {
        // Fake login check
        if (username === 'admin' && password === 'admin') {
            handleFetchUserData();
        } 
        else if (username === 'abc' && password === 'admin') {
            handleFetchUserData();
        }else {
            setError('Invalid username or password');
            setUserData(null);
        }
    };

    const handleFetchUserData = async () => {
        try {
            const data = await fetchUserData(username);
            // Sort screenshots in descending order by date
            data.screenshots.sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime());
            setUserData(data);
            setError(null);
        } catch (err: any) {
            setError(err.message);
            setUserData(null);
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">Testings</h1>
            <div className="mb-4">
                <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter username"
                    className="p-2 border rounded mr-2"
                />
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="p-2 border rounded mr-2"
                />
                <button
                    onClick={handleLogin}
                    className="bg-blue-500 text-white p-2 rounded"
                >
                    Login
                </button>
            </div>

            {error && <p className="text-red-500 mb-4">{error}</p>}

            {userData && (
                <div>
                    <div className="mb-4">
                        <button
                            className={`p-2 ${activeTab === 'logs' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                            onClick={() => setActiveTab('logs')}
                        >
                            Time Logs
                        </button>
                        <button
                            className={`p-2 ml-2 ${activeTab === 'screenshots' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
                            onClick={() => setActiveTab('screenshots')}
                        >
                            Screenshots
                        </button>
                    </div>

                    {activeTab === 'logs' && (
                        <div>
                            <h2 className="text-xl font-semibold mb-2">User Time Logs</h2>
                            <table className="w-full border-collapse">
                                <thead>
                                    <tr>
                                        <th className="border p-2">ID</th>
                                        <th className="border p-2">Project</th>
                                        <th className="border p-2">Task</th>
                                        <th className="border p-2">Start Time</th>
                                        <th className="border p-2">End Time</th>
                                        <th className="border p-2">Duration</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {userData.time_logs.map((log: any) => (
                                        <tr key={log.id}>
                                            <td className="border p-2">{log.id}</td>
                                            <td className="border p-2">{log.project_name}</td>
                                            <td className="border p-2">{log.task_name}</td>
                                            <td className="border p-2">{log.start_time}</td>
                                            <td className="border p-2">{log.end_time}</td>
                                            <td className="border p-2">{log.duration}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeTab === 'screenshots' && (
                        <div>
                            <h2 className="text-xl font-semibold mb-2">User Screenshots</h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                {userData.screenshots.map((screenshot: any) => (
                                    <div key={screenshot.id} className="border p-2">
                                        <a href={screenshot.url} target="_blank" rel="noopener noreferrer">
                                            <Image src={screenshot.url} alt={screenshot.title} width={500} height={500} className="w-full h-auto" />
                                        </a>
                                        <p>{screenshot.title}</p>
                                        <p>{screenshot.date}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default UserPage;
