---
title: Print (All Chapters)
permalink: /print/
nav_exclude: true
search_exclude: true
---

# Full Report (Print View)

{% assign chapters_sorted = site.chapters | sort: "nav_order" %}

{% for ch in chapters_sorted %}
<hr />
## {{ ch.title }}

{{ ch.content }}
{% endfor %}
