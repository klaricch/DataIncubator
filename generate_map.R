library(rgdal)
library(rgeos)
library(leaflet)
library(dplyr)
library(htmlwidgets)
setwd("~/Desktop/Data_Incubator")
#download grocery stores file
#url<-"http://data.cityofchicago.org/api/views/53t8-wyrc/rows.csv?accessType=DOWNLOAD"
#download_dir<-getwd()
#dest_name<-"grocery_stores.csv"
#download.file(url, dest_name)

gf<-read.csv("chicago_green_roof.txt")
gs<-read.csv("grocery_stores.csv")

#filter for grocery stores > 10,000 sq feet (used in definition of food desert)
large_store<-filter(gs,SQUARE.FEET>10000)

#download zipcodes:
url <- "http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_us_zcta510_500k.zip"
download_dir<-getwd()
dest_name<-"all_zip.zip"
download.file(url, dest_name)
unzip(dest_name, exdir=download_dir, junkpaths=TRUE)
filename<-list.files(download_dir, pattern=".shp", full.names=FALSE)
filename<-gsub(".shp", "", filename)
zip_codes<-readOGR(download_dir, "cb_2014_us_zcta510_500k")

chi_zips<-c(60647,60639,60707,60622,60651,60611,60638,60652,60626,60621,60645,60631,60646,60628,60660,60640,60625,60641,60657,60615,60636,60649,60617,60643,60633,60643,60612,60604,60656,60624,60655,60644,60603,60605,60653,60609,60666,60618,60616,60602,60601,60608,60607,60661,60606,60614,60827,60630,60642,60659,60707,60634,60613,60610,60654,60632,60623,60629,60620,60637,60619)
chicago <- zip_codes[zip_codes$ZCTA5CE10  %in% chi_zips,]
interest<-subset(chicago, grepl('^(60636)|(60628)|(60644).*', chicago$ZCTA5CE10,perl=T)) 

#epsg:4326 transform
chicago<-spTransform(chicago, CRS("+init=epsg:4326"))
interest<-spTransform(interest, CRS("+init=epsg:4326"))
chicago_data<-chicago@data[,c("GEOID10", "ALAND10")]
interest_data<-interest@data[,c("GEOID10", "ALAND10")]
#gSimplify
chicago<-gSimplify(chicago,tol=0.01, topologyPreserve=TRUE)
interest<-gSimplify(interest,tol=0.01, topologyPreserve=TRUE)
#create SpatialPolygonsDataFrame
chicago<-SpatialPolygonsDataFrame(chicago, data=chicago_data)
interest<-SpatialPolygonsDataFrame(interest, data=interest_data)

#leaflet map
m <- leaflet(gf) %>%
  addTiles() %>% 
  setView(lng =-87.7738, lat =41.78798, zoom = 10) %>% 

  addPolygons(data=chicago,weight=2,fillOpacity = 0.15,color="blue")%>%
  addPolygons(data=interest,weight=2,fillOpacity = 0.6,color="turquoise")%>%
addCircles(~LONGITUDE, ~LATITUDE, weight =4, radius=20, 
           color="darkgreen", stroke = TRUE, fillOpacity = 0.8) %>% 
  addCircles(large_store$LONGITUDE, large_store$LATITUDE, weight = 4, radius=20, 
             color="purple", stroke = TRUE, fillOpacity = 0.8)
m

#save map
saveWidget(m, file="chicago_map.html")
