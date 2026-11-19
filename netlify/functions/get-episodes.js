const FIELDS = ['Title','Episode Number','YouTube ID','Air Date','Description','AZFamily URL','Guest','Series','Part'];
const project = row => ({ id: row.id, ...(row.createdTime ? { createdTime: row.createdTime } : {}),
  fields: Object.fromEntries(FIELDS.filter(k => Object.hasOwn(row.fields || {},k)).map(k => [k,row.fields[k]])) });
async function request(url, options={}) {
  const response = await fetch(url,{...options,redirect:'error',signal:AbortSignal.timeout(10000)});
  if (!response.ok) throw new Error('Episode data unavailable');
  return response.json();
}
async function airtableRecords() {
  const base=process.env.AIRTABLE_BASE_ID,key=process.env.AIRTABLE_API_KEY;
  if (!base||!key) throw new Error('Airtable is not configured');
  const records=[],seen=new Set();let offset;
  do {
    const params=new URLSearchParams({filterByFormula:'{Show on Website}=1','sort[0][field]':'Episode Number','sort[0][direction]':'desc',pageSize:'100'});
    FIELDS.forEach(f=>params.append('fields[]',f));if(offset)params.set('offset',offset);
    const data=await request(`https://api.airtable.com/v0/${encodeURIComponent(base)}/YouTube%20Videos?${params}`,{headers:{Authorization:`Bearer ${key}`}});
    if(!Array.isArray(data.records))throw new Error('Invalid episode data');records.push(...data.records.map(project));
    offset=data.offset;if(offset){if(seen.has(offset)||seen.size>=100)throw new Error('Invalid episode pagination');seen.add(offset);}
  }while(offset);
  return records;
}
exports.handler=async function() {
  try {
    const mode=process.env.YOUTUBE_VIDEOS_STORE||'airtable';let records;
    if(mode==='airtable')records=await airtableRecords();
    else if(mode==='managed') {
      const base=(process.env.SUPABASE_URL||'').replace(/\/+$/,'');const key=process.env.SUPABASE_PUBLISHABLE_KEY||'';
      if(base!=='https://wlktkvhgupwwwmewlfgh.supabase.co'||!key.startsWith('sb_publishable_'))throw new Error('Public video feed is not configured');
      const feed=await request(base+'/rest/v1/rpc/genai_youtube_feed',{method:'POST',headers:{apikey:key,'Content-Type':'application/json'},body:'{}'});
      if(feed.backend==='airtable')records=await airtableRecords();
      else if(feed.backend==='supabase'&&Array.isArray(feed.records))records=feed.records.map(project);
      else throw new Error('Invalid video routing');
    }else throw new Error('Unsupported video store');
    return {statusCode:200,headers:{'Content-Type':'application/json','Cache-Control':'public, max-age=300'},body:JSON.stringify(records)};
  }catch{return {statusCode:503,headers:{'Content-Type':'application/json','Cache-Control':'no-store'},body:JSON.stringify({error:'Episode feed is temporarily unavailable'})};}
};
