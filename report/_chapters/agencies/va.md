---
title: U.S. Department of Veterans Affairs
parent: Agency Profiles
nav_order: 40
---

Some agencies were overzealous in their compliance with [Executive Order 14168](https://www.federalregister.gov/documents/2025/01/30/2025-02090/defending-women-from-gender-ideology-extremism-and-restoring-biological-truth-to-the-federal) by replacing the terms "gender" with "sex" in the titles, descriptions, and field labels of their datasets, and may have also considered several dataset titles to be inconsistent with [Executive Order 14151](https://www.federalregister.gov/documents/2025/01/29/2025-01953/ending-radical-and-wasteful-government-dei-programs-and-preferencing). For instance, the U.S. Department of Veterans Affairs made substantial changes to its comprehensive data inventory (CDI). The metadata for at least fifty-one datasets was altered between February 15th, 2025 and December 31st, 2026. Most of these alterations involved titles invoking gender, race, or both, and occurred between March 15th, 2025 and April 2nd, 2025. Some metadata changes were entirely innocuous and likely reflected mundane maintenance of the files. All entries with changes to titles between the two time points are listed below. 

- VetPop2020_Gender_2000to2023
- Board of Veterans' Appeals
- Use of VA Benefits and Services: 2021 (Part 2)
- VetPop2020 Urban/Rural by Period of Service FY2023
- Use of VA Benefits and Services: 2021 (Part 1)
- Number of Users by Program, FY2010-2021
- Trend in Use of Any VA Benefit, FY 2010-2021
- VETPOP2014 LIVING VETERANS BY RACE/ETHNICITY, GENDER, 2013-2043
- AIAN Veterans Report (2015)
- FY 2021 Total Number of Veterans, Veteran VA Users, and Veteran VA Healthcare Users by Gender and Age Group
- Veterans Utilization Profile FY18 - Fig. 9 - Use Rate of Genders within Era
- Korean War Veterans by State
- Rates of Use within Age Group by Sex, FY2021
- Rate of Use by Race/Ethnicity, FY2021
- Percentage Era Distribution of Female Users and Non-Users, FY 2021
- VetPop2020 Urban/Rural by Ethnicity FY2021-2023
- Use of VA Benefits and Services: 2021 (Introduction)
- Trend in Percent Health Care Enrolled Users, Enrolled Non-Users & Non-Enrolled among Service-Connected Disabled Veterans, FY2010-2021
- Profile of Veterans: (2017)
- Percentage Age Distribution of Male Users and Non-Users, FY 2021
- Users of VA Benefits by Program, FY2021
- VetPop2020 State Estimates 2000 to 2020
- Use of VA Benefits and Services: 2021 (Appendix)
- Percentage Age Distribution of Female Users and Non-Users, FY 2021
- Trend in Rate of Users by Sex, FY2010-2021
- VetPop2020 National Estimates by Race 2000 to 2020
- Analysis of Differences in Disability Compensation in the Department of Veterans Affairs
- Percentage of Service-Connected Disabled Veterans Who Used VA Health Care, by Race/Ethnicity, FY 2021
- Rural Veterans: FY2021-2023
- Percentage Distribution of Users by Era of Initial Service and Sex, FY 2021
- Rates of Use by Sex within Era of Initial Service, FY 2021
- Number of Users of One or More VA Programs by Sex, FY2010-2021
- Age Distribution of Users by Sex, FY2021
- VetPop2020_GenderRaceEthnicity
- Trend in Percent of Health Care & Disability Compensation Users vs Other Users, FY2010-2021
- VetPop Total Population by Gender
- vetpop_gender
- VetPop2020 Urban/Rural by Race FY2021-2023
- VetPop2020 National Estimates 2000 to 2020
- VetPop2020 Urban/Rural by Poverty & Disability FY2021-2023
- Percent of Veterans who Use VA Benefits by Program and Gender, FY2023
- Percentage of Service-Connected Disabled Who Did and Did Not Use Health Care, by Disability Rating, FY2021
- Percentage Era Distribution of Male Users and Non-Users, FY 2021
- Use of VA Benefits and Services: 2021 (Part 3)
- VetPop2020 Urban/Rural FY2021-2023
- FY 2020 Total Number of Veterans, Veteran VA Users, and Veteran VA Healthcare Users by Gender and Age Group
- FY10 Compensation and Pension by County
- VetPop2020_GenderPeriodOfService
- Take-up Rate by Race/Etnicity and Gender
- Veterans Receiving Compensation Service Benefits On the Rolls by Period of Service and Residence FY22 and FY23
- Percent Change in Veteran Population by State from 2000 to 2022

Critically, many of these changes were not simply modifications to persistent records. Rather, VA apparently removed and replaced many of the updated the entries altogether. For example, the previous CDI entry for the dataset titled, "VetPop2020 estimate of Veterans by gender from 2000 to 2023", had this entry:

```
{
	...
      "identifier": "https://www.data.va.gov/api/views/2rci-xm64",
      "description": "VetPop2020 estimate of Veterans by gender from 2000 to 2023",
      "title": "VetPop2020_Gender_2000to2023",
      "programCode": [
        "029:086"
      ],
      "distribution": [
        {
          "@type": "dcat:Distribution",
          "downloadURL": "https://www.data.va.gov/api/views/2rci-xm64/rows.csv?accessType=DOWNLOAD",
          "mediaType": "text/csv"
        },
	...
```

which appears to have been entirely deleted and replaced with a new entry:

```
	...
      "identifier": "https://www.data.va.gov/api/views/y4w4-egzx",
      "description": "The Department of Veterans Affairs provides official estimates and projections of the Veteran population using the Veteran Population Projection Model (VetPop). Based on the available information through September 30, 2023, the latest model VetPop2023 estimated the Veteran population for the period from 2000 to 2023. The “Number of Estimated Veterans by Sex and 15 Age Groups, 9/30/2000 to 9/30/2023” data table shows the number of living Veterans at the end of each fiscal year from 2000 to 2023.",
      "title": "VetPop2023 National Estimates by Sex and Age Groups 2000 to 2023",
      "programCode": [
        "029:086"
      ],
      "distribution": [
        {
          "@type": "dcat:Distribution",
          "downloadURL": "https://www.data.va.gov/api/views/y4w4-egzx/rows.csv?accessType=DOWNLOAD",
          "mediaType": "text/csv"
        },
	...

```

In part, this is likely due to the how the underlying data management system VA uses, Socrata, automatically generates API endpoints for every dataset uploaded to its platform through its Socrata Open Data API (SODA).

## Manipulation of underlying data files

According to research by Freilich & Kesselheim {% cite freilich2025lancet -A %}, nearly half of the 79 datasets from the VA they examined were manipulated in response to EO 14168 between the Inauguration and March of 2025. Freilich graciously provided the python code used for their report and the acquisition routines and review methods were reproducible (and indeed comparable to those used in this project and complementary to those in [the auditing workflow](/chapters/07-auditing/)). They manually evaluated both metadata and underyling dataset changes by comparing live versions of VA datasets to those archived prior to January 20th, 2025 by the WayBack Machine.  Their results are consistent with those presented above: VA replaced "gender" with "sex" in the title, general description, and column headers of the plurality of the data and metadata they evaluated. None of the changes were documented by VA and there were no disclosures on the public dataset landing pages that this was occurring. Further auditing of several of the datasets Freilich & Kesselheim examined was done by evaluating the checksums of version-pairs after stripping the column headers out of the datasets were the same (via the SHA256 algorithm). In these cases, even though the variable names differed, the underlying data remained unchanged. 

Even so, there is evidence that VA's efforts were not comprehensive. Even up to the date of publication of this report, there are still metadata entries in the CDI that include the word "Gender" in both the title and in the underlying datasets (this likely belies a less-than-systematic approach on their part). For example, as of 3/12/2026, the dataset 
titled "FY 2021_NCVAS Vet Pop Gender Over Time Data For State Summaries" was still included in the CDI and available for download.

```
	...
      "identifier": "https://www.data.va.gov/api/views/gidu-8zyi",
      "description": "These data are based on the latest Veteran Population Projection Model, VetPop2020, provided by the National Center for Veterans Statistics and Analysis, published in 2023.",
      "title": "FY 2021_NCVAS Vet Pop Gender Over Time Data For State Summaries",
      "programCode": [
        "029:000"
      ],
      "distribution": [
        {
          "@type": "dcat:Distribution",
          "downloadURL": "https://www.data.va.gov/api/views/gidu-8zyi/rows.csv?accessType=DOWNLOAD",
          "mediaType": "text/csv"
        },
	...
``` 

## Conclusion

Arbitrarily changing variable and study names is against best practices for data governance. It can also contribute to link rot and code replication problems in the future. However, those violations of data integrity are far less impactful than manipulating the underlying data. Forensic auditing that compared pre- and post-Administration versions of several of these datasets revealed that data manipulation was unlikely. The materials reviewed here support the conclusion that the VA's 2025 public-data integrity issues were primarily metadata and labeling changes on public dataset pages, often without clear documentation, rather than changes to the underlying data.

## References

{% bibliography --cited %}