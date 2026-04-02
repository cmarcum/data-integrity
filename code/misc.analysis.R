####
# This R script runs some analysis supporting project statistics
# Last Modified: 3.3.2026
####

# Colors from Okabe-Ito colorblind-friendly palette:
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000")

# #CC79A7 - reddish
# #56B4E9 - bluish
# #009E73 - greenish

# USAID proportion of public datasets
usaid.datainventory.2025012029 <- read.csv("../data/usaid-datainventory-2025012029.csv")
prop.table(table(usaid.datainventory.2025012029$Proposed.Access.Level))

# Federal workforce changes
library(ggplot2)
library(dplyr)
library(scales)
library(patchwork)
library(readr)
library(tidyr)
library(lubridate)

df <- read_csv("../data/opm-workforce.csv", show_col_types = FALSE)
df <- df %>%
  mutate(
    `Workforce changes count` = as.numeric(gsub(",", "", `Workforce changes count`)),
    `Percentage Cut (%)` = `2025 cuts as % of 2024 Workforce` * 100
  ) %>%
  arrange(`2025 cuts as % of 2024 Workforce`) %>%
  mutate(`Federal Agency` = factor(`Federal Agency`, levels = `Federal Agency`))

# Plot 1: Absolute Workforce Changes (Count)
p1 <- ggplot(df, aes(x = `Workforce changes count`, y = `Federal Agency`)) +
  geom_col(fill = "#CC79A7") +
  geom_text(aes(label = comma(`Workforce changes count`)), 
            hjust = 1.1, size = 4, color = "black") +
  labs(
    title = "Absolute Workforce Changes",
    x = "Number of Employees",
    y = NULL
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, margin = margin(b = 15)),
    axis.text.y = element_text(size = 11),
    axis.title.x = element_text(size = 12)
  ) +
  scale_x_continuous(expand = expansion(mult = c(0.2, 0))) 

# Plot 2: Percentage Cuts
p2 <- ggplot(df, aes(x = `Percentage Cut (%)`, y = `Federal Agency`)) +
  geom_col(fill = "#56B4E9") +
  geom_text(aes(label = sprintf("%.1f%%", `Percentage Cut (%)`)), 
            hjust = -0.1, size = 4, color = "black") +
  labs(
    title = "2025 Cuts as % of 2024 Workforce",
    x = "Percentage Cut (%)",
    y = NULL
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, margin = margin(b = 15)),
    axis.text.y = element_blank(), # Hide y labels for the second plot
    axis.title.x = element_text(size = 12)
  ) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.15))) 

# Combine the plots
final_plot <- p1 + p2 + 
  plot_annotation(
    title = 'OPM Data on Federal Workforce Changes by Select Agency, 2024-2025',
    theme = theme(plot.title = element_text(size = 18, face = "bold", hjust = 0.5, margin = margin(b = 20)))
  )

# Save the figure
ggsave("../report/assets/images/workforce.png", plot = final_plot, width = 16, height = 8, dpi = 300, bg = "white")

###
# Analysis of PRA discontinuations
# Last Modified: 2/17/2026
###

prad<-read.csv("../data/pra_discontinuation_aggregated-01282026.csv",stringsAsFactors=FALSE)

#Remove invalid years of request
# prad<-prad[-which(prad$Request.Year<2016),]
prad<-prad[which(prad$Web_Request.Type=="Discontinue"),]

#Barplot of discontinuations by year

png("../report/assets/images/icr-discontinuations.png",width = 2500, height=2500, res=300)
barplot(table(prad$AdminYear),las=2,col=c("#56B4E9",rep("#CC79A7",4),rep("#009E73",4),"#CC79A7"),
        main="\n Number of Discontinued Information Collections \n by 'Administration' Year of Request to OIRA \n 1/21/2016-1/15/2026",ylim=c(0,800),xlab="Administration Year",ylab="Frequency")
legend("topright",legend=c("Obama","Trump","Biden"),fill=c("#56B4E9","#CC79A7","#009E73"),bty="n")
dev.off()

#Line plot that reproduces (approximately) the Data.gov figure

dcc <- read.csv("../data/datagov_collection_count-01262026.csv")
dcc$Date <- as.Date(my(dcc$Date))
dcc$FedMagOfChange <- as.numeric(as.character(dcc$FedMagOfChange))
plot(dcc$Date, dcc$FedMagOfChange, type = "b", col = "#56B4E9", pch = 19,las=1, lwd = 2, main = "Month-to-Month Change in the Number of Federal Data Assets Indexed in Data.gov \n (2023 - 2026) 
", xlab = "", ylab = "")
abline(y=c(3000,-3000))