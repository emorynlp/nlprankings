# NLP Rankings

The [NLP Rankings](http://nlprankings.org) site provides research rankings for faculty and academic universities, focusing on the field of Natural Language Processing (NLP).
Inspired by [CSRankings](http://csrankings.org/) which gives university rankings in diverse areas, this site conducts a more thorough survey in NLP.
The academic research achievement is represented by publications archived on the [ACL Anthology](https://www.aclweb.org/anthology/), an open source website hosted by the Association for Computational Linguistics.

These rankings are dedicated to provide insight on research environments in different universities, and allow prospective students to acquire useful information about relevant faculty.
Users can weight conferences and workshop as desired, and view the corresponding rankings for faculty and universities in NLP by the customized weights.
Currently, the site gives rankings for only universities in the United States, but it will be soon expanded to universities in other countries as well.

* Contact: [Jinho D. Choi](http://www.mathcs.emory.edu/~choi).
* Developers: [Chole Lee](https://github.com/chloelee1230) (Fall'19 ~ Spring'20).


## References

* [Ranking U.S. Universities in NLP — Part 1: Data Collection](https://medium.com/@chloelee_62702/ranking-u-s-universities-in-nlp-part-1-data-collection-e30bcbe4c9a5)


## How to Contribute

If you find any discrepancy between your publications and what are presented on [nlpankings.org](http://www.nlprankings.org), you can request for updates through the following procedures:

### Updating Email Addresses

* The university ranking is determined by the domains of email addresses listed on top of every publication. 
If your email address is either incorrectly matched or excluded in the publication, you can make pull requests by updating the corresponding publication JSON files under the directory [`dat/acl_anthology/json/`](dat/acl_anthology/json/). 
* If you do not wish to have your email address included, leave an empty string `""` instead, in which case, your contribution to the paper will not be counted towards any university.
* Only requests on email address modifications will be accepted. Please refrain from modifying any other content. 

### Updating University Information

* The JSON file `dat/university_*.json` contains the name, the email domains, and the location of each university grouped by country (`us`: United States).
* If your university is listed not on [nlpankings.org](http://www.nlprankings.org/), please update `university_*.json` accordingly.
* If there is more than one email domain for the university, please add the addtional domains to the list. Please do not add subdomains such as `cs.emory.edu`. 

### Adding Universities Outside of U.S.

* If we wish to contribute to add universities in other countries, please create the JSON file `dat/university_CC.json` where `CC` is the [country code top-level domain](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains#Country_code_top-level_domains) in lowercase (e.g., for universities in South Korea, please create `dat/university_kr.json`).
