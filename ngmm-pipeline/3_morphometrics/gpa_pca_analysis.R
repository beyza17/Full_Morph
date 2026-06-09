# =============================================================
# gpa_pca_analysis.R
# GPA + PCA + Procrustes ANOVA + LDA for mouse brain morphometrics
#
# Usage:
#   Rscript 3_morphometrics/gpa_pca_analysis.R
#   Or open in RStudio and run all (Ctrl+Alt+R)
#
# Input:  Per-region folders of .mrk.json landmark files
#         (output of Stage 2 ALPACA)
# Output: Statistics, PCA scores, and matrix PDFs saved to root_dir
# =============================================================
# root_dir: reads from environment variable set in config/paths.sh
# If running interactively in RStudio, set REPO_ROOT manually below:
# Sys.setenv(REPO_ROOT = "/path/to/ngmm-pipeline")
root_dir <- file.path(Sys.getenv("REPO_ROOT"), "2_landmark_placement/output")
if (root_dir == "/2_landmark_placement/output") {
  stop("REPO_ROOT is not set. See config/paths_template.sh or set it above.")
}
# -------------------------------
# 0. Dependencies
# -------------------------------
packages <- c("devtools", "geomorph", "tidyverse", "jsonlite", 
              "ggforce", "sp", "ggh4x", "ggnewscale", "MASS", "RRPP")

installed_packages <- packages %in% rownames(installed.packages())
if (any(installed_packages == FALSE)) {
  install.packages(packages[!installed_packages])
}

library(MASS)
library(ggh4x)
library(ggnewscale)
library(sp)
library(geomorph)
library(tidyverse)
library(jsonlite)
library(RRPP)

# =============================================================
# CONFIGURATION — edit these two sections before running
# =============================================================

# Path to the folder containing per-region subfolders of .mrk.json files
# (i.e. the output directory from Stage 2 ALPACA, reorganised by region)
#
# Expected structure:
#   root_dir/
#   ├── DG/
#   │   ├── NG4975_RCL5_DG_template.mrk.json
#   │   └── ...
#   ├── HP/
#   └── ...
root_dir   <- file.path(Sys.getenv("REPO_ROOT"), "pipeline_data/alpaca_run/output")
output_dir <- file.path(Sys.getenv("REPO_ROOT"), "3_morphometrics/output")
# Genotype table — add one row per sample ID in your dataset
# Supported genotype labels: "WT", "HOM", "IT"
geno_table <- tribble(
  ~ID,      ~geno,
  "NG2561", "WT",
  "NG2562", "HOM",
  "NG2563", "HOM",
  "NG2564", "WT",
  "NG2565", "WT",
  "NG2566", "HOM",
  "NG2567", "HOM",
  "NG2568", "WT"
)

# =============================================================
# END OF CONFIGURATION — do not edit below this line
# =============================================================

# -------------------------------
# 1. Helper: READ SLICER JSON
# -------------------------------
read_slicer_json <- function(file) {
  json_data <- fromJSON(file)
  if (length(json_data$markups) == 0) stop(paste("No markups found in", file))
  control_points <- json_data$markups$controlPoints[[1]]
  coords_raw <- control_points$position
  if (is.list(coords_raw)) {
    coords <- do.call(rbind, coords_raw)
  } else {
    coords <- as.matrix(coords_raw)
  }
  mode(coords) <- "numeric"
  colnames(coords) <- c("x", "y", "z")
  return(coords)
}

# -------------------------------
# 2. MAIN LOOP: Process subfolders
# -------------------------------
folders <- list.dirs(root_dir, full.names = TRUE, recursive = FALSE)
if (length(folders) == 0) stop("No subfolders found in root_dir.")

all_regions_data <- list()
stats_collector  <- list()

