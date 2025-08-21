import requests
import re
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse as date_parse

# Source M3U URL
source_url = "https://raw.githubusercontent.com/abusaeeidx/IPTV-Scraper-Zilla/refs/heads/main/daddylive-schedule.m3u"

# Fetch the latest content
response = requests.get(source_url)
if response.status_code != 200:
    print("Error fetching source M3U. Status code:", response.status_code)
    exit(1)

lines = response.text.splitlines()

# Prepare output
output_lines = ["#EXTM3U"]
seen_titles = set()

i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith("#EXTINF:"):
        # Check for Soccer group
        if 'group-title="Soccer"' in line:
            # Extract title after the comma
            if "," in line:
                parts = line.split(",", 1)
                extinf_prefix = parts[0]
                title = parts[1].strip()
            else:
                extinf_prefix = line
                title = ""

            # Skip if duplicate title
            if title in seen_titles:
                i += 1  # Skip URL line too
                if i < len(lines) and not lines[i].startswith("#"):
                    i += 1
                continue
            seen_titles.add(title)

            # Parse and convert GMT time if found
            time_match = re.search(r"(\d{1,2}:\d{2}) GMT", title)
            if time_match:
                gmt_time_str = time_match.group(1)
                try:
                    # Parse as GMT/UTC
                    gmt_time = date_parse(gmt_time_str).replace(tzinfo=tz.UTC)
                    # Convert to local timezone (use UTC as fallback for GitHub Actions)
                    local_tz = tz.UTC  # GitHub Actions runs in UTC
                    local_time = gmt_time.astimezone(local_tz)
                    local_time_str = local_time.strftime("%H:%M")
                    # Replace in title
                    title = re.sub(r"\d{1,2}:\d{2} GMT", f"{local_time_str} UTC", title)
                except ValueError:
                    pass  # Skip if parsing fails

            # Rebuild EXTINF line
            new_extinf = f"{extinf_prefix},{title}"
            output_lines.append(new_extinf)

            # Add the next line (URL)
            i += 1
            if i < len(lines) and not lines[i].startswith("#"):
                output_lines.append(lines[i])
            continue

    i += 1

# Write to file
with open("soccer_schedule.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print("Generated soccer_schedule.m3u with Soccer matches (unique titles, times in UTC).")
