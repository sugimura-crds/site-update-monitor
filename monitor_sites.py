from datetime import datetime, timezone
from pathlib import Path

FEED_PATH = Path("docs/feed.xml")

now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
<title>Site Update Monitor</title>
<link>https://github.com/</link>
<description>Test Auto Update</description>
<lastBuildDate>{now}</lastBuildDate>

<item>
<title>Auto Test Update</title>
<link>https://example.com</link>
<guid>{now}</guid>
<pubDate>{now}</pubDate>
<description>GitHub Actions test</description>
</item>

</channel>
</rss>
"""

FEED_PATH.write_text(feed, encoding="utf-8")

print("feed.xml updated")
