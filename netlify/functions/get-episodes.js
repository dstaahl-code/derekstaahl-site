exports.handler = async function () {
  const BASE_ID = process.env.AIRTABLE_BASE_ID;
  const API_KEY = process.env.AIRTABLE_API_KEY;

  if (!BASE_ID || !API_KEY) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Missing Airtable configuration' }),
    };
  }

  const params = new URLSearchParams();
  params.set('filterByFormula', '{Show on Website}=1');
  params.set('sort[0][field]', 'Episode Number');
  params.set('sort[0][direction]', 'desc');
  ['Title', 'Episode Number', 'YouTube ID', 'Air Date', 'Description', 'AZFamily URL', 'Guest', 'Series', 'Part'].forEach(
    (f) => params.append('fields[]', f)
  );

  try {
    const resp = await fetch(
      `https://api.airtable.com/v0/${BASE_ID}/YouTube%20Videos?${params}`,
      { headers: { Authorization: `Bearer ${API_KEY}` } }
    );

    if (!resp.ok) {
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'Failed to fetch from Airtable' }),
      };
    }

    const data = await resp.json();

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300',
      },
      body: JSON.stringify(data.records || []),
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal error' }),
    };
  }
};
