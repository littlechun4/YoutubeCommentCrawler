# -*- coding: utf8 -*-

import os, os.path as op, sys
from datetime import datetime as dt
from datetime import timedelta as td

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YoutubeCrawler:
    def __init__(self, developer_key=None):
        """
        Build the service object

        :param developer_key: Google API key
        """
        if developer_key is None:
            self.DEVELOPER_KEY = 'AIzaSyApZ_e6k7P4DqjaXP_Q7OGFyTNJ3osAYJA'
        else:
            self.DEVELOPER_KEY = developer_key

        self.service = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=self.DEVELOPER_KEY)

    def get_channel_videos(self, channel_id):
        """
        Retrieve channel's uploaded videos
        :param channel_id: Id of the channel
        :return: List of video id
        """
        results = self.service.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
        playlist_id = results["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        videos = self.get_playlist_items(playlist_id)
        return videos

    def get_playlist_items(self, playlist_id):
        """
        Retrieve videos' ID using the given playlist id
        :param playlist_id: Id of the playlist
        :return: List of video id
        """
        items = []
        params = {'part': 'snippet', 'playlistId': playlist_id, 'maxResults': 50}
        results = self.service.playlistItems().list(**params).execute()
        items += results['items']

        while 'nextPageToken' in results:
            params['pageToken'] = results['nextPageToken']
            results = self.service.playlistItems().list(**params).execute()
            items += results['items']

        videos = [x['snippet']['resourceId']['videoId'] for x in items]
        return videos

    def get_video_comments(self, video_id):
        """

        :param video_id:
        :return:
        """
        comments = []
        result = self.get_video_comment_threads(video_id)
        comments += result['items']

        while 'nextPageToken' in result:
            result = self.get_video_comment_threads(video_id, result['nextPageToken'])
            comments += result['items']

        replies = []
        for comment in comments:
            if comment['snippet']['totalReplyCount'] > 0:
                result = self.get_comment_replies(comment['snippet']['topLevelComment']['id'])
                replies += result

        # ret_dic = {'comments': comments, 'replies': replies}
        return comments, replies

    def get_video_comment_threads(self, video_id, next_token=None):
        """
        Retrieve top level comments from the video of the given page
        :param video_id: Id of the video
        :param next_token: Pagination token
        :return: Top-level comments of the given page (if next_token is None, first page)
        """
        params = {'part': 'snippet', 'videoId': video_id, 'textFormat': 'plainText', 'order': 'time', 'maxResults': 100}
        if next_token is not None:
            params['pageToken'] = next_token

        results = self.service.commentThreads().list(**params).execute()
        return results

    def get_comment_replies(self, parent_id):
        """
        Return replies of the comment
        :param parent_id: Id of the top-level comment
        :return: Replies of the parent comment
        """
        replies = []

        params = {'part': 'snippet', 'parentId': parent_id, 'textFormat': 'plainText', 'maxResults': 100}
        results = self.service.comments().list(**params).execute()
        replies += results['items']

        while 'nextPageToken' in results:
            params['pageToken'] = results['nextPageToken']
            results = self.service.comments().list(**params).execute()
            replies += results['items']

        return replies

    def save_comments(self, filepath, comments, replies):
        """
        Parse and save the given comments and replies
        :param filepath: Path to save the file
        :param comments: List of comments
        :param replies: List of replies
        :return: None
        """
        parsed_comments = self._parse_comments(comments, replies)
        with open(filepath, 'w', encoding='utf8') as fp:
            for cmt in parsed_comments:
                fp.write(cmt + '\n')

    def delete_old_comments(self):
        """
        Delete saved comments after 30 days
        :return None
        """
        today = dt.now()
        for f in os.listdir('dataset'):
            path = op.join('dataset', f)
            stat = os.stat(path)
            last_modify = dt.fromtimestamp(stat.st_mtime)
            
            if today - last_modify > td(days=30):
                os.remove(path)

    @staticmethod
    def _parse_comments(comments, replies):
        """
        Extract information from comments and replies and make it as tab-separated strings
        :param comments: List of comments
        :param replies: List of replies
        :return: Parsed comments and replies as
        """
        parsed_cmts = []

        video_id = comments[0]['snippet']['videoId']

        # (video_id, top_level, comment_id, parent_id, commenter name, commenter id, comment text, ratable,
        # rating, like count, published time, updated time)
        # and make tuple as tab-separated string
        for cmt in comments:
            parsed_cmt = []
            parsed_cmt.append(video_id)
            parsed_cmt.append('top_level')
            parsed_cmt.append(cmt['snippet']['topLevelComment']['id'])
            parsed_cmt.append('null')
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['authorChannelId']['value'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['textOriginal'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['canRate'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['viewerRating'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['likeCount'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['publishedAt'])
            parsed_cmt.append(cmt['snippet']['topLevelComment']['snippet']['updatedAt'])
            parsed_cmt.append(cmt['snippet']['totalReplyCount'])

            parsed_cmts.append('\t'.join(list(map(str, parsed_cmt))))

        for cmt in replies:
            parsed_cmt = []
            parsed_cmt.append(video_id)
            parsed_cmt.append('top_level')
            parsed_cmt.append(cmt['id'])
            parsed_cmt.append(cmt['snippet']['parentId'])
            parsed_cmt.append(cmt['snippet']['authorDisplayName'])
            parsed_cmt.append(cmt['snippet']['authorChannelId']['value'])
            parsed_cmt.append(cmt['snippet']['textOriginal'])
            parsed_cmt.append(cmt['snippet']['canRate'])
            parsed_cmt.append(cmt['snippet']['viewerRating'])
            parsed_cmt.append(cmt['snippet']['likeCount'])
            parsed_cmt.append(cmt['snippet']['publishedAt'])
            parsed_cmt.append(cmt['snippet']['updatedAt'])
            parsed_cmt.append(0)

            parsed_cmts.append('\t'.join(list(map(str, parsed_cmt))))

        return parsed_cmts


if __name__ == '__main__':
    if not op.exists(op.join('dataset')):
        os.makedirs(op.join('dataset'))

    crawler = YoutubeCrawler()
    crawler.delete_old_comments()

    input_str = input('Video id or the file of video ids: ')

    if 'txt' in input_str:
        with open(input_str, 'r') as fp:
            video_id_lst = fp.read().splitlines()

        for video_id in video_id_lst:
            try:
                if op.exists(op.join('dataset', video_id + '.tsv')):
                    continue

                comments, replies = crawler.get_video_comments(video_id)
                crawler.save_comments(op.join('dataset', video_id + '.tsv'), comments, replies)
                print('Finished video: ', video_id)

            except HttpError as e:
                print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    else:
        video_id = input_str
        try:
            if op.exists(op.join('dataset', video_id + '.tsv')):
                sys.exit()

            comments, replies = crawler.get_video_comments(video_id)
            crawler.save_comments(op.join('dataset', video_id + '.tsv'), comments, replies)
            print('Finished video: ', video_id)

        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
