# Independent check of make_simulated_data.py using R car::Anova (SPSS-equivalent
# univariate repeated-measures tests). All data are SIMULATED for teaching.
# Run: Rscript verify_with_r.R
invisible(Sys.setlocale("LC_CTYPE", "en_US.UTF-8"))
suppressMessages(suppressWarnings(library(car)))
options(contrasts = c("contr.sum", "contr.poly"))

d <- read.csv("等待期焦虑_模拟数据.csv", fileEncoding = "UTF-8-BOM")
d <- d[complete.cases(d[, c("sas_f_t0", "sas_f_t1", "sas_f_t2")]), ]
d$group <- factor(d$group)
cat("Complete cases by group:\n"); print(table(d$group))

m <- lm(cbind(sas_f_t0, sas_f_t1, sas_f_t2) ~ group, data = d)
idata <- data.frame(time = factor(c("t0", "t1", "t2")))
s <- summary(Anova(m, idata = idata, idesign = ~time, type = "III"), multivariate = FALSE)

cat("\nUnivariate tests (sphericity assumed):\n"); print(s$univariate.tests)
cat("\nMauchly:\n"); print(s$sphericity.tests)
cat("\nGG / HF corrections:\n"); print(s$pval.adjustments)

cat("\nGroup difference at each time (intervention - control), pooled-variance t:\n")
for (v in c("sas_f_t0", "sas_f_t1", "sas_f_t2")) {
  tt <- t.test(d[d$group == "干预组", v], d[d$group == "对照组", v], var.equal = TRUE)
  diff <- unname(tt$estimate[1] - tt$estimate[2])
  cat(sprintf("%s: diff=%.4f  p=%.5f  95%%CI=[%.4f, %.4f]\n", v, diff, tt$p.value, tt$conf.int[1], tt$conf.int[2]))
}
cat("\nNote: car's HF epsilon uses the Lecoutre (1991) correction; SPSS (and make_simulated_data.py) use the\n",
    "original Huynh-Feldt formula, so HF values differ slightly by design. GG, Mauchly and F must match.\n", sep = "")
