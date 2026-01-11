import { render, screen, waitFor } from '@testing-library/react';
import { LogConsole } from './LogConsole';
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('LogConsole Component', () => {
    beforeEach(() => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                project_id: 'test-project',
                logs: ['[ERROR] Failed to parse chapter 1', '[INFO] Retrying...']
            })
        });
    });

    it('renders logs from API', async () => {
        render(<LogConsole projectId="test-project" />);
        
        await waitFor(() => {
            expect(screen.getByText(/Failed to parse chapter 1/)).toBeInTheDocument();
            expect(screen.getByText(/Retrying/)).toBeInTheDocument();
        });
    });

    it('shows empty state when no logs', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ project_id: 'test-project', logs: [] })
        });
        
        render(<LogConsole projectId="test-project" />);
        
        await waitFor(() => {
            expect(screen.getByText(/NO SYSTEM LOGS FOUND/)).toBeInTheDocument();
        });
    });
});
