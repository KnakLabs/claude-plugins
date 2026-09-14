# Email Marketing

Three skills for the writing half of email marketing: turn raw direction into a complete
brief, score and rewrite copy you already have, and take a recurring newsletter from blank
page to finished draft.

Built by [Knak](https://knak.com/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin). Nothing here is tied to a platform — the output is copy, so it
works whether you build in Marketo, HubSpot, Braze, Eloqua, Klaviyo or by hand.

## Skills

### `email-brief-generator`

Turns raw direction into a complete email brief: audience and goal, three subject line
options, preview text, and body copy section by section. Direction can be a few bullets, a
voice note, a meeting transcript, a blog post URL, or a half-formed idea.

> *"Write me a brief for the webinar invite"* · *"Turn this transcript into a nurture email"*
> · *"Draft an email announcing this blog post"*

### `email-scorer`

Grades an email that already exists and rewrites the parts that score badly. Hand it a brief
document, a copy deck, email HTML, a screenshot of a rendered email, or just a pasted subject
line and body.

> *"Score this email"* · *"How good is this subject line?"* · *"Roast this copy"*

### `newsletter-content-sourcer`

Takes a recurring newsletter from blank page to finished draft. It researches the sources you
tell it to watch, surfaces the topics worth covering, shapes the ones you pick into the format
your past editions use, and optionally sources images for each slot with alt text.

> *"It's newsletter time"* · *"What should go in this month's edition?"* ·
> *"Build the December newsletter"*

It remembers between runs: where your content comes from, what your newsletter looks like, and
which topics past editions already covered, so it stops asking and stops repeating itself.

## The CHEETAH framework

Both brief skills write and score against **CHEETAH** — Captivate, Human, Entertain, Easy,
Transitions, Animate, Harmony — created by Pierce Ujjainwalla, Co-Founder and CEO of Knak.
Seven checks that decide whether an email gets opened, read and clicked, plus one top tip that
matters more than any of them.

The full framework ships inside the plugin, so the skills apply it without an internet lookup.
The guide it comes from is at
[knak.com/resources/guides/cheetah](https://knak.com/resources/guides/cheetah/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin).

## Requirements

None. Every skill here is model work — no Python, no packages, no API keys, no setup step.
Install it and ask.

## Your files

So they stop asking you the same questions, the skills save a few plain markdown files
**into whatever folder you're already working in** — straight into it, not into sub-folders
and not into a folder named after the plugin. Work somewhere else next time and they simply
start fresh there.

| File | Written by | What it holds |
|---|---|---|
| `brand-guidelines.md` | email-brief-generator, email-scorer | Words to use, words never to use, tone |
| `email-brief-config.md` | email-brief-generator | Sender details, usual audiences and goals |
| `newsletter-sources.md` | newsletter-content-sourcer | Where newsletter content comes from |
| `newsletter-template.md` | newsletter-content-sourcer | Your newsletter's format and tone |
| `newsletter-past-editions.md` | newsletter-content-sourcer | What past editions covered |

**None of this is required to start.** Every skill runs with no folder at all and tells you
what it could not save. It asks for one only when it has something worth keeping, and you can
say no.

Two skills share a file only when they run in the same folder. If you want one set of brand
rules everywhere, keep working in the same place.

You can edit any of these by hand — they are plain markdown, written to be read. If you rename
one, the skills work out what it is from its contents rather than its filename.

## Optional connectors

The skills degrade rather than fail when a connector is missing, and say what they could not
reach.

- **Notion, Slack, Gmail, Google Sheets** — content sources for `newsletter-content-sourcer`,
  and places to send a finished draft.
- **A browser** — for reading blog posts and sourcing images from the pages you link to.

## Companion plugin

**Marketing Operations** covers the production work after the copy is written: UTM-tagged
links, image cropping and compression with alt text, branded QR codes, and contact-list
uploads. The two are built to work together — the usual order is brief or newsletter draft
here, then UTMs and images there, then build and send.

## Licence

MIT. See [LICENSE](LICENSE).
