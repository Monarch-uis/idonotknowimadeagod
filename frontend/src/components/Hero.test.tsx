import { render, screen } from '@testing-library/react';
import { Hero } from './Hero';
import { describe, it, expect } from 'vitest';

describe('Hero Component', () => {
    it('renders the main title', () => {
        render(<Hero />);
        expect(screen.getByText(/FANFICTION/i)).toBeInTheDocument();
        expect(screen.getByText(/LEGEND/i)).toBeInTheDocument();
    });

    it('contains a video background', () => {
        render(<Hero />);
        const video = screen.getByTestId('hero-video') as HTMLVideoElement;
        expect(video).toBeInTheDocument();
        expect(video).toHaveAttribute('autoplay');
        expect(video).toHaveAttribute('loop');
        // Check property for muted, as attribute reflection can be flaky in jsdom
        expect(video.muted).toBe(true);
    });
});
