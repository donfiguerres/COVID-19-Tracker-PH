---
layout: tracker
title: "COVID-19 Tracker Home"
description: "Tracker home page"
---

This serves as a supplementary tracker for the
[COVID-19 Tracker](https://www.doh.gov.ph/covid19tracker) maintained by the
[Department of Health](https://www.doh.gov.ph/). The data set used in this
tracker are pulled from DOH's
[data drop](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o).

GitHub Project: [COVID-19-Tracker-PH](https://github.com/donfiguerres/COVID-19-Tracker-PH)

## Summary
Note:
* Case Doubling Time and Reproduction Number are measured at 14 days before
the last daily report.
* Rt is computed using the simple model and thus may not be the same with 
the official computation of DOH.

<div class="{% if site.scrollappear_enabled %}scrollappear{% endif %}">
{% include tracker/charts/summary.html %}
</div>
