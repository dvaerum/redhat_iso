# JSON Output Format Documentation

The `redhat_iso` tool supports JSON output for all list operations via the `--json` flag.

## Default List (Currently Supported Releases)

**Command:**
```bash
redhat_iso --json list
```

**Output Structure:**
```json
{
  "releases": [
    {
      "version": "9.6",
      "architecture": "x86_64",
      "images": [...]
    },
    {
      "version": "8.10",
      "architecture": "x86_64",
      "images": [...]
    }
  ]
}
```

## Specific Version and Architecture

**Command:**
```bash
redhat_iso --json list --version 9.6 --arch x86_64
```

**Output Structure:**
```json
{
  "version": "9.6",
  "architecture": "x86_64",
  "images": [
    {
      "imageName": "Red Hat Enterprise Linux 9.6 Binary DVD",
      "filename": "rhel-9.6-x86_64-dvd.iso",
      "arch": "x86_64",
      "checksum": "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
      "datePublished": "2025-04-22T09:34:36.000Z",
      "downloadHref": "https://api.access.redhat.com/management/v1/images/febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb/download"
    }
  ]
}
```

## Content Set

**Command:**
```bash
redhat_iso --json list --content-set rhel-9-for-x86_64-baseos-isos
```

**Output Structure:**
```json
{
  "content_set": "rhel-9-for-x86_64-baseos-isos",
  "images": [
    {
      "filename": "rhel-9.6-x86_64-dvd.iso",
      "arch": "x86_64",
      "checksum": "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
      "datePublished": "2025-04-22T09:34:36.000Z"
    }
  ]
}
```

## Image Object Fields

Each image object contains:

| Field | Type | Description |
|-------|------|-------------|
| `imageName` | string | Human-readable name of the image |
| `filename` | string | ISO filename |
| `arch` | string | Architecture (x86_64, aarch64, etc.) |
| `checksum` | string | SHA-256 checksum for download |
| `datePublished` | string | ISO publication date (ISO 8601) |
| `downloadHref` | string | API endpoint to get download URL |

## Common Use Cases

### Extract All Checksums
```bash
redhat_iso --json list --version 9.6 --arch x86_64 | jq -r '.images[].checksum'
```

### Get Binary DVD Checksum
```bash
redhat_iso --json list --version 9.6 --arch x86_64 | \
  jq -r '.images[] | select(.filename | contains("dvd.iso")) | .checksum'
```

### Filter by Date
```bash
redhat_iso --json list --content-set rhel-9-for-x86_64-baseos-isos | \
  jq '.images[] | select(.datePublished > "2025-01-01")'
```

### Count Available ISOs
```bash
redhat_iso --json list | jq '[.releases[].images | length] | add'
```

### Generate Download Script
```bash
redhat_iso --json list --version 9.6 --arch x86_64 | \
  jq -r '.images[] | "redhat_iso download \(.checksum) --output ~/isos"'
```

## Integration Examples

### Bash Script
```bash
#!/bin/bash
checksums=$(redhat_iso --json list --version 9.6 --arch x86_64 | jq -r '.images[].checksum')
for checksum in $checksums; do
  echo "Downloading: $checksum"
  redhat_iso download "$checksum"
done
```

### Python Script
```python
import subprocess
import json

result = subprocess.run(
    ["redhat_iso", "--json", "list", "--version", "9.6", "--arch", "x86_64"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

for image in data["images"]:
    if "dvd.iso" in image["filename"]:
        print(f"Downloading {image['filename']}...")
        subprocess.run(["redhat_iso", "download", image["checksum"]])
```

### jq Filter Examples
```bash
# Get only Boot ISOs
redhat_iso --json list | jq '.releases[].images[] | select(.filename | contains("boot.iso"))'

# Group by version
redhat_iso --json list | jq '.releases | group_by(.version)'

# Get latest release info
redhat_iso --json list | jq '.releases[0]'
```
