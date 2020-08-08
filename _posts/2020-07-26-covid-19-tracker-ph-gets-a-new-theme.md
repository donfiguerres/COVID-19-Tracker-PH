---
layout: post 
date: 2020-07-27 00:30
title: "The COVID-19 Tracker Gets a New Theme"
description: "The COVID-19 Tracker is now using the Chalk Theme."
categories: blog
---

I'm happy to announce that the COVID-19 Tracker PH site is now using the 
[Chalk Theme](https://github.com/nielsenramon/chalk).

# Other changes
## gh-pages branch
The live site will now be published from the gh-pages branch since I need to
build the site first locally due to some dependencies not being supported by
Github Pages.

# Smaller sized charts
Charts are now at kilobytes size from around 3.5MB each. By default, plotly's
write_html method would include the their whole js library which is around 3MB.
I changed the include_plotlyjs option to 'cdn'. This will load the publicly
available copy of their library from the internet instead of being included in
each chart.

# Top LGU
Horizontal bar chart for top city/municipality is now available.
