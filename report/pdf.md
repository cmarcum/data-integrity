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

{% assign cp = site.pages | where: "name", "copyright.md" | first %}
{% if cp %}
<section class="pdf-copyright">
  <h1>{{ cp.title | default: "Copyright Information" }}</h1>
  {{ cp.content | markdownify }}
</section>
{% endif %}

<section class="pdf-toc">
  <h1>Table of Contents</h1>
  {% assign chapters_sorted = site.chapters | where_exp: "c", "c.nav_exclude != true" | sort: "nav_order" %}
  {% assign top_level_toc = chapters_sorted | where_exp: "c", "c.parent == nil and c.grand_parent == nil" %}
  <ul>
    {% for top in top_level_toc %}
    <li>
      <a href="#pdf-{{ top.slug | default: top.title | slugify }}">{{ top.title }}</a>
      {% assign children = chapters_sorted | where: "parent", top.title %}
      {% if children.size > 0 %}
      <ul>
        {% for child in children %}
        <li>
          <a href="#pdf-{{ child.slug | default: child.title | slugify }}">{{ child.title }}</a>
          {% assign grands = chapters_sorted | where: "parent", child.title %}
          {% if grands.size > 0 %}
          <ul>
            {% for g in grands %}
            <li><a href="#pdf-{{ g.slug | default: g.title | slugify }}">{{ g.title }}</a></li>
            {% endfor %}
          </ul>
          {% endif %}
        </li>
        {% endfor %}
      </ul>
      {% endif %}
    </li>
    {% endfor %}
  </ul>
</section>

<section class="pdf-body">
  {% for top in top_level_toc %}
  <article id="pdf-{{ top.slug | default: top.title | slugify }}" class="pdf-chapter">
    <h1>{{ top.title }}</h1>
    {{ top.content }}
    <div class="report-disclaimer"><p><em>{{ site.disclaimer }}</em></p></div>
  </article>

  {% assign children = chapters_sorted | where: "parent", top.title %}
  {% for child in children %}
  <article id="pdf-{{ child.slug | default: child.title | slugify }}" class="pdf-chapter pdf-subchapter">
    <h2>{{ child.title }}</h2>
    {{ child.content }}
    <div class="report-disclaimer"><p><em>{{ site.disclaimer }}</em></p></div>
  </article>

  {% assign grands = chapters_sorted | where: "parent", child.title %}
  {% for g in grands %}
  <article id="pdf-{{ g.slug | default: g.title | slugify }}" class="pdf-chapter pdf-subchapter">
    <h3>{{ g.title }}</h3>
    {{ g.content }}
    <div class="report-disclaimer"><p><em>{{ site.disclaimer }}</em></p></div>
  </article>
  {% endfor %}
  
  {% endfor %}
  {% endfor %}
</section>

<section class="pdf-cover-back"></section>