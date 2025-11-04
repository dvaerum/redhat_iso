## services\.redhat-iso-downloader\.enable



Whether to enable Red Hat ISO downloader service\.



*Type:*
boolean



*Default:*
` false `



*Example:*
` true `

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)



## services\.redhat-iso-downloader\.downloads

List of ISOs to download\.

Each download can specify:

 - Only checksum: Downloads by SHA-256 checksum (immutable)
 - Only filename: Downloads by filename (may change over time)
 - Both: Downloads by checksum and verifies filename matches

The checksum-based approach is recommended for reproducibility\.



*Type:*
list of (submodule)



*Default:*
` [ ] `



*Example:*

```
[
  # Download by checksum (recommended - immutable)
  {
    checksum = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
  }

  # Download by filename (may change over time)
  {
    filename = "rhel-9.6-x86_64-boot.iso";
  }

  # Download by checksum and verify filename matches
  {
    checksum = "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb";
    filename = "rhel-9.6-x86_64-dvd.iso";
  }
]

```

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)



## services\.redhat-iso-downloader\.downloads\.\*\.checksum



SHA-256 checksum of the ISO to download\.

Download by checksum is the recommended approach as checksums
are immutable identifiers\.

At least one of ‘checksum’ or ‘filename’ must be provided\.



*Type:*
null or string



*Default:*
` null `



*Example:*
` "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63" `

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)



## services\.redhat-iso-downloader\.downloads\.\*\.filename



Filename of the ISO to download\.

WARNING: Downloading by filename may result in different checksums
over time if Red Hat updates the file\. For immutable downloads,
use checksum instead\.

At least one of ‘checksum’ or ‘filename’ must be provided\.



*Type:*
null or string



*Default:*
` null `



*Example:*
` "rhel-9.6-x86_64-boot.iso" `

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)



## services\.redhat-iso-downloader\.outputDir



Directory where ISO files will be downloaded\.

The directory will be created if it doesn’t exist\.



*Type:*
absolute path



*Default:*
` "/var/lib/redhat-isos" `



*Example:*
` "/srv/isos/redhat" `

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)



## services\.redhat-iso-downloader\.runOnBoot



Whether to run the download service on system boot\.

If false, you can manually trigger downloads with:
systemctl start redhat-iso-downloader\.service



*Type:*
boolean



*Default:*
` true `

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)



## services\.redhat-iso-downloader\.tokenFile



Path to the Red Hat API offline token file\.

Generate your token at: https://access\.redhat\.com/management/api

For security, consider using agenix or sops-nix to manage this secret\.



*Type:*
absolute path



*Default:*
` "/etc/redhat-api-token.txt" `



*Example:*
` "/run/secrets/redhat-api-token" `

*Declared by:*
 - [/home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader\.nix](file:///home/runner/work/redhat_iso/redhat_iso/modules/redhat-iso-downloader.nix)


