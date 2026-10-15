import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import POS from './POS';
import { vi } from 'vitest';

// Mock the api module to return empty arrays immediately
vi.mock('../api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: {} }))
  }
}));

describe('POS Mount Test', () => {
  it('should mount and render the main UI without crashing', async () => {
    try {
      const { container } = render(
        <BrowserRouter>
          <POS />
        </BrowserRouter>
      );
      // Wait for the spinner to disappear
      await waitFor(() => {
        const spinner = container.querySelector('.spinner-border');
        if (spinner) throw new Error("Spinner still here");
      }, { timeout: 3000 });
      
      console.log("RENDER SUCCESS (Past Spinner)!");
      // If we made it here, no unhandled exceptions were thrown during the main render!
    } catch (e) {
      console.error("RENDER FAILED:", e.message);
      throw e;
    }
  });
});
