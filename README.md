# Census Folium Tutorial

![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/interactive_map_demonstration.gif?raw=true)

[Click here](https://kburchfiel3.wordpress.com/2022/01/13/census-folium-tutorial/) to read my blog post about this program. 

This project demonstrates how to use Folium to generate interactive zip-, county-, and state-level choropleth maps. As part of this project, I wrote a function for creating a vertical legend as an alternative to the default horizontal one, as I find vertical legends to be easier to read in certain circumstances. (See the images below for examples of this custom legend.)

Note: some files were too large to be included within the GitHub repository. You can find those additional files at https://drive.google.com/drive/folders/11h1jnaVOA5A6ubbOJnC-kPEvdnJU00yv?usp=sharing.


## Screenshots

Here are example screenshots of the choropleth maps currently stored in this repository. (The original maps are .html files, so for the best viewing experience, I recommend downloading them to your computer and then opening them in a web browser. These screenshots don't display the interactive popup data stored in the .html maps.)

[Click here](https://github.com/kburchfiel/census_folium_tutorial/tree/master/census_folium_map_screenshots) to access all choropleth map screenshots in the repository.

### Population growth data:

#### Population growth from the American Community Survey's 2016 5-year averages to its 2021 5-year averages:

**Zip-level growth:**

![](https://raw.githubusercontent.com/kburchfiel/census_folium_tutorial/master/census_folium_map_screenshots/acs5_2016_2021_zip_pop_growth.png?raw=true)

**County-level growth:**

![](https://raw.githubusercontent.com/kburchfiel/census_folium_tutorial/master/census_folium_map_screenshots/acs5_2016_2021_county_pop_growth.png?raw=true)

**State-level growth:**

![](https://raw.githubusercontent.com/kburchfiel/census_folium_tutorial/master/census_folium_map_screenshots/acs5_2016_2021_state_pop_growth.png?raw=true)

#### County-level population growth from 2010 to 2020 (according to the decennial census):

![](https://raw.githubusercontent.com/kburchfiel/census_folium_tutorial/master/census_folium_map_screenshots/census_2010_2020_county_pop_growth.png?raw=true)


### Demographic data:

These maps contain data from the ACS 2021 community survey (5-year averages). Also note that these maps only show counties and zip codes with at least 1,000 households.

**The proportion of households in each zip code that consist of a married couple with at least one child:**

![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/census_folium_map_screenshots/zip_married_couples_with_kids_acs5_2021.png?raw=true)


**Median household income by zip code:**

![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/census_folium_map_screenshots/zip_median_hh_income_acs5_2021.png?raw=true)


**The proportion of households in each county that consist of a married couple with at least one child:**

![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/census_folium_map_screenshots/county_married_couples_with_kids_acs5_2021.png?raw=true)


**Median household income by county:**

![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/census_folium_map_screenshots/county_median_hh_income_acs5_2021.png?raw=true)



**The proportion of households in each state that consist of a married couple with at least one child:**

![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/census_folium_map_screenshots/state_married_couples_with_kids_acs5_2021.png?raw=true)



**Median household income by state:**
![](https://github.com/kburchfiel/census_folium_tutorial/blob/master/census_folium_map_screenshots/state_median_hh_income_acs5_2021.png?raw=true)



