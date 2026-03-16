---
title: Office of Management and Budget
parent: Agency Case Studies
nav_order: 20
---

On March 24, 2025, the OMB revoked public access to its apportionments database. Apportionments are legally binding documents issued by the OMB that specify the timing and conditions under which federal agencies may use funds appropriated by Congress {% cite fiorentino2025omb %}. Following the impoundment of more than $250M in Congressionally mandated aid to Ukraine by OMB in 2019, Congress established a legal requirement for OMB to make all apportionment documents, including footnotes and written explanations, available on a public website within two business days of their issuance in the The Consolidated Appropriations Act of 2022 {% cite heilweil2025gao %}. This legislation was designed to provide Congress and the public with real-time insight into how the executive branch manages appropriated funds. Previously, OMB had voluntarily made apportionments data publicly accessible. A Protect Democracy initiative provides both historical and, when it is available, contemporaneous data available through [OpenOMB](https://openomb.org/). 

Based on [data from the OpenOMB API](https://www.github.com/cmarcum/data-integrity/tree/main/data/omb-apportionments-takedown.json), OMB prevented access to more than 1700 individual apportionment files for FY 2024 and 2025 between March 24th and August 15th of 2025.  The actions taken by OMB, prompted inquiries from civic-society organizations and the Government Accountability Office (GAO). Public access to apportionments data is the primary transparency tool used for accountability that OMB is appropriately spending funds appropriated by Congress. The GAO subsequently issued a finding that the removal of the website was inconsistent with the law. Loss of public access to the apportionments data represented one of the most significant examples of direct political interference into the integrity of federal data in 2025.

OMB Director Russell Vought defended the decision to restrict access to the database, outlining his reasoning in communications with the House Appropriations Committee and in subsequent court filings. Vought argued that the 2022 transparency requirements interfered with the executive branch's internal operations. He maintained that apportionments often contain pre-decisional and deliberative information that should be protected from immediate public release. According to Vought, making these documents public in real-time could inhibit candid discussions between OMB staff and agency officials regarding budgetary adjustments.

Furthermore, the OMB argued that the President possesses inherent Article II authority to manage the execution of the budget. From this perspective, the mandatory public posting of technical spending footnotes was viewed by the OMB as an encroachment on executive discretion. Vought also noted concerns that some spending data might inadvertently reveal sensitive administrative strategies, asserting that the OMB required a level of confidentiality to execute the President’s policy priorities efficiently without premature public or legislative interference {% cite emma2025appeals katz2025omb %}.

The removal of the data led to lawsuits from several organizations, including Citizens for Responsibility and Ethics in Washington (CREW). The plaintiffs argued that the OMB was in direct violation of the 2022 Act. In July 2025, U.S. District Judge Emmet Sullivan ruled that the OMB was legally required to maintain the database. The court found that because apportionments are legally binding directives under the Antideficiency Act, they constitute final agency actions rather than protected deliberative materials. Consequently, the court issued a permanent injunction requiring the OMB to restore the website {% cite emma2025appeals %}.

Following this ruling, the OMB restored the database in August 2025. However, further disputes arose regarding the completeness of the data. Plaintiffs noted that the OMB was using "A" footnotes to refer to "spend plans" and other documents that remained private. This led to additional litigation regarding whether the statutory requirement for "all footnotes and written explanations" included documents incorporated by reference {% cite crew2025omb katz2026omb %}.

## Timeline of Events

{% capture figpath1 %}{{ site.baseurl }}/assets/images/apportionments_timeline.png{% endcapture %}
{% include figure.md src=figpath1 alt="Apportionments dataset public access removal and restoration timeline, 2025-2026" caption="Figure: Apportionments dataset public access removal and restoration timeline, 2025-2026. The figure was generated with Google Slides AI 'beautify this slide' feature on a plain slide with the bulleted timeline text (below)." %}

* **March 24, 2025:** OMB disables the Public Apportionments Database, citing the need to protect deliberative communications.
* **April 8, 2025:** The GAO confirms that the suspension of the website violates the Consolidated Appropriations Act.
* **April 8, 2025:** Legal challenges by Citizens for Responsibility and Ethics in Washington are filed in the U.S. District Court for the District of Columbia.
* **July 21, 2025:** The District Court rules against OMB and orders the restoration of the database.
* **August 9, 2025:** A federal appeals court declines to stay the lower court's order, requiring the OMB to comply during the appeals process.
* **August 15, 2025:** OMB restores the public website, though some data remains inaccessible through the use of external references known as 'A' footnotes.
* **September 19, 2025:** Plaintiffs file a motion to enforce the injunction, seeking the release of documents referenced in footnotes .
* **January 28, 2026:** The court clarifies that documents incorporated by reference in apportionments must also be made public.

## References

{% bibliography --cited %}