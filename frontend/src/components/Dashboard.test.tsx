import { render, screen } from '@testing-library/react';
import { Dashboard } from './Dashboard';
import type { Project } from './Dashboard';
import { describe, it, expect } from 'vitest';

const mockProjects: Project[] = [
    { id: '1', title: 'The Great Gatsby', author: 'F. Scott Fitzgerald', status: 'active', last_updated: '2023-01-01' },
    { id: '2', title: '1984', author: 'George Orwell', status: 'archived', last_updated: '2023-01-02' },
];

describe('Dashboard Component', () => {
    it('renders project titles', () => {
        render(<Dashboard projects={mockProjects} />);
        expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
        expect(screen.getByText('1984')).toBeInTheDocument();
    });

    it('renders project authors', () => {
        render(<Dashboard projects={mockProjects} />);
        expect(screen.getByText(/F. Scott Fitzgerald/)).toBeInTheDocument();
        expect(screen.getByText(/George Orwell/)).toBeInTheDocument();
    });
    
    it('renders empty state when no projects', () => {
        render(<Dashboard projects={[]} />);
        expect(screen.getByText(/No active projects/i)).toBeInTheDocument();
    });
});
