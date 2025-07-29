import feedparser

def get_latest_video_from_rss(rss_url):
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        raise ValueError("No videos found in RSS feed")
    
    latest = feed.entries[0]
    video_id = latest['yt_videoid']
    title = latest['title']
    link = latest['link']
    
    return video_id, title, link

if __name__ == "__main__":
    rss_url = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLZPgleW4baxpCtioKMLwGfWxeUUIuZi49"

    try:
        video_id, title, link = get_latest_video_from_rss(rss_url)
        print(f"Latest Video ID: {video_id}")
        print(f"Title: {title}")
        print(f"Link: {link}")
    except ValueError as e:
        print(e)
