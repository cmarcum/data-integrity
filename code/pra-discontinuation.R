###
# Analysis of PRA discontinuations
# Last Modified: 1/23/2026
###

setwd("~/Consulting/Contracts/New Venture Fund/DataIntegrity/cleaned/wip")
prad<-read.csv("../data/pra_discontinuation_aggregated.csv",stringsAsFactors=FALSE)

#Remove invalid years of request
# prad<-prad[-which(prad$Request.Year<2016),]
prad<-prad[which(prad$Web_Request.Type=="Discontinue"),]

#Barplot of discontinuations by year
barplot(table(prad$AdminYear),las=2,col=c("cornflowerblue",rep("red",4),rep("darkgreen",4),"red"),
        main="Number of Discontinued Information Collections \n by 'Administration' Year of Request to OIRA \n 1/21/2016-1/15/2026",ylim=c(0,800))
legend("topright",legend=c("Obama","Trump","Biden"),fill=c("cornflowerblue","red","darkgreen"),bty="n")

