/**
 * Žemperica API — Cloudflare Worker
 * Handles theme suggestions from blog visitors.
 * Stores in KV as pending, awaiting approval.
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    // POST /suggest — submit a theme suggestion
    if (request.method === 'POST' && url.pathname === '/suggest') {
      return handleSuggest(request, env);
    }

    // GET /suggestions — list pending (for review)
    if (request.method === 'GET' && url.pathname === '/suggestions') {
      return handleList(env);
    }

    // GET /themes — public list of active themes
    if (request.method === 'GET' && url.pathname === '/themes') {
      return handleThemes(env);
    }

    // POST /hit — page view counter
    if (request.method === 'POST' && url.pathname === '/hit') {
      return handleHit(request, env);
    }

    // POST /vote — like/dislike a post
    if (request.method === 'POST' && url.pathname === '/vote') {
      return handleVote(request, env);
    }

    // GET /votes?slug=xxx — get votes for a post
    if (request.method === 'GET' && url.pathname === '/votes') {
      const slug = url.searchParams.get('slug');
      if (!slug) return jsonResponse({ error: 'Missing slug' }, 400);
      const likes = parseInt(await env.SUGGESTIONS.get(`votes:${slug}:likes`) || '0');
      const dislikes = parseInt(await env.SUGGESTIONS.get(`votes:${slug}:dislikes`) || '0');
      return jsonResponse({ slug, likes, dislikes });
    }

    // DELETE /suggestion?id=xxx&adminKey=xxx — remove a suggestion
    if (request.method === 'DELETE' && url.pathname === '/suggestion') {
      const id = url.searchParams.get('id');
      const key = url.searchParams.get('adminKey');
      if (key !== env.ADMIN_KEY) return jsonResponse({ error: 'Unauthorized' }, 403);
      if (!id) return jsonResponse({ error: 'Missing id' }, 400);
      await env.SUGGESTIONS.delete(`suggestion:${id}`);
      const index = JSON.parse(await env.SUGGESTIONS.get('index:pending') || '[]');
      const newIndex = index.filter(i => i !== id);
      await env.SUGGESTIONS.put('index:pending', JSON.stringify(newIndex));
      return jsonResponse({ ok: true, deleted: id });
    }

    return new Response('🃏 Žemperica API', {
      headers: { 'Content-Type': 'text/plain; charset=utf-8', ...CORS_HEADERS },
    });
  },
};

async function handleSuggest(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON' }, 400);
  }

  const strip = s => s.replace(/[<>]/g, '');
  const name = strip((body.name || '').trim());
  const prompt = strip((body.prompt || '').trim());
  const author = strip((body.author || 'Anonimni ludak').trim());

  if (!name || name.length < 3 || name.length > 80) {
    return jsonResponse({ error: 'Ime teme: 3-80 znakova' }, 400);
  }
  if (!prompt || prompt.length < 10 || prompt.length > 300) {
    return jsonResponse({ error: 'Prompt: 10-300 znakova' }, 400);
  }
  if (author.length > 50) {
    return jsonResponse({ error: 'Autor: max 50 znakova' }, 400);
  }

  // Admin bypass
  const isAdmin = body.adminKey === (env.ADMIN_KEY || '');

  // Rate limit: max 3 suggestions per IP per day
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const rateKey = `rate:${ip}:${new Date().toISOString().slice(0, 10)}`;
  const rateCount = parseInt(await env.SUGGESTIONS.get(rateKey) || '0');

  if (!isAdmin && rateCount >= 3) {
    return jsonResponse({ error: 'Previše prijedloga danas. Dođi sutra!' }, 429);
  }

  // Store suggestion
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const suggestion = {
    id,
    name,
    prompt,
    author,
    ip,
    status: 'pending',
    createdAt: new Date().toISOString(),
  };

  await env.SUGGESTIONS.put(`suggestion:${id}`, JSON.stringify(suggestion));
  await env.SUGGESTIONS.put(rateKey, String(rateCount + 1), { expirationTtl: 86400 });

  // Update pending index
  const index = JSON.parse(await env.SUGGESTIONS.get('index:pending') || '[]');
  index.push(id);
  await env.SUGGESTIONS.put('index:pending', JSON.stringify(index));

  // Notify via Telegram (fire-and-forget)
  if (env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID) {
    const text = `🃏 NOVI PRIJEDLOG ZA ŽEMPERICU

Tema: ${name}
Prompt: ${prompt}
Autor: ${author}`;
    fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
    }).catch(() => {});
  }

  // Notify n8n webhook (fire-and-forget)
  if (env.N8N_WEBHOOK_URL) {
    fetch(env.N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${env.N8N_WEBHOOK_AUTH}`,
      },
      body: JSON.stringify({ name, prompt, author, createdAt: suggestion.createdAt }),
    }).catch(() => {});
  }

  return jsonResponse({ ok: true, message: 'Hvala! Žemperica će razmotriti tvoj prijedlog. 🃏', id });
}

async function handleList(env) {
  const index = JSON.parse(await env.SUGGESTIONS.get('index:pending') || '[]');
  const suggestions = [];

  for (const id of index) {
    const data = await env.SUGGESTIONS.get(`suggestion:${id}`);
    if (data) suggestions.push(JSON.parse(data));
  }

  return jsonResponse({ suggestions, count: suggestions.length });
}

async function handleThemes(env) {
  // Return count of pending suggestions (public info only)
  const index = JSON.parse(await env.SUGGESTIONS.get('index:pending') || '[]');
  return jsonResponse({ pendingSuggestions: index.length });
}

async function handleVote(request, env) {
  let body;
  try { body = await request.json(); } catch { return jsonResponse({ error: 'Invalid JSON' }, 400); }

  const slug = (body.slug || '').trim();
  const type = body.type; // 'like' or 'dislike'
  if (!slug || (type !== 'like' && type !== 'dislike')) {
    return jsonResponse({ error: 'Need slug and type (like/dislike)' }, 400);
  }

  // One vote per IP per post
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const voteKey = `voted:${slug}:${ip}`;
  const prev = await env.SUGGESTIONS.get(voteKey);

  if (prev) {
    // Already voted — if same type, ignore; if different, switch
    if (prev === type) {
      const likes = parseInt(await env.SUGGESTIONS.get(`votes:${slug}:likes`) || '0');
      const dislikes = parseInt(await env.SUGGESTIONS.get(`votes:${slug}:dislikes`) || '0');
      return jsonResponse({ slug, likes, dislikes, voted: type });
    }
    // Switch vote
    const oldKey = `votes:${slug}:${prev}s`;
    const newKey = `votes:${slug}:${type}s`;
    const oldCount = Math.max(0, parseInt(await env.SUGGESTIONS.get(oldKey) || '0') - 1);
    const newCount = parseInt(await env.SUGGESTIONS.get(newKey) || '0') + 1;
    await env.SUGGESTIONS.put(oldKey, String(oldCount));
    await env.SUGGESTIONS.put(newKey, String(newCount));
    await env.SUGGESTIONS.put(voteKey, type);
    return jsonResponse({ slug, likes: type === 'like' ? newCount : oldCount, dislikes: type === 'dislike' ? newCount : oldCount, voted: type });
  }

  // New vote
  const key = `votes:${slug}:${type}s`;
  const count = parseInt(await env.SUGGESTIONS.get(key) || '0') + 1;
  await env.SUGGESTIONS.put(key, String(count));
  await env.SUGGESTIONS.put(voteKey, type);

  const likes = parseInt(await env.SUGGESTIONS.get(`votes:${slug}:likes`) || '0');
  const dislikes = parseInt(await env.SUGGESTIONS.get(`votes:${slug}:dislikes`) || '0');
  return jsonResponse({ slug, likes, dislikes, voted: type });
}

async function handleHit(request, env) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const key = `visitor:${ip}`;
  const seen = await env.SUGGESTIONS.get(key);

  // Always count page view
  const views = parseInt(await env.SUGGESTIONS.get('stats:views') || '0');
  await env.SUGGESTIONS.put('stats:views', String(views + 1));

  // Count unique visitor only once
  if (!seen) {
    await env.SUGGESTIONS.put(key, '1', { expirationTtl: 86400 * 365 });
    const visitors = parseInt(await env.SUGGESTIONS.get('stats:visitors') || '0');
    await env.SUGGESTIONS.put('stats:visitors', String(visitors + 1));
  }

  return jsonResponse({
    visitors: parseInt(await env.SUGGESTIONS.get('stats:visitors') || '0'),
    views: views + 1
  });
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...CORS_HEADERS },
  });
}
