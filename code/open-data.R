####
# This R script creates a cryptic background image for the cover-art.
####

# 1. Data & Color Setup
open.data <- rbind(
  c(0,1,1,0,1,1,1,1), # o
  c(0,1,1,1,0,0,0,0), # p
  c(0,1,1,0,0,1,0,1), # e
  c(0,1,1,0,1,1,1,0), # n
  c(0,1,1,0,0,1,0,0), # d
  c(0,1,1,0,0,0,0,1), # a
  c(0,1,1,1,0,1,0,0), # t
  c(0,1,1,0,0,0,0,1)  # a
)
# Note: Using your logic where 0=Teal, 1=Orange
teal <- "#00d2ff"
orange <- "#ff9d00"
bg_col <- "#040c18"

png("../report/assets/images/cover.png", width = 2480, height = 3508, res = 300)
par(mar = c(0,0,0,0), bg = bg_col)
plot(NULL, xlim = c(-1, 1), ylim = c(-1.41, 1.41), axes = FALSE, xaxs="i", yaxs="i")

# 2. DRAW FIRST: Deep Radial Gradient
# This creates the background 'glow' that everything else sits on.
for(r in seq(1.5, 0, length.out=150)) {
  col <- rgb(0.01 + 0.05*(1-r/1.5), 0.05 + 0.1*(1-r/1.5), 0.1 + 0.1*(1-r/1.5))
  symbols(0, 0, circles=r, inches=FALSE, add=TRUE, fg=NA, bg=col)
}

# 3. DRAW SECOND: Focal Lines
# Now these are drawn on top of the gradient, but will be 'behind' the orbits.
set.seed(12125)
focal_point <- c(0, 0)
for (i in 1:350) {
  angle <- runif(1, 0, 2 * pi)
  dist <- runif(1, 0.1, 1.4)
  col <- if(runif(1) > 0.7) rgb(1, 0.6, 0.2, 0.24) else rgb(0, 0.7, 0.9, 0.25)
  segments(focal_point[1], focal_point[2], 
           focal_point[1] + cos(angle) * dist, 
           focal_point[2] + sin(angle) * dist, 
           col = col, lwd = runif(1, 0.5, 2.5))
}

# 4. DRAW LAST: Orbit paths and nodes
# This is the topmost layer.
inner_r <- 0.3; step_r <- 0.08
for(i in 1:8) {
  r <- inner_r + (i-1)*step_r
  # Faint orbit circle
  symbols(0, 0, circles=r, inches=FALSE, add=TRUE, fg=rgb(1,1,1,0.05))
  
  for(j in 1:8) {
    angle <- pi/2 - (j-1)*(2*pi/8)
    val <- open.data[i,j] 
    col <- if(val == 1) orange else teal # Correcting mapping to your bit logic
    x <- r * cos(angle)
    y <- r * sin(angle)
    
    # Layered glow for the data nodes
    for(g in 1:6) points(x, y, col=adjustcolor(col, 0.08/g), pch=16, cex=1+g*2)
    # Core point
    points(x, y, col="white", pch=16, cex=0.7)
    
    # Connect bits along the orbit if they are both '1's
    if(val == 1 && open.data[i, (j %% 8) + 1] == 1) {
      angles <- seq(angle, pi/2 - j*(2*pi/8), length.out=10)
      lines(r*cos(angles), r*sin(angles), col=adjustcolor(orange, 0.4), lwd=2)
    }
  }
}

dev.off()
