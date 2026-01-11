import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the child components to simplify integration testing
vi.mock('./components/Hero', () => ({
    Hero: () => <div data-testid="mock-hero">Hero Component</div>
}));

// We don't mock Dashboard completely because we want to see if it renders the data passed to it
// But we can check if it receives the right props or just check for the text on screen.

const mockProjectsResponse = {
    active: [
        { id: '1', title: 'API Project 1', author: 'API Author 1', status: 'active', last_updated: '2023-01-01' }
    ],
    archived: [
        { id: '2', title: 'API Project 2', author: 'API Author 2', status: 'archived', last_updated: '2023-01-02' }
    ]
};

describe('App Integration', () => {
    beforeEach(() => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockProjectsResponse
        });
    });

    it('renders Hero and fetches projects for Dashboard', async () => {
        render(<App />);

        // Check Hero
        expect(screen.getByTestId('mock-hero')).toBeInTheDocument();

        // Check loading state (optional, might happen too fast)
        // await waitFor(() => expect(screen.getByText(/loading/i)).toBeInTheDocument());

        // Check that API data eventually appears
        await waitFor(() => {
            expect(screen.getByText(/API Project 1/i)).toBeInTheDocument();
            expect(screen.getByText(/API Project 2/i)).toBeInTheDocument();
        });

        // Verify API call
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/projects');
    });
});
