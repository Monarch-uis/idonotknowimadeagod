import type { Project } from '../components/Dashboard';

export interface ProjectListResponse {
    active: Project[];
    archived: Project[];
}

export interface SystemOptions {
    engines: string[];
    voices: Record<string, string[]>;
    quality_presets: string[];
    speeds: string[];
}

const API_BASE_URL = 'http://localhost:8000/api';

export const fetchProjects = async (): Promise<ProjectListResponse> => {
    const response = await fetch(`${API_BASE_URL}/projects`);
    if (!response.ok) {
        throw new Error('Failed to fetch projects');
    }
    return response.json();
};

export const fetchSystemOptions = async (): Promise<SystemOptions> => {
    const response = await fetch(`${API_BASE_URL}/system/options`);
    if (!response.ok) {
        throw new Error('Failed to fetch system options');
    }
    return response.json();
};

export const uploadProject = async (file: File): Promise<Project> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
    }

    return response.json();
};

export const startProjectProcessing = async (projectId: string, settings?: any): Promise<{ status: string; job_id: string }> => {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/process`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ settings }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start processing');
    }

    return response.json();
};
