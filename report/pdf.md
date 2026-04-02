---
title: Report PDF
permalink: /pdf/
layout: pdf
nav_exclude: true
search_exclude: true
---

<section class="pdf-cover">
  <div class="pdf-cover__panel">
    {% if site.description %}
    <h1>{{ site.description }}</h1>
    {% endif %}

    {% if site.subtitle %}
    <p class="pdf-subtitle">{{ site.subtitle }}</p>
    {% endif %}

    {% if site.author %}
    <p class="pdf-author">{{ site.author }}</p>
    {% endif %}

    <p class="pdf-date">{{ site.time | date: "%B %Y" }}</p>
  </div>
</section>

<section class="pdf-frontmatter">
  {% assign cp = site.pages | where: "name", "copyright.md" | first %}
  {% if cp %}
  <section class="pdf-copyright">
  # {{ cp.title | default: "" }}

  {{ cp.content }}
  </section>
  {% endif %}

  <section class="pdf-toc">
  # Table of Contents

  {% assign chapters_sorted = site.chapters | where_exp: "c", "c.nav_exclude != true" %}
  {% assign top_level_toc = chapters_sorted | where_exp: "c", "c.parent == nil and c.grand_parent == nil" | sort: "nav_order" %}
  {% for top in top_level_toc %}
  {% unless top.nav_exclude %}
  {% if top.parent == nil and top.grand_parent == nil %}
    * [{{ top.title }}](#{{ top.title | slugify }})
    {% assign children = chapters_sorted | where: "parent", top.title | sort: "nav_order" %}
    {% if children.size > 0 %}
    {% for child in children %}
    {% unless child.nav_exclude %}
      * [{{ child.title }}](#{{ child.title | slugify }})
      {% assign grands = chapters_sorted | where: "parent", child.title | sort: "nav_order" %}
      {% if grands.size > 0 %}
      {% for g in grands %}
      {% unless g.nav_exclude %}
        * [{{ g.title }}](#{{ g.title | slugify }})
      {% endunless %}
      {% endfor %}
      {% endif %}
    {% endunless %}
    {% endfor %}
    {% endif %}
  {% endif %}
  {% endunless %}
  {% endfor %}
  </section>
</section>

<section class="pdf-body">

<!-- ===================================================== -->
<!-- MAIN REPORT -->
<!-- ===================================================== -->
{% assign chapters_all = site.chapters | where_exp: "c", "c.nav_exclude != true" %}

{% assign top_level = chapters_all | where_exp: "c", "c.parent == nil and c.grand_parent == nil" | sort: "nav_order" %}

{% for top in top_level %}
<section id="{{ top.slug | default: top.title | slugify }}" class="pdf-chapter">
  <h1>{{ top.title }}</h1>
  {{ top.content }}
  <div class="report-disclaimer"><p><em>{{ site.disclaimer }}</em></p></div>
</section>
<div class="page-break"></div>

{% assign children = chapters_all | where: "parent", top.title | sort: "nav_order" %}
{% for child in children %}
<section id="{{ child.slug | default: child.title | slugify }}" class="pdf-chapter pdf-subchapter">
  <h1>{{ child.title }}</h1>
  {{ child.content }}
  <div class="report-disclaimer"><p><em>{{ site.disclaimer }}</em></p></div>
</section>
<div class="page-break"></div>

{% assign grands = chapters_all | where: "parent", child.title | sort: "nav_order" %}
{% for g in grands %}
<section id="{{ g.slug | default: g.title | slugify }}" class="pdf-chapter pdf-subchapter">
  <h1>{{ g.title }}</h1>
  {{ g.content }}
  <div class="report-disclaimer"><p><em>{{ site.disclaimer }}</em></p></div>
</section>
<div class="page-break"></div>
{% endfor %}
{% endfor %}
{% endfor %}

</div>

</section>