for (folder in folders) {
  folder_name <- basename(folder)
  message("\n--- Processing folder: ", folder_name, " ---")

  json_files <- list.files(folder, pattern = "\\.mrk\\.json$", full.names = TRUE)

  # Keep only specimens whose NG ID is in geno_table
  base_ids <- sub("^(NG[0-9]+).*", "\\1", basename(json_files))
  keep     <- base_ids %in% geno_table$ID

  if (!any(keep)) next

  json_files <- json_files[keep]
  base_ids   <- base_ids[keep]
  message("   -> Using ", length(json_files), " specimens matching geno_table in this region.")

  # Setup output subfolder (timestamped)
  ts     <- format(Sys.time(), "%Y-%m-%d_%H_%M_%S")
  outdir <- file.path(folder, ts)
  dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

  # Read landmark data
  LM_list <- lapply(json_files, read_slicer_json)
  k <- nrow(LM_list[[1]]); p <- 3; n <- length(LM_list)

  LM_array <- array(NA, dim = c(k, p, n))
  for (i in seq_len(n)) LM_array[,,i] <- LM_list[[i]]

  # GPA
  gpa       <- gpagen(LM_array, print.progress = FALSE)
  meanShape <- gpa$consensus
  shape_mat <- two.d.array(gpa$coords)

  write.csv(as.data.frame(meanShape),
            file.path(outdir, paste0(folder_name, "_meanShape.csv")), row.names = FALSE)

  # -----------------------------------------------------------------------
  # A. OUTLIER DETECTION (Mean + 2*SD)
  # -----------------------------------------------------------------------
  proc_dists <- numeric(n)
  for (i in 1:n) proc_dists[i] <- sqrt(sum((gpa$coords[,,i] - meanShape)^2))

  dist_mean   <- mean(proc_dists)
  dist_sd     <- sd(proc_dists)
  upper_fence <- dist_mean + (2 * dist_sd)

  outlier_df <- tibble(
    Specimen   = basename(json_files),
    ProcDist   = proc_dists,
    Is_Outlier = proc_dists > upper_fence
  )

  png(file.path(outdir, paste0(folder_name, "_Outlier_Check.png")), width = 800, height = 600)
  plot(proc_dists, type = "h",
       main = paste("Outlier Check (Mean + 2SD):", folder_name),
       ylab = "Procrustes Dist to Mean", xlab = "Specimen Index", lwd = 2)
  text(1:n, proc_dists,
       labels = ifelse(outlier_df$Is_Outlier, sub("_.*", "", outlier_df$Specimen), ""),
       pos = 3, col = "red", cex = 0.8)
  abline(h = upper_fence, col = "red", lty = 2)
  dev.off()

  write.csv(outlier_df,
            file.path(outdir, paste0(folder_name, "_outliers.csv")), row.names = FALSE)

  # -----------------------------------------------------------------------
  # B. PCA
  # -----------------------------------------------------------------------
  pr          <- prcomp(shape_mat, center = TRUE, scale. = FALSE)
  eig_vals    <- pr$sdev^2
  var_explained <- eig_vals / sum(eig_vals)

  write.csv(tibble(PC = seq_along(eig_vals), Eigenvalue = eig_vals, VarPct = var_explained * 100),
            file.path(outdir, paste0(folder_name, "_eigenvalues.csv")), row.names = FALSE)
  write.csv(as.data.frame(pr$rotation),
            file.path(outdir, paste0(folder_name, "_eigenvectors.csv")), row.names = TRUE)

  pcs_df <- as.data.frame(pr$x) %>%
    mutate(Specimen = basename(json_files)) %>%
    relocate(Specimen)

  pcs_df$Base_ID <- sub("^(NG[0-9]+).*", "\\1", pcs_df$Specimen)
  pcs_df <- pcs_df %>% left_join(geno_table, by = c("Base_ID" = "ID"))

  if (any(is.na(pcs_df$geno))) warning("Missing genotypes in ", folder_name)
  pcs_df$geno <- factor(pcs_df$geno, levels = c("WT", "HOM", "IT"))
  pcs_df <- pcs_df %>%
    left_join(outlier_df %>% dplyr::select(Specimen, Is_Outlier), by = "Specimen")

  # -----------------------------------------------------------------------
  # C. DYNAMIC PC SELECTION (ANOVA + FDR)
  # -----------------------------------------------------------------------
  best_pc_x <- "PC1"; best_pc_y <- "PC2"

  valid_indices <- which(!is.na(pcs_df$geno))
  n_wt  <- sum(pcs_df$geno == "WT",  na.rm = TRUE)
  n_hom <- sum(pcs_df$geno == "HOM", na.rm = TRUE)

  if (length(valid_indices) >= 5) {
    pc_scores_valid <- pr$x[valid_indices, , drop = FALSE]
    geno_valid      <- pcs_df$geno[valid_indices]

    pc_pvals <- sapply(seq_len(ncol(pc_scores_valid)), function(j) {
      if (var(pc_scores_valid[, j]) < 1e-10) return(NA)
      fit <- tryCatch(aov(pc_scores_valid[, j] ~ geno_valid), error = function(e) NULL)
      if (is.null(fit)) return(NA)
      summary(fit)[[1]][["Pr(>F)"]][1]
    })

    pc_stats_df <- tibble(PC = colnames(pc_scores_valid), P_PC_ANOVA = pc_pvals) %>%
      mutate(P_PC_FDR = p.adjust(P_PC_ANOVA, method = "fdr")) %>%
      arrange(P_PC_FDR)

    write.csv(pc_stats_df,
              file.path(outdir, paste0(folder_name, "_pcwise_genotype_effects.csv")), row.names = FALSE)

    sig_pcs <- pc_stats_df %>% filter(!is.na(P_PC_FDR) & P_PC_FDR < 0.05)

    if (nrow(sig_pcs) >= 2) {
      best_pc_x <- sig_pcs$PC[1]; best_pc_y <- sig_pcs$PC[2]
      message("      -> Selected Sig PCs: ", best_pc_x, " & ", best_pc_y)
    } else if (nrow(sig_pcs) == 1) {
      best_pc_x <- sig_pcs$PC[1]
      candidates <- pc_stats_df$PC[pc_stats_df$PC != best_pc_x]
      best_pc_y <- if (length(candidates) > 0) candidates[1] else "PC2"
      message("      -> Selected 1 Sig PC + Next Best: ", best_pc_x, " & ", best_pc_y)
    } else {
      message("      -> No Significant PCs. Defaulting to PC1 & PC2.")
    }
  }

  idx_x <- as.numeric(gsub("PC", "", best_pc_x))
  idx_y <- as.numeric(gsub("PC", "", best_pc_y))

  pcs_df$Driver_X     <- pcs_df[[best_pc_x]]
  pcs_df$Driver_Y     <- pcs_df[[best_pc_y]]
  pcs_df$Driver_Label <- paste0(best_pc_x, " (", round(var_explained[idx_x] * 100, 1), "%) / ",
                                best_pc_y, " (", round(var_explained[idx_y] * 100, 1), "%)")
  pcs_df$Region <- folder_name
  all_regions_data[[folder_name]] <- pcs_df

  write.csv(pcs_df,
            file.path(outdir, paste0(folder_name, "_pcScores.csv")), row.names = FALSE)

  output_data_combined <- pcs_df %>%
    dplyr::select(Specimen, Base_ID, geno, Is_Outlier) %>%
    bind_cols(as.data.frame(shape_mat))
  write.csv(output_data_combined,
            file.path(outdir, paste0(folder_name, "_outputData.csv")), row.names = FALSE)

  # -----------------------------------------------------------------------
  # D. INDIVIDUAL REGION PCA PLOT
  # -----------------------------------------------------------------------
  p_indiv <- ggplot(pcs_df, aes(x = Driver_X, y = Driver_Y, color = geno)) +
    geom_point(size = 3, alpha = 0.8) +
    scale_color_manual(values = c("WT" = "blue", "IT" = "purple", "HOM" = "red")) +
    theme_bw() +
    labs(title    = paste(folder_name, "-", best_pc_x, "vs", best_pc_y),
         subtitle = "Best Separating PCs")

  ggsave(file.path(outdir, paste0(folder_name, "_PCA_Best_Separation.png")),
         plot = p_indiv, width = 6, height = 5)

  # -----------------------------------------------------------------------
  # E. STATISTICS (Procrustes ANOVA + Pairwise + CV-LDA + LDA Permutation)
  # -----------------------------------------------------------------------
  message("   -> Running Statistics...")

  if (length(valid_indices) < 5 || n_wt < 2 || n_hom < 2) {
    stat_entry <- tibble(Region = folder_name, ANOVA_P = NA,
                         LDA_Accuracy_Pct = NA, LDA_Perm_P_Value = NA,
                         Note = "Insufficient Data")
  } else {
    coords_subset <- gpa$coords[,, valid_indices]
    geno_subset   <- pcs_df$geno[valid_indices]

    # Procrustes ANOVA (999 permutations, RRPP)
    gdf       <- geomorph.data.frame(coords = coords_subset, geno = geno_subset)
    fit_anova <- procD.lm(coords ~ geno, data = gdf, iter = 999,
                          RRPP = TRUE, print.progress = FALSE)
    anova_p_val <- fit_anova$aov.table["geno", "Pr(>F)"]

    # Pairwise tests
    tryCatch({
      pw     <- RRPP::pairwise(fit_anova, groups = geno_subset, print.progress = FALSE)
      pw_sum <- summary(pw, stat.table = TRUE)
      pw_tab <- if (!is.null(pw_sum$summary.table)) pw_sum$summary.table else pw_sum
      pair_tab <- as_tibble(pw_tab, rownames = "Comparison") %>%
        mutate(Region = folder_name, .before = 1)
      write.csv(pair_tab,
                file.path(outdir, paste0(folder_name, "_pairwise_tests.csv")), row.names = FALSE)
    }, error = function(e) message("      [!] Pairwise tests skipped (error)."))

    # CV-LDA
    lda_input_raw <- pcs_df[valid_indices, c("PC1", "PC2", "PC3"), drop = FALSE]
    lda_group     <- pcs_df$geno[valid_indices]
    keep_cols     <- sapply(lda_input_raw, function(col) var(col) > 1e-10)
    lda_input     <- lda_input_raw[, keep_cols, drop = FALSE]

    if (ncol(lda_input) == 0) {
      actual_accuracy <- NA; lda_p_val <- NA
    } else {
      lda_model       <- lda(lda_input, grouping = lda_group, CV = TRUE)
      actual_accuracy <- sum(lda_model$class == lda_group) / length(lda_group)

      # LDA permutation test (1000 permutations)
      n_perm          <- 1000
      perm_accuracies <- numeric(n_perm)
      try({
        for (i in 1:n_perm) {
          shuffled_group    <- sample(lda_group)
          lda_perm          <- lda(lda_input, grouping = shuffled_group, CV = TRUE)
          perm_accuracies[i] <- sum(lda_perm$class == shuffled_group) / length(shuffled_group)
        }
      }, silent = TRUE)
      lda_p_val <- (sum(perm_accuracies >= actual_accuracy) + 1) / (n_perm + 1)
    }

    stat_entry <- tibble(
      Region           = folder_name,
      ANOVA_P          = anova_p_val,
      LDA_Accuracy_Pct = round(actual_accuracy * 100, 2),
      LDA_Perm_P_Value = lda_p_val,
      Note             = "Success"
    )
    message("      -> P(Anova)=", round(stat_entry$ANOVA_P, 4),
            " | Acc=", stat_entry$LDA_Accuracy_Pct, "%")
  }

  stats_collector[[folder_name]] <- stat_entry
  write.csv(stat_entry,
            file.path(outdir, paste0(folder_name, "_stats_results.csv")), row.names = FALSE)
  message("   -> Outputs saved.")
}

