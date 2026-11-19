import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import youtube_api as a
import youtube_playlist as p

KEY = 'AIzaFIXTUREkeyFIXTUREkeyFIXTUREkey12345'


def video(vid, duration, published, title='Episode', desc='First line\n\nSecond'):
    return {'id': vid, 'contentDetails': {'duration': duration}, 'snippet': {'title': title, 'publishedAt': published, 'description': desc}}


class ApiTests(unittest.TestCase):
    def fetcher(self, pages, videos):
        calls = []
        def fetch(endpoint, params):
            calls.append((endpoint, dict(params)))
            if endpoint == 'playlistItems':
                return json.dumps(pages[params.get('pageToken', '')])
            wanted = params['id'].split(',')
            return json.dumps({'items': [v for v in videos if v['id'] in wanted]})
        return fetch, calls

    def test_pages_durations_private_and_dates(self):
        pages = {'': {'items': [{'contentDetails': {'videoId': 'aaaaaaaaaa1'}}, {'contentDetails': {'videoId': 'aaaaaaaaaa2'}}], 'nextPageToken': 'P2'},
                 'P2': {'items': [{'contentDetails': {'videoId': 'aaaaaaaaaa3'}}, {'contentDetails': {'videoId': 'aaaaaaaaaa4'}}]}}
        videos = [video('aaaaaaaaaa1', 'PT26M10S', '2026-11-19T02:00:33Z', 'Full show'),
                  video('aaaaaaaaaa2', 'PT12M47S', '2026-02-26T02:00:00Z', 'Segment'),
                  video('aaaaaaaaaa4', 'PT1H2M', '2026-03-19T02:04:06Z', 'Long')]  # aaaaaaaaaa3 is private: no details
        fetch, calls = self.fetcher(pages, videos)
        found = a.full_episodes('PLx', KEY, fetch=fetch)
        self.assertEqual([v['youtubeId'] for v in found], ['aaaaaaaaaa1', 'aaaaaaaaaa4'])
        self.assertEqual(found[0]['date'], '2026-11-18', '7 p.m. Wednesday in Arizona, not Thursday UTC')
        self.assertEqual(found[0]['description'], 'First line')
        self.assertEqual(found[1]['seconds'], 3720)
        self.assertEqual([c[0] for c in calls], ['playlistItems', 'playlistItems', 'videos'])

    def test_empty_playlist_and_bad_duration_fail(self):
        fetch, _ = self.fetcher({'': {'items': []}}, [])
        with self.assertRaises(p.PlaylistError):
            a.full_episodes('PLx', KEY, fetch=fetch)
        with self.assertRaises(p.PlaylistError):
            a.duration_seconds('26:10')
        self.assertEqual(a.duration_seconds('PT24M'), 1440)

    def test_errors_never_include_the_key(self):
        body = io.BytesIO(json.dumps({'error': {'message': 'API key not valid.'}}).encode())
        err = urllib.error.HTTPError(a.API + 'videos?key=' + KEY, 400, 'Bad Request', {}, body)
        with patch.object(a.urllib.request, 'urlopen', side_effect=err):
            with self.assertRaises(p.PlaylistError) as caught:
                a._call('videos', {'id': 'x'}, KEY)
        self.assertNotIn(KEY, str(caught.exception))
        self.assertIsNone(caught.exception.__cause__)
        self.assertIn('API key not valid', str(caught.exception))

    def test_workflow_without_key_refuses_page_scraping(self):
        import update_episodes as u
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'YOUTUBE_API_KEY': ''}), patch.object(u, 'full_episodes') as scrape:
            with self.assertRaises(RuntimeError):
                u.fetch_full_episodes()
            scrape.assert_not_called()


if __name__ == '__main__':
    unittest.main()
