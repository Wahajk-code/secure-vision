import React, { createContext, useContext, useState, useEffect } from 'react';

// Types
interface User {
    username: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

const parseUserFromToken = (token: string): User | null => {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (!payload?.sub || !payload?.role) {
            return null;
        }
        return { username: payload.sub, role: payload.role };
    } catch (e) {
        console.error("Invalid Token", e);
        return null;
    }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [token, setToken] = useState<string | null>(localStorage.getItem('securevision_token'));
    const [user, setUser] = useState<User | null>(() => {
        const storedToken = localStorage.getItem('securevision_token');
        return storedToken ? parseUserFromToken(storedToken) : null;
    });

    useEffect(() => {
        if (token) {
            const parsedUser = parseUserFromToken(token);
            if (parsedUser) {
                setUser(parsedUser);
            } else {
                logout();
            }
        } else {
            setUser(null);
        }
    }, [token]);

    const login = (newToken: string) => {
        localStorage.setItem('securevision_token', newToken);
        setToken(newToken);
    };

    const logout = () => {
        localStorage.removeItem('securevision_token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token && !!user }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within AuthProvider");
    return context;
};
