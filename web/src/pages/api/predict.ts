import type { APIRoute } from 'astro';
import { runRecursiveInference } from '../../lib/inference';
import type { PredictionRequest } from '../../lib/types';

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = (await request.json()) as PredictionRequest;

    const { observations, startTime, steps } = body;

    if (!observations || observations.length !== 8) {
      return new Response(
        JSON.stringify({ error: 'Diperlukan tepat 8 titik observasi.' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (!steps || steps < 1 || steps > 3) {
      return new Response(
        JSON.stringify({ error: 'steps harus 1, 2, atau 3.' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const startDate = new Date(startTime);
    if (isNaN(startDate.getTime())) {
      return new Response(
        JSON.stringify({ error: 'startTime tidak valid.' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const predictions = await runRecursiveInference(observations, startDate, steps);

    return new Response(JSON.stringify({ predictions }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      },
    });
  } catch (err) {
    console.error('[API /predict] Error:', err);
    return new Response(
      JSON.stringify({ error: String(err instanceof Error ? err.message : err) }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
