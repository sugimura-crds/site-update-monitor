from datetime import datetime, timezone
from pathlib import Path

FEED_PATH = Path("docs/feed.xml")

now_dt = datetime.now(timezone.utc)
now = now_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
stamp = now_dt.strftime("%Y%m%d%H%M%S")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Site Update Monitor</title>
<link>https://example.com</link>
<description>Simple RSS Feed</description>

<item>
<title>Test {stamp}</title>
<link>https://example.com/{stamp}</link>
<guid>test-{stamp}</guid>
<pubDate>{now}</pubDate>
<description>Test item {stamp}</description>
</item>

</channel>
</rss>
"""

FEED_PATH.write_text(feed, encoding="utf-8")
print("feed.xml updated")
