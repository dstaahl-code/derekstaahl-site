import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import youtube_playlist as p


def lockup(vid, title, badge):
    return {'lockupViewModel': {'contentId': vid, 'contentImage': {'thumbnailViewModel': {'overlays': [{'thumbnailBottomOverlayViewModel': {'badges': [{'thumbnailBadgeViewModel': {'text': badge}}]}}]}},
                                'metadata': {'lockupMetadataViewModel': {'title': {'content': title}}}}}


def page(items, extra_sections=()):
    data = {'contents': {'twoColumnBrowseResultsRenderer': {'tabs': [{'tabRenderer': {'content': {'sectionListRenderer': {'contents': [
        {'itemSectionRenderer': {'contents': [{'playlistVideoListRenderer': {'contents': items}}]}}, *extra_sections]}}}}]}}}
    return 'x<script>var ytInitialData = ' + json.dumps(data) + ';</script>"INNERTUBE_CLIENT_VERSION":"2.20261118"'


def watch(vid, title, published, desc):
    player = {'videoDetails': {'videoId': vid, 'title': title, 'shortDescription': desc}, 'microformat': {'playerMicroformatRenderer': {'publishDate': published}}}
    return '<script>var ytInitialPlayerResponse = ' + json.dumps(player) + ';var meta = 1;</script>'


SECTION_CONTINUATION = {'continuationItemViewModel': {'continuationCommand': {'token': 'NOT-VIDEOS'}}}


class PlaylistTests(unittest.TestCase):
    def test_full_episodes_only_and_other_sections_ignored(self):
        html = page([lockup('aaaaaaaaaa1', 'Full show', '26:10'), lockup('aaaaaaaaaa2', 'Segment', '12:47'),
                     lockup('aaaaaaaaaa3', 'Exactly 24', '24:00'), lockup('aaaaaaaaaa4', 'Short', '0:49')], [SECTION_CONTINUATION])
        calls = []
        def fetch(url, data):
            calls.append(url)
            return html
        found = p.full_episodes('PLx', fetch=fetch)
        self.assertEqual([v['youtubeId'] for v in found], ['aaaaaaaaaa1', 'aaaaaaaaaa3'])
        self.assertEqual(len(calls), 1, 'a section continuation is not a page of videos')

    def test_long_playlist_follows_its_own_continuation(self):
        first = page([lockup('bbbbbbbbbb1', 'One', '26:00'), {'continuationItemRenderer': {'continuationEndpoint': {'continuationCommand': {'token': 'MORE'}}}}])
        more = json.dumps({'onResponseReceivedActions': [{'appendContinuationItemsAction': {'continuationItems': [
            {'playlistVideoRenderer': {'videoId': 'bbbbbbbbbb2', 'title': {'runs': [{'text': 'Two'}]}, 'lengthSeconds': '1560'}}]}}]})
        posted = []
        def fetch(url, data):
            if data:
                posted.append(data['continuation'])
                return more
            return first
        self.assertEqual([v['youtubeId'] for v in p.full_episodes('PLx', fetch=fetch)], ['bbbbbbbbbb1', 'bbbbbbbbbb2'])
        self.assertEqual(posted, ['MORE'])

    def test_unreadable_pages_fail_instead_of_reporting_nothing_new(self):
        with self.assertRaises(p.PlaylistError):
            p.full_episodes('PLx', fetch=lambda u, d: '<html>consent page</html>')
        with self.assertRaises(p.PlaylistError):
            p.full_episodes('PLx', fetch=lambda u, d: page([]))
        with self.assertRaises(p.PlaylistError):
            p.full_episodes('PLx', fetch=lambda u, d: page([lockup('ccccccccccc', 'No time', None)]))

    def test_details_use_the_arizona_date_and_first_paragraph(self):
        html = watch('ddddddddddd', 'Voters call for changes', '2026-11-18T18:00:33-08:00', 'Para one\nline two\nhttps://x.example\n\nPara two')
        v = p.video_details({'youtubeId': 'ddddddddddd', 'title': 'Playlist title', 'seconds': 1596}, fetch=lambda u, d: html)
        self.assertEqual(v['date'], '2026-11-18', '7 p.m. Arizona, not the next UTC day')
        self.assertEqual(v['dateFormatted'], 'November 18, 2026')
        self.assertEqual(v['description'], 'Para one line two')
        self.assertEqual(p.arizona_date('2026-02-12T02:00:06+00:00'), '2026-02-11')
        with self.assertRaises(p.PlaylistError):
            p.video_details({'youtubeId': 'eeeeeeeeeee', 'title': 't', 'seconds': 1600}, fetch=lambda u, d: html)


class RetryTests(unittest.TestCase):
    def test_429_is_retried_then_succeeds_and_other_errors_raise(self):
        import urllib.error
        from unittest.mock import patch
        answers = [urllib.error.HTTPError('u', 429, 'Too Many Requests', {}, None), 'ok']
        class Resp:
            def __init__(self, text): self.text = text
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return self.text.encode()
        def opener(req, timeout):
            item = answers.pop(0)
            if isinstance(item, Exception): raise item
            return Resp(item)
        with patch.object(p.urllib.request, 'urlopen', opener), patch.object(p.time, 'sleep') as slept:
            self.assertEqual(p._get('https://example.test'), 'ok')
            slept.assert_called_once_with(10)
        with patch.object(p.urllib.request, 'urlopen', side_effect=urllib.error.HTTPError('u', 404, 'Not Found', {}, None)), patch.object(p.time, 'sleep'):
            with self.assertRaises(urllib.error.HTTPError):
                p._get('https://example.test')
        with patch.object(p.urllib.request, 'urlopen', side_effect=urllib.error.HTTPError('u', 429, 'Too Many', {}, None)), patch.object(p.time, 'sleep') as slept:
            with self.assertRaises(urllib.error.HTTPError):
                p._get('https://example.test')
            self.assertEqual([c.args[0] for c in slept.call_args_list], [10, 30, 60])


if __name__ == '__main__':
    unittest.main()
