#!/usr/bin/env python
# this script:
# 1) downloads the green roof and parks database from the Chicago data portal
# 2) generates a boxplot comparing the percent vegetation on academic buildings to that of non-academic buildings
# 3) performs a rank correlation test to determine if the number of community gardens within a zipcode is correlated with the number of green rooftops
# USAGE: python green_roof.py
# NOTE: requires installation of rpy2, geopy, andd ggplot2(R)

import urllib
import re
import csv
from collections import namedtuple, defaultdict
from rpy2 import robjects
from geopy.geocoders import Nominatim
geolocator = Nominatim()

#retrieve data files on Chicago green rooftops and parks
file_url = 'https://data.cityofchicago.org/api/views/q3z3-udcz/rows.csv?accessType=DOWNLOAD'
urllib.urlretrieve(file_url,"chicago_green_roof.txt")
file_url='https://data.cityofchicago.org/api/views/wwy2-k7b3/rows.csv?accessType=DOWNLOAD'
urllib.urlretrieve(file_url,"chicago_parks.txt")


#FOR PLOT 1, boxplot:
academic_buildings={} #key:building ID, value:percent of rooftop that is vegetated
non_academic_buildings={} #key:building ID, value:percent of rooftop that is vegetated
academic_patterns=('school|university|academy|college|u of|univ\.') # patterns to search for in building names

with open("chicago_green_roof.txt", 'r') as IN:
	GREEN=csv.reader(IN)
	headers=next(IN)
	Row=namedtuple('Row',headers)
	for r in GREEN:
		row=Row(*r)
		#calculate percent of the roof that is vegetated
		per_veg=round((float(row.VEGETATED_SQFT)/float(row.TOTAL_ROOF_SQFT))*100,2)
		#check the two building name columns to determine if the buidlding can be classfied as "academic"
		if re.search(academic_patterns,row.BUILDING_NAME1,flags=re.IGNORECASE) or re.search(academic_patterns,row.BUILDING_NAME2,flags=re.IGNORECASE):
			academic_buildings[row.ID]=per_veg
		else:
			non_academic_buildings[row.ID]=per_veg

#write data to output file:
OUT=open("percent_vegetated.txt", 'w')
for key,value in academic_buildings.items():
	OUT.write("{key}\t{value}\tacademic_building\n".format(**locals()))
for key,value in non_academic_buildings.items():
	OUT.write("{key}\t{value}\tnon_academic_building\n".format(**locals()))		
OUT.close()

#generate box plot with R:
robjects.r("""
	library(ggplot2)
	d1<-read.table("percent_vegetated.txt")
	colnames(d1)<-c("ID","percent_vegetated", "building_type") #add column names
	m <- ggplot(d1, aes(x=building_type, y=percent_vegetated)) + 
		geom_boxplot()+
		theme_bw()+
		scale_x_discrete(breaks=c("academic_building","non_academic_building"), #rename tick mark labels
                   labels=c("Academic Buildings", "Non-Academic Buildings"))+
		labs(x = "Building Type", y = "Percent of Rooftop Vegetated")
	ggsave(filename="Percent_Vegetated_by_Building_Type.png",
       dpi=300,
       width=4,
       height=4,
       units="in")
"""
	)

#FOR PLOT 2,rank correlation test:
gardens=defaultdict(int) #key:zip code, value:number of community gardens
with open("chicago_parks.txt", 'r') as IN:
	PARKS=csv.reader(IN)
	#scrub headers,some contain nonvalid identifying characters
	headers = [ re.sub('[^a-zA-Z_]','_',h) for h in next(PARKS)]
	Row=namedtuple('Row',headers)
	for r in PARKS:
		row=Row(*r)
		if int(row.COMMUNITY_GARDEN) !=0: # only count parks with community gardens
			gardens[row.ZIP] += int(row.COMMUNITY_GARDEN)

green_roofs=defaultdict(int) #key:zip code, value:number of buildings with green rooftops
with open("chicago_green_roof.txt", 'r') as IN:
	GREEN=csv.reader(IN)
	headers=next(IN)
	Row=namedtuple('Row',headers)
	for r in GREEN:
		row=Row(*r)
		coordinate=str(row.LATITUDE+","+row.LONGITUDE)
		location = geolocator.reverse(coordinate,timeout=5) #reverse geocode
		location_info=location.raw
		address=location_info[u'address']
		zip_codes= address[u'postcode']
		match=re.search('(\d+)',zip_codes)
		zip_code=match.group(1) #take first zip code
		green_roofs[zip_code]+=1

#write data to output file:
OUT=open("garden_roof_per_zip.txt","w")
all_zip_codes=set(gardens.keys()+green_roofs.keys())
for zip_code in list(all_zip_codes):
	if zip_code in green_roofs.keys():
		green_roof_no=green_roofs[zip_code]
	else:
		green_roof_no=0
	if zip_code in gardens.keys():
		garden_no=gardens[zip_code]
	else:
		garden_no=0
	OUT.write("{zip_code}\t{garden_no}\t{green_roof_no}\n".format(**locals()))
OUT.close()

#generate plot2 scatterplot with R:
robjects.r("""
	library(ggplot2)
	d2<-read.table("garden_roof_per_zip.txt")
	colnames(d2)<-c("zip_code","gardens", "green_roofs") #add column names

	#spearman correlation
	correlation<-cor.test(d2$gardens, d2$green_roofs,method="spearman",exact=FALSE)
	rho=round(correlation$estimate,3)

	r_label <- paste("italic(r)[s] == ", rho)
	m <- ggplot(d2, aes(x=gardens, y=green_roofs))+
  		geom_point(size=1.25)+
  		geom_smooth(method="lm",se=FALSE,col="red")+ 
  		annotate("text", x=.5, y=28,label=r_label,parse=TRUE,size=2.5)+
  		theme_bw()+
  		labs(x = "Number of Community Gardens Per Zip Code", y = "Number of Green Roofs Per Zip Code")
	ggsave(filename="Green_Rooftop_vs_Gardens.png",
       dpi=300,
       width=4,
       height=4,
       units="in")
"""
)


