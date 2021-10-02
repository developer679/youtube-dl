# coding: utf-8
from __future__ import unicode_literals
import time

from .common import InfoExtractor
from ..compat import (
    compat_str
)
from ..utils import (
    mimetype2ext,
    try_get,
    unified_timestamp
)


class LectureTubeIE(InfoExtractor):
    _VALID_URL = r'https?://oc-presentation\.ltcc\.tuwien\.ac\.at/paella/ui/watch.html\?id=(?P<id>[0-9a-z-]+)'
    _TESTS = [{
        'url': 'https://oc-presentation.ltcc.tuwien.ac.at/paella/ui/watch.html?id=32822249-06b9-480e-bc64-05c2c2351ddc',
        'md5': '86e854e991e39c8384d38a9020852777',
        'info_dict': {
            'creator': 'Diverse',
            'duration': 33455839,
            'ext': 'mp4',
            'id': '32822249-06b9-480e-bc64-05c2c2351ddc',
            'series': '0 Diverse Events ("public")',
            'timestamp': 1631685600,
            'title': 'Lehrangebot Architektur WS2021',
            'upload_date': '20210915',
            'url': 'https://oc-presentation.ltcc.tuwien.ac.at/static/mh_default_org/engage-player/32822249-06b9-480e-bc64-05c2c2351ddc/ef62aa92-c8a3-410d-99b1-8f8d0979d8a9/presentation_f051b2de_ffec_4bc3_b83f_09ba21e3c6c0.mp4'
        }
    },
        {
        'url': 'https://oc-presentation.ltcc.tuwien.ac.at/paella/ui/watch.html?id=085ec06c-a5fa-4ea9-9bf4-67dd749a6675',
        'md5': '75267c3d8b3d0bce3860d654202b2fcf',
        'info_dict': {
            'creator': 'Bunny',
            'duration': 634560,
            'ext': 'mp4',
            'formats': [
                {
                    'abr': 64,
                    'asr': 48000,
                    'ext': 'mp4',
                    'fps': 25,
                    'resolution': '640x360',
                    'url': 'https://oc-presentation.ltcc.tuwien.ac.at/static/mh_default_org/engage-player/085ec06c-a5fa-4ea9-9bf4-67dd749a6675/94a00187-42ee-4bc2-91e6-e693f7522cb5/2020_11_20_23_03___Big_Buck_Bunny___Bunny__presenter__OC_Studio_.mp4',
                    'vbr': 741
                },
                {
                    'abr': 129,
                    'asr': 48000,
                    'ext': 'mp4',
                    'fps': 25,
                    'resolution': '1280x720',
                    'url': 'https://oc-presentation.ltcc.tuwien.ac.at/static/mh_default_org/engage-player/085ec06c-a5fa-4ea9-9bf4-67dd749a6675/e19f412f-003b-4336-91d9-1cc51e6ed585/2020_11_20_23_03___Big_Buck_Bunny___Bunny__presenter__OC_Studio_.mp4',
                    'vbr': 1791
                },
                {
                    'abr': 129,
                    'asr': 48000,
                    'ext': 'mp4',
                    'fps': 25,
                    'protocol': 'https',
                    'resolution': '1920x1080',
                    'url': 'https://oc-presentation.ltcc.tuwien.ac.at/static/mh_default_org/engage-player/085ec06c-a5fa-4ea9-9bf4-67dd749a6675/2c5f91e6-838b-46a1-a296-53d612f8fb5a/2020_11_20_23_03___Big_Buck_Bunny___Bunny__presenter__OC_Studio_.mp4',
                    'vbr': 3363
                }
            ],
            'id': '085ec06c-a5fa-4ea9-9bf4-67dd749a6675',
            'series': 'Testvideos public',
            'timestamp': 1605909826,
            'title': 'Big Buck Bunny',
            'upload_date': '20201120'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # '_' query parameter is technically unnecessary, but the web app uses it, so we also use it here
        # int(round()) instead of round() is necessary for python<3.6
        time_ms = int(round(time.time() * 1000))
        meta = self._download_json('https://oc-presentation.ltcc.tuwien.ac.at/search/episode.json', video_id, query={'id': video_id, '_': time_ms})

        result = try_get(meta, lambda x: x['search-results']['result'], dict) or {}
        media_package = result.get('mediapackage') or {}
        track = try_get(media_package, lambda x: x['media']['track'])

        # meta['search-results]['result']['mediapackage']['media'] is a dict if only one track is present, otherwise it is a list of dicts
        if isinstance(track, list):
            tracks = track
        else:
            tracks = [track]

        formats = []
        for track in tracks:
            format = {
                'abr': try_get(track, lambda x: x['audio']['bitrate'] // 1000, int),
                'asr': try_get(track, lambda x: x['audio']['samplingrate'], int),
                'ext': mimetype2ext(track.get('mimetype')),
                'filesize': track.get('size'),
                'fps': try_get(track, lambda x: x['video']['framerate'], int),
                'resolution': try_get(track, lambda x: x['video']['resolution'], compat_str),
                'url': track.get('url'),
                'vbr': try_get(track, lambda x: x['video']['bitrate'] // 1000, int)
            }
            # f4m, m3u8, mpd, ism, rtmp aren't supported by LectureTube, although they are in meta dict
            if format['ext'] not in ['f4m', 'm3u8', 'mpd', 'ism'] and 'rtmp' not in format['url']:
                formats.append(format)

        self._sort_formats(formats)

        return {
            'creator': result.get('dcCreator') or try_get(media_package, lambda x: x['creators']['creator'], compat_str),
            'duration': media_package.get('duration'),
            'formats': formats,
            'id': video_id,
            'series': media_package.get('seriestitle'),
            'timestamp': unified_timestamp(result.get('dcCreated')),
            'title': result.get('dcTitle') or media_package.get('title')
        }
