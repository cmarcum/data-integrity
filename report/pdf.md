---
title: Report PDF
permalink: /pdf/
layout: pdf
nav_exclude: true
search_exclude: true
---

<!-- ===================================================== -->
<!-- COVER PAGE -->
<!-- ===================================================== -->
<div class="pdf-cover">
  <div class="pdf-cover__content" >
	{% if site.description %}<p class="pdf-subtitle">{{ site.description }}</p>{% endif %}
	{% if site.subtitle %}<p class="pdf-subtitle">{{ site.subtitle }}</p>{% endif %}
    <div class="pdf-cover__rule"></div>
    {% if site.author %}<p class="pdf-author">{{ site.author }}</p>{% endif %}
    <p class="pdf-date">{{ site.time | date: "%B %Y" }}</p>
  </div>
</div>

<div class="page-break"></div>

<div class="pdf-body">

<!-- ===================================================== -->
<!-- COPYRIGHT PAGE (pulled from copyright.md) -->
<!-- ===================================================== -->
{% assign cp = site.pages | where: "name", "copyright.md" | first %}
{% if cp %}
<section class="pdf-frontmatter" id="copyright">
  <h1>{{ cp.title | default: "" }}</h1>
  {{ cp.content }}
</section>
<div class="page-break"></div>
{% endif %}

<!-- ===================================================== -->
<!-- TABLE OF CONTENTS (nested using parent relationships) -->
<!-- ===================================================== -->
<section class="pdf-toc-page">
<h1> Table of Contents</h1>

{% assign chapters_sorted = site.chapters | where_exp: "c", "c.nav_exclude != true" %}

{% assign top_level_toc = chapters_sorted | where_exp: "c", "c.parent == nil and c.grand_parent == nil" | sort: "nav_order" %}

<ul class="pdf-toc">
  {% for top in top_level_toc %}
    {% unless top.nav_exclude %}
      {% if top.parent == nil and top.grand_parent == nil %}
        <li>
          <a href="#{{ top.slug | default: top.title | slugify }}">{{ top.title }}</a>

          {% assign children = chapters_sorted | where: "parent", top.title | sort: "nav_order" %}
          {% if children.size > 0 %}
            <ul>
              {% for child in children %}
                {% unless child.nav_exclude %}
                  <li>
                    <a href="#{{ child.slug | default: child.title | slugify }}">{{ child.title }}</a>

                    {% assign grands = chapters_sorted | where: "parent", child.title | sort: "nav_order" %}
                    {% if grands.size > 0 %}
                      <ul>
                        {% for g in grands %}
                          {% unless g.nav_exclude %}
                            <li>
                              <a href="#{{ g.slug | default: g.title | slugify }}">{{ g.title }}</a>
                            </li>
                          {% endunless %}
                        {% endfor %}
                      </ul>
                    {% endif %}

                  </li>
                {% endunless %}
              {% endfor %}
            </ul>
          {% endif %}

        </li>
      {% endif %}
    {% endunless %}
  {% endfor %}
</ul>
</section>

<div class="page-break"></div>

<!-- ===================================================== -->
<!-- MAIN REPORT -->
<!-- ===================================================== -->
{% assign chapters_all = site.chapters | where_exp: "c", "c.nav_exclude != true" %}

{%- comment -%}
  1) Top-level = no parent/grand_parent
  2) Render top-level in nav_order order
  3) For each top-level, render its children (parent == top.title) in nav_order order
  4) Optionally render grandchildren (parent == child.title) if you use that depth
{%- endcomment -%}

{% assign top_level = chapters_all | where_exp: "c", "c.parent == nil and c.grand_parent == nil" | sort: "nav_order" %}

{% for top in top_level %}
<section id="{{ top.slug | default: top.title | slugify }}" class="pdf-chapter">
  <h1>{{ top.title }}</h1>
  {{ top.content }}
</section>
<div class="page-break"></div>

{% assign children = chapters_all | where: "parent", top.title | sort: "nav_order" %}
{% for child in children %}
<section id="{{ child.slug | default: child.title | slugify }}" class="pdf-chapter pdf-subchapter">
  <h1>{{ child.title }}</h1>
  {{ child.content }}
</section>
<div class="page-break"></div>

{% assign grands = chapters_all | where: "parent", child.title | sort: "nav_order" %}
{% for g in grands %}
<section id="{{ g.slug | default: g.title | slugify }}" class="pdf-chapter pdf-subchapter">
  <h1>{{ g.title }}</h1>
  {{ g.content }}
</section>
<div class="page-break"></div>
{% endfor %}
{% endfor %}
{% endfor %}

</div>