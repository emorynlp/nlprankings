# NLPRankings

[NLP Rankings](http://nlprankings.org) is a site that provides research rankings for faculty and universities in the United States, focusing on the field of Natural Language Processing (NLP). Inspired by [CSRankings](http://csrankings.org/) which gives university rankings in diverse areas, this site conducts a more thorough survey in NLP. The academic research achievement is represented by publications archived on the [ACL Anthology](https://www.aclweb.org/anthology/), an open source website hosted by the Association for Computational Linguistics.

These rankings are dedicated to provide insight on research environments in different universities, and allow prospective students to acquire useful information about relevant faculty. Users can weight conferences and workshop as desired, and view the corresponding rankings for faculty and universities in NLP by the customized weights.


## Contact

* [Jinho D. Choi](http://www.mathcs.emory.edu/~choi).


## How to Contribute
If you recognize any discrepancy between your publications and what is being presented on [NLP Rankings](http://www.nlprankings.org/), you can add or modify through the following steps:

### Updating Email Addresses
The University ranking is determined by the domain of the email addresses listed on top of each publication. If your email address is incorrectly matched, not included in the publication, or not extracted correctly, you can update the details through updating the publication json files under the directory `nlprankings/dat/acl_anthology/json/`. 

If you do not wish to have your email address included, leave an empty string `""` instead. 

Only pull requests on email addresses modification will be accepted. Please refrain from modifying anything else. 

### Updating U.S. University Info
`nlprankings/dat/university_info_us.json` contains the name, email domains, location of universities located in the United States. As much as we tried to include all universities, we might still be missing some. 

If your university affiliation is not on [NLP Rankings](http://www.nlprankings.org/), please modify the file `university_info_us.json` accordingly. 

If there's more than one email domain for the university, please add the addtional domains to the list. Note that *@cs.emory.edu* is the same domain as *@emory.edu*. 

The JSON format for `university_info_us.json` is as followed:
{
  "name": `university name`,
  "domain": `list of university email domains`,
  "city": `city name`,
  "state": `two letter state abbreviation in capital letters`
}


### Adding International University (outside of U.S.) Info
At the moment, universities outside of the United States are not included in [NLP Rankings](http://www.nlprankings.org/). However we will include international education institutions once we have sufficient data. 

If you belong to an university outside of U.S. and would like to have your institution included, please fill in the JSON file `_____________` as followed:
{
  "name": `university name`,
  "domain": `list of university email domains`,
  "city": `city name`,
  "country": `ISO Alpha-2 country codes`
}

## Acknowledgements

NLP Rankings is an Honors project presened by [Emory NLP](http://nlp.cs.emory.edu/), advised by Dr. Jinho Choi and initiated by Chloe Lee from Emory University. The site is currently being maintained by _________________. 

We would like to thank [ACL Anthology](https://www.aclweb.org/anthology/) for providing the data necessary for our platform by hosting NLP publications from various venues. Publications are made available under the **Creative Commons Attribution License**. 

We would also like to acknowledge [Materialize](https://materializecss.com/) for providing the front-end framework used to build [NLP Rankings](http://www.nlprankings.org/), and [CSRankings](http://csrankings.org/) developed by Emery Berger for inspiring us to create NLP Rankings. 






