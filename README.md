# YoutubeCommentCrawler

Client to retrieve comments from YouTube videos using YouTube Data API v3

To use this program, please substitute developer key in the crawler.py with your API key

## Program Usage

### Preliminary
-	This program runs on python3
-	Additionally, requires library (google-api-python-client) to be installed

### Process
1.	Run: python3 crawler.py
2.	Give input of video id or the filename contains the video id line by line

### Result
-	Comments and replies of given video id(s) are saved in the dataset directory (this directory will be automatically created under the current working directory) as tab-separated files 