# -------------------------------------------------------------------------
# 3. FINAL PLOTTING & SUMMARY
# -------------------------------------------------------------------------
message("\n--- Generating Final Matrices and Summary ---")

final_stats_df <- bind_rows(stats_collector)
master_df      <- bind_rows(all_regions_data)
master_df$geno <- factor(master_df$geno, levels = c("WT", "IT", "HOM"))

write.csv(final_stats_df,
          file.path(root_dir, "FULL_STATISTICS_SUMMARY.csv"), row.names = FALSE)
message("   -> Saved FULL_STATISTICS_SUMMARY.csv")

# Anatomical group definitions
fibers       <- c("AC", "cc_", "CC", "F", "Fi", "IC", "St", "OCH")
hippocampus  <- c("DG", "HP", "RHP")
diencephalon <- c("TH", "HY", "Hb")
pons_mb      <- c("MB", "P")
hind_brain   <- c("Cerebellum_ML", "My")
ventricles   <- c("V")
striatum     <- c("CPu")
fore_brain   <- c("CTX_", "A")
controls     <- c("ALL", "deduped", "projected")
target_order <- c(fibers, hippocampus, diencephalon, pons_mb,
                  hind_brain, ventricles, striatum, fore_brain, controls)

group_colors <- c("Fibers"="#ADD8E6", "Hippocampus"="#FFD700", "Diencephalon"="#FFB6C1",
                  "Pons & MB"="#FFA07A", "Hindbrain"="#98FB98", "Ventricles"="#E6E6FA",
                  "Striatum"="#F0E68C", "Forebrain"="#D8BFD8", "Controls"="#D3D3D3", "Other"="#FFFFFF")

