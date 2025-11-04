#!/usr/bin/env python3
"""
Example: Using redhat_iso as a Python library
"""

from redhat_iso import RedHatAPI

# Initialize API with your offline token
# In practice, you'd load this from a file or environment variable
token = open("redhat-api-token.txt").read().strip()
api = RedHatAPI(token)

# Example 1: List RHEL images for a specific version
print("Example 1: List RHEL 9.6 x86_64 images")
print("=" * 50)
images = api.list_rhel_images("9.6", "x86_64")
for img in images[:3]:  # Show first 3
    print(f"  {img['imageName']}")
    print(f"    Filename: {img['filename']}")
    print(f"    Checksum: {img['checksum']}")
    print()

# Example 2: Discover available RHEL versions
print("\nExample 2: Discover available RHEL versions")
print("=" * 50)
versions = api.discover_rhel_versions("x86_64")
print(f"Found {len(versions)} RHEL versions:")
for version, arch in versions[:5]:  # Show first 5
    print(f"  RHEL {version} ({arch})")

# Example 3: Check if a specific version exists
print("\nExample 3: Check if RHEL 11.0 exists")
print("=" * 50)
exists = api.version_exists("11.0", "x86_64")
print(f"RHEL 11.0 exists: {exists}")

# Example 4: Find an image by filename (silent mode)
print("\nExample 4: Find image by filename")
print("=" * 50)
# For library usage, you might want to search quietly
x86_64_versions = api.discover_rhel_versions("x86_64")
aarch64_versions = api.discover_rhel_versions("aarch64")
search_versions = x86_64_versions + aarch64_versions

filename = "rhel-9.6-x86_64-boot.iso"
found = None
for version, arch in search_versions:
    images = api.list_rhel_images(version, arch)
    for img in images:
        if img.get('filename') == filename:
            found = img
            break
    if found:
        break

if found:
    print(f"Found: {found['imageName']}")
    print(f"  Checksum: {found['checksum']}")
else:
    print(f"Not found: {filename}")

# Example 5: Download a file programmatically
# (commented out to avoid actually downloading)
# print("\nExample 5: Download file")
# print("=" * 50)
# api.download_file(
#     identifier="febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
#     output_dir="./downloads",
#     by_filename=False
# )

print("\n" + "=" * 50)
print("Library examples completed!")
