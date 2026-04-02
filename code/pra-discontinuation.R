###
# Analysis of PRA discontinuations
# Last Modified: 2/17/2026
###

prad<-read.csv("../data/pra_discontinuation_aggregated-01282026.csv",stringsAsFactors=FALSE)

#Remove invalid years of request
# prad<-prad[-which(prad$Request.Year<2016),]
prad<-prad[which(prad$Web_Request.Type=="Discontinue"),]

#Barplot of discontinuations by year

# Colors:
# #CC79A7 - reddish
# #56B4E9 - bluish
# #009E73 - greenish

# Colors from Okabe-Ito colorblind-friendly palette:
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000")

# #CC79A7 - reddish
# #56B4E9 - bluish
# #009E73 - greenish

png("../report/assets/images/icr-discontinuations.png",width = 2500, height=2500, res=300)
barplot(table(prad$AdminYear),las=2,col=c("#56B4E9",rep("#CC79A7",4),rep("#009E73",4),"#CC79A7"),
        main="\n Number of Discontinued Information Collections \n by 'Administration' Year of Request to OIRA \n 1/21/2016-1/15/2026",ylim=c(0,800),xlab="Administration Year",ylab="Frequency")
legend("topright",legend=c("Obama","Trump","Biden"),fill=c("#56B4E9","#CC79A7","#009E73"),bty="n")
dev.off()

