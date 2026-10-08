# Knak Claude Plugins

Two Claude plugins for marketing teams, from [Knak](https://knak.com/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin).

| Plugin | What it does |
|---|---|
| **[Email Marketing](plugins/email-marketing)** | Writing the email — briefs from rough direction, copy scored against the CHEETAH framework, and newsletters built from your own sources |
| **[Marketing Operations](plugins/marketing-operations)** | The production work around a campaign — UTM links, image cropping and compression with alt text, branded QR codes, and contact-list cleaning |

They work well together and install separately. Each plugin's own README covers what it
does in detail.

## Install

In Claude desktop, open **Plugins → Discover** and search for **Knak**.

To install from this repo directly instead:

```
/plugin marketplace add KnakLabs/claude-plugins
/plugin install email-marketing@knak-plugins
/plugin install marketing-operations@knak-plugins
```

## Requirements

**Email Marketing** needs nothing — every skill is model work.

**Marketing Operations** runs Python for part of each job. The skills install what they need
themselves, the first time they run, so there is nothing to set up. If you use Claude Code,
`/setup-for-claude-code` makes that install permanent on your machine.

## Contributing

These repos are a public showcase maintained by Knak, so we don't accept external pull
requests — see [CONTRIBUTING.md](CONTRIBUTING.md). The code is MIT licensed; clone or fork it freely.

## Licence

MIT. See [LICENSE](LICENSE).

The `image-cropper` skill bundles the MIT-licensed YuNet face detection model from
OpenCV Zoo — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Tested on macOS

These skills were built and tested on macOS. The Python packages they rely on ship Windows
and Linux builds, and the skills resolve `python3` or `python` to whichever the machine has,
so they should work elsewhere — but nothing here has been run on Windows or Linux, and the
shell commands throughout assume a POSIX shell (Git Bash or WSL on Windows).

One known limit: **Clay's CLI has no Windows build**, so `list-upload` falls back to the Clay
connector there, which is slower on long lists.
