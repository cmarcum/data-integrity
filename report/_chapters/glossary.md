---
layout: glossary
title: Glossary
nav_order: 1000
---

{% comment %}
  1. Get all mds from the 'terms' collection and sort them alpha-numerically by the 'term' variable.
{% endcomment %}
{% assign sorted_terms = site.terms | sort: "term" %}

{% comment %}
  2. Group the sorted terms by the first letter of their 'term' variable.
     This creates groups like {"name": "A", "items": [...]}, {"name": "B", "items": [...]}, etc.
{% endcomment %}
{% assign grouped_terms = sorted_terms | group_by_exp: "item", "item.term | slice: 0, 1 | upcase" %}

<div class="container" id="top">
  <header>
    {{ "The glossary provides select list of terms and definitions used in this project. When feasible, term definitions were drawn from U.S. Federal Government sources as federal definitions can sometimes deviate from concensus-based definitions in standard sources. Additional general resources for terms related to this project include the [Open Data Handbook Glossary](https://opendatahandbook.org/glossary/en/) and the [Turing Way Glossary](https://book.the-turing-way.org/afterword/glossary/). The code for this glossary was adapted from [jekyll-glossary](https://github.com/cmarcum/jekyll-glossary) by the author." | markdownify }}
  </header>

  <nav class="alpha-nav">
    {% for group in grouped_terms %}
      <a href="#{{ group.name }}">{{ group.name }}</a>
    {% endfor %}
  </nav>

  <main>
    {% for group in grouped_terms %}
    <section id="{{ group.name }}" class="glossary-section">
      <h2>{{ group.name }}</h2>
      <dl>
        {% for item in group.items %}
          <dt id="{{ item.slug | default: item.term | slugify }}">{{ item.term }}</dt>
          <dd>{{ item.definition | markdownify }}</dd>
        {% endfor %}
      </dl>
    </section>
    {% unless forloop.last %}<hr>{% endunless %}
    {% endfor %}
  </main>

  <footer>
    <a href="#top" class="back-to-top">↑ Back to Top</a>
  </footer>
</div>