group_map <- bind_rows(
  tibble(Region = fibers,       Group = "Fibers"),
  tibble(Region = hippocampus,  Group = "Hippocampus"),
  tibble(Region = diencephalon, Group = "Diencephalon"),
  tibble(Region = pons_mb,      Group = "Pons & MB"),
  tibble(Region = hind_brain,   Group = "Hindbrain"),
  tibble(Region = ventricles,   Group = "Ventricles"),
  tibble(Region = striatum,     Group = "Striatum"),
  tibble(Region = fore_brain,   Group = "Forebrain"),
  tibble(Region = controls,     Group = "Controls")
)

master_df <- master_df %>%
  left_join(group_map, by = "Region") %>%
  mutate(Group = replace_na(Group, "Other"))

actual_regions <- unique(master_df$Region)
final_order    <- c(intersect(target_order, actual_regions),
                    setdiff(actual_regions, target_order))
master_df$Region <- factor(master_df$Region, levels = final_order)

strip_color_list <- master_df %>%
  dplyr::select(Region, Group) %>% distinct() %>% arrange(Region)
strip_fills <- group_colors[strip_color_list$Group]

region_stats <- tibble(Region = final_order) %>%
  left_join(final_stats_df, by = "Region") %>%
  mutate(Sig_Status = case_when(
    !is.na(ANOVA_P) & ANOVA_P < 0.05 ~ "Significant (p < 0.05)",
    TRUE ~ "Not Significant"
  ))
