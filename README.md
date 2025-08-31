# modarchive_dl

Small script I use to download modules from modarchive.org, which scrapes the metadata and save it to a csv file. 
Beware! The code is LLM assisted because I was lazy. It is pretty bad. But! it mostly works.

## Usage

> python3 modarchive_dl.py <MOD-Archive-ID>

This downloads the module and put it in a directory based on genre. also adds an entry to `modules_catalog.csv`
Sidenote: it was hard for me to come up with a reasonable folder structure: the artists info is not always available, there are not really "albums", and also no dates.

Can also override the artist or name with your own values

> python3 modarchive_dl.py <MOD-Archive-ID> --artist Bob --name epic-song
