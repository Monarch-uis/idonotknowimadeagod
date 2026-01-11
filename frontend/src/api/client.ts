import { Project } from '../components/Dashboard';

export interface ProjectListResponse {
    active: Project[];
    archived: Project[];
}

const API_BASE_URL = 'http://localhost:8000/api';

export const fetchProjects = async (): Promise<ProjectListResponse> => {
    const response = await fetch(`${API_BASE_URL}/projects`);
    if (!response.ok) {
        throw new Error('Failed to fetch projects');
    }
    return response.json();
};