region_stats$Region <- factor(region_stats$Region, levels = final_order)

# Matrix A: PC1 vs PC2
message("1. Generating Matrix A (PC1 vs PC2)...")
p1 <- ggplot() +
  geom_rect(data = region_stats, aes(fill = Sig_Status),
            xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = Inf, alpha = 0.2) +
  scale_fill_manual(values = c("Significant (p < 0.05)" = "red", "Not Significant" = "white"),
                    name = "Global ANOVA (p<0.05)") +
  new_scale_fill() +
  geom_rect(data = master_df, aes(xmin = 0, xmax = 0, ymin = 0, ymax = 0, fill = Group), alpha = 0) +
  scale_fill_manual(values = group_colors, name = "Anatomical Group",
                    guide = guide_legend(override.aes = list(alpha = 1))) +
  geom_point(data = master_df, aes(x = PC1, y = PC2, color = geno, shape = Is_Outlier), size = 2.5) +
  scale_color_manual(values = c("WT" = "blue", "IT" = "purple", "HOM" = "red")) +
  scale_shape_manual(values = c(`FALSE` = 19, `TRUE` = 8), name = "Outlier?") +
  facet_wrap2(~ Region, scales = "free",
              strip = strip_themed(background_x = elem_list_rect(fill = strip_fills))) +
  theme_bw() +
  theme(strip.text = element_text(size = 20, face = "bold", color = "black"),
        legend.position = "bottom", panel.grid.minor = element_blank()) +
  labs(title    = "Matrix A: Standard Shape Variation (PC1 vs PC2)",
       subtitle = "Red Background = Significant Global ANOVA. Stars = Outliers (Mean+2SD).")

