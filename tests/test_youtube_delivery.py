import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import youtube_delivery as y
AGENT='11111111-1111-4111-8111-111111111111'
ENV={'YOUTUBE_AGENT_ID':AGENT,'YOUTUBE_AGENT_TOKEN':'genai_agent_'+AGENT+'.'+'a'*43}
EP={'title':'Fixture video','youtubeId':'aaaaaaaaaaa','date':'2026-11-18','description':'Description'}
class DeliveryTests(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,ENV);self.env.start();self.addCleanup(self.env.stop)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'outbox.json'
 def prepare(self):return y.prepare([(EP,'')],self.path,'123',call=lambda *_:{'data':{'records':[]}})
 def test_deduplication_and_no_secret_in_file(self):
  box=y.prepare([(EP,''),(EP,'')],self.path,'123',call=lambda *_:{'data':{'records':[]}})
  self.assertEqual(len(box['requests']),1);self.assertNotIn(ENV['YOUTUBE_AGENT_TOKEN'],self.path.read_text())
  with self.assertRaises(FileExistsError):y.prepare([],self.path,'123',call=lambda *_:{'data':{'records':[]}})
 def test_original_keys_survive_failure_and_recovery(self):
  self.prepare();original=self.path.read_bytes();keys=[]
  def lost(op,p,key):keys.append(key);raise y.DeliveryError('lost')
  with self.assertRaises(y.DeliveryError):y.deliver(self.path,'123',Path(self.tmp.name)/'lost.json',call=lost)
  def ok(op,p,key):keys.append(key);return {'status':'ok','data':{'id':'recExisting'},'unchanged':True}
  rows=y.deliver(self.path,'123',Path(self.tmp.name)/'receipts.json',call=ok)
  self.assertEqual(keys[0],keys[1]);self.assertEqual(original,self.path.read_bytes());self.assertTrue(rows[0]['unchanged'])
 def test_wrong_run_or_replacement_identity_refused(self):
  self.prepare()
  with self.assertRaises(y.DeliveryError):y.load(self.path,'999')
  with patch.dict(os.environ,{'YOUTUBE_AGENT_ID':'22222222-2222-4222-8222-222222222222'}):
   with self.assertRaises(y.DeliveryError):y.load(self.path,'123')
 def test_warning_or_error_stops_remaining_saves(self):
  self.prepare();calls=[]
  def call(*a):calls.append(a);return {'status':'ok','warning':'receipt unknown','data':{'id':'recOne'}}
  with self.assertRaises(y.DeliveryError):y.deliver(self.path,'123',Path(self.tmp.name)/'bad.json',call=call)
  self.assertEqual(len(calls),1)
 def test_bad_saved_operation_refused_before_any_call(self):
  self.prepare();box=json.loads(self.path.read_text());box['requests'][0]['operation']='settings.update';self.path.write_text(json.dumps(box))
  with self.assertRaises(y.DeliveryError):y.load(self.path,'123')
 def test_invalid_or_oversized_payload_refused_before_delivery(self):
  self.prepare();box=json.loads(self.path.read_text());box['requests'][0]['params']['fields']['Description']='世'*9000;self.path.write_text(json.dumps(box))
  with self.assertRaises(y.DeliveryError):y.load(self.path,'123')
 def test_existing_airtable_mode_is_unchanged(self):
  import update_episodes as u
  with patch.dict(os.environ,{'YOUTUBE_DATA_BACKEND':'airtable','AIRTABLE_API_KEY':'fixture','AIRTABLE_BASE_ID':'appFixture'}),patch.object(sys,'argv',['update_episodes.py']),patch.object(u,'parse_youtube_rss',return_value=[EP]),patch.object(u,'scrape_azfamily_links',return_value=[]),patch.object(u,'write_episodes_to_airtable',return_value=0) as write:
   self.assertEqual(u.main(),0);write.assert_called_once_with([(EP,'')],'appFixture','fixture')
 def test_main_dashboard_requires_preparation_and_cannot_fall_back(self):
  import update_episodes as u
  with patch.dict(os.environ,{'YOUTUBE_DATA_BACKEND':'dashboard'}),patch.object(sys,'argv',['update_episodes.py']),patch.object(u,'parse_youtube_rss') as fetch:
   with self.assertRaises(SystemExit):u.main()
   fetch.assert_not_called()
if __name__=='__main__':unittest.main()
