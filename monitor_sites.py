from datetime import datetime, timezone
from pathlib import Path
import urllib.parse

FEED_PATH = Path("docs/feed.xml")

now_dt = datetime.now(timezone.utc)
now = now_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
stamp = now_dt.strftime("%Y%m%d%H%M%S")

test_url = f"https://example.com/test-{stamp}"

feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
<title>Site Update Monitor</title>
<link>https://github.com/</link>
<description>Test Auto Update</description>
<lastBuildDate>{now}</lastBuildDate>

<item>
<title>Auto Test Update {stamp}</title>
<link>{test_url}</link>
<guid isPermaLink="false">test-{stamp}</guid>
<pubDate>{now}</pubDate>
<description>GitHub Actions test {stamp}</description>
</item>

</channel>
</rss>
"""

FEED_PATH.write_text(feed, encoding="utf-8")

print("feed.xml updated")
