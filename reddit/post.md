**Title:** [OC] UK UFO reports follow people, not dark skies or air bases; Loch Ness sightings jumped from about 1 a year to 136 in 1934, when the press made Nessie famous; and only 20 of 44 police forces could list their big cat reports

**Body:**

I treated three British "mystery" report series as data and wrote the tests down before looking at the answers.

- **UFOs.** I used 1,905 UK reports to the US National UFO Reporting Center, counted by council. Reports scale with population almost exactly in step (elasticity 1.08). Darker skies, nearby military airfields, nearby airports and sunshine make no difference. Half of the reports are within 36 km of a military airfield, and so are half of random points spread like the population (37 km). 500 sets of fake air bases did as well as the real ones.
- **Nessie.** I recovered 1,145 sightings from the Official Loch Ness Monster Sightings Register, partly by reading scanned book pages by machine. 1930 to 1932 had 4 sightings, 1933 (the first "monster" headlines) had 93 and 1934 (the hoaxed surgeon's photo) had 136. Operation Deepscan in 1987 and the 2023 Quest brought no rise. Per day, August has 4x as many sightings as January.
- **Big cats.** In a 2019 FOI request to UK police forces, 12 forces refused on cost: word searches turn up hundreds or thousands of incidents, including Puma trainers, Ford Pumas and leopard print, and one force said it would have to read 65,295 calls. 4 said they keep no record.

Interactive map (UFO dots, police replies, a Loch Ness timeline): https://maps.tristanhotham.com/ufos-cats-nessie/

**Source comment:**

Data: NUFORC reports as scrubbed and geocoded by planetsig/ufo-reports (dates and places only, no text); the Official Loch Ness Monster Sightings Register, including H. Bauer's list from The Enigma of Loch Ness (1986); WhatDoTheyKnow batch request 666 "Big cat sightings" (2019); WorldPop 2023; Met Office HadUK-Grid; OurAirports. Method: negative binomial models by council with errors clustered by region, placebo pseudo-bases, OCR (Tesseract) for the scanned list, and Poisson rate ratios for the Nessie years. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/ufos-cats-nessie
