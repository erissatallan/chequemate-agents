// src/app/api/moderate/route.js

import { NextResponse } from 'next/server';

const PERSPECTIVE_KEY = process.env.PERSPECTIVE_KEY;
const XAI_API_KEY = process.env.XAI_API_KEY;
const THRESHOLD = 0.7;

export async function POST(request) {
  try {
    const body = await request.json();
    const { username, message } = body || {};
    if (!username || !message) {
      return NextResponse.json({ error: 'Missing username or message' }, { status: 400 });
    }

    // 1) Call Perspective API to assess toxicity
    const perspective_url = `https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=${PERSPECTIVE_KEY}`;
    const perspective_payload = {
      comment: { text: message },
      languages: ['en'],
      requestedAttributes: { TOXICITY: {} },
    };
    const p_resp = await fetch(perspective_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(perspective_payload),
    });
    const p_data = await p_resp.json();
    const toxicity = (((p_data || {}).attributeScores || {}).TOXICITY || {}).summaryScore?.value || 0.0;

    let flagged = false;
    let suggestion = null;

    // 2) If toxic, generate a polite rewrite via XAI
    if (toxicity > THRESHOLD) {
      flagged = true;
      const prompt = `Rewrite the following message politely without changing its meaning:\n"${message}"\n`;
      const xai_resp = await fetch('https://api.xai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${XAI_API_KEY}`,
        },
        body: JSON.stringify({
          model: 'grok-3-mini',
          messages: [{ role: 'user', content: prompt }],
        }),
      });
      const xai_data = await xai_resp.json();
      suggestion = xai_data?.choices?.[0]?.message?.content || null;
    }

    // 3) Respond
    return NextResponse.json({ flagged, toxicity, suggestion });
  } catch (err) {
    return NextResponse.json({ error: 'Invalid request', details: String(err) }, { status: 400 });
  }
}
