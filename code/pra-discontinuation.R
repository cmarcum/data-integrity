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
# #e74c3c - reddish
# #3498db - bluish
# #2ecc71 - greenish

png("../report/assets/images/icr-discontinuations.png",width = 2500, height=2500, res=300)
barplot(table(prad$AdminYear),las=2,col=c("#3498db",rep("#e74c3c",4),rep("#2ecc71",4),"#e74c3c"),
        main="\n Number of Discontinued Information Collections \n by 'Administration' Year of Request to OIRA \n 1/21/2016-1/15/2026",ylim=c(0,800),xlab="Administration Year",ylab="Frequency")
legend("topright",legend=c("Obama","Trump","Biden"),fill=c("#3498db","#e74c3c","#2ecc71"),bty="n")
dev.off()

