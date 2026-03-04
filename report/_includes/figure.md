{% assign _src = include.src | default: "" %}
{% assign _alt = include.alt | default: "" %}
{% assign _caption = include.caption | default: "" %}
---

![{{ _alt }}]({{ _src }}){: .img-medium .img-center}
{{ _caption }}

---