ggsave(filename = file.path(root_dir, "MATRIX_1_PC1_PC2.pdf"),
       plot = p1, width = 18, height = 15, dpi = 300)

# Matrix B: Best separation axes
message("2. Generating Matrix B (Best Separators)...")
axis_labels <- master_df %>% dplyr::select(Region, Driver_Label) %>% distinct()

sig_regions <- region_stats %>%
  filter(Sig_Status == "Significant (p < 0.05)") %>% pull(Region)

find_hull <- function(df) df[chull(df$x, df$y), ]

hulls_red <- master_df %>%
  filter(geno == "HOM" & Region %in% sig_regions) %>%
  rename(x = Driver_X, y = Driver_Y) %>%
  group_by(Region) %>%
  filter(n() >= 3) %>%
  drop_na(x, y) %>%
  do(find_hull(.))

p2 <- ggplot() +
  geom_rect(data = region_stats, aes(fill = Sig_Status),
            xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = Inf, alpha = 0.2) +
  scale_fill_manual(values = c("Significant (p < 0.05)" = "red", "Not Significant" = "white"),
                    name = "Global ANOVA (p<0.05)") +
  new_scale_fill() +
  geom_polygon(data = hulls_red, aes(x = x, y = y),
               fill = "red", alpha = 0.3, color = "red", linetype = "solid") +
  geom_rect(data = master_df, aes(xmin = 0, xmax = 0, ymin = 0, ymax = 0, fill = Group), alpha = 0) +
  scale_fill_manual(values = group_colors, name = "Anatomical Group") +
  geom_point(data = master_df, aes(x = Driver_X, y = Driver_Y, color = geno), size = 2.5) +
  scale_color_manual(values = c("WT" = "blue", "IT" = "purple", "HOM" = "red")) +
  geom_text(data = axis_labels, aes(x = -Inf, y = Inf, label = Driver_Label),
            hjust = -0.1, vjust = 1.5, size = 3, fontface = "italic", color = "black") +
  facet_wrap2(~ Region, scales = "free",
              strip = strip_themed(background_x = elem_list_rect(fill = strip_fills))) +
  theme_bw() +
  theme(strip.text = element_text(size = 20, face = "bold", color = "black"),
        legend.position = "bottom", panel.grid.minor = element_blank(),
        axis.title = element_blank()) +
  labs(title    = "Matrix B: Best Phenotype Separation (Smart Axes)",
       subtitle = "Axes chosen by ANOVA+FDR to show strongest Genotype effects.")

ggsave(filename = file.path(root_dir, "MATRIX_2_BEST_SEPARATION.pdf"),
       plot = p2, width = 18, height = 15, dpi = 300)

ggsave(filename = file.path(root_dir, "MATRIX_2_SIGNIFICANT_HULLS.pdf"),
       plot = p2, width = 18, height = 15)

message("DONE. All plots and statistics saved to: ", root_dir)