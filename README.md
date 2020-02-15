# NLPRankings

http://nlprankings.org

## Contact

* [Jinho D. Choi](http://www.mathcs.emory.edu/~choi).


## How to Contribute
If you recognize any discrepancy between your publications and what is being presented on [NLPRankings.org](http://www.nlprankings.org/), you can add or modify through the following steps:

### Updating Email Addresses
The University ranking is determined by the domain of the email addresses listed on top of each publication. If your email address is incorrectly matched, not included in the publication, or not extracted correctly, you can update the details through updating the publication json files under the directory `nlprankings/dat/acl_anthology/json/`. 

If you do not wish to have your email address included, leave an empty string `""` instead. 

Only pull requests on email addresses modification will be accepted. Please refrain from modifying anything else. 

### Updating U.S. University Info
`nlprankings/dat/university_info_us.json` contains the name, email domains, location of universities located in the United States. As much as we tried to include all universities, we might still be missing some. 

If your university affiliation is not on [NLPRankings.org](http://www.nlprankings.org/), please modify the file `university_info_us.json` accordingly. 

If there's more than one email domain for the university, please add the addtional domains to the list. Note that *@cs.emory.edu* is the same domain as *@emory.edu*. 

The JSON format for `university_info_us.json` is as followed:
{
  "name": `university name`,
  "domain": `list of university email domains`,
  "city": `city name`,
  "state": `two letter state abbreviation in capital letters`
}


### Adding International University (outside of U.S.) Info
At the moment, universities outside of the United States are not included in [NLPRankings.org](http://www.nlprankings.org/). However we will include international education institutions once we have sufficient information. 

If you belong to an university outside of U.S. and would like to have your institution included, please fill in the JSON file `x` as followed:
{
  "name": `university name`,
  "domain": `list of university email domains`,
  "city": `city name`,
  "country": `ISO Alpha-2 country codes`
}

