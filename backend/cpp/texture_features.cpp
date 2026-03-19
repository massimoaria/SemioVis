#include "texture_features.hpp"
#include <opencv2/opencv.hpp>
#include <cmath>
#include <vector>

static cv::Mat to_mat_gray(py::array_t<uint8_t>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_8UC1, buf.ptr);
}

py::dict compute_texture_features(
    py::array_t<uint8_t> img_gray)
{
    cv::Mat gray = to_mat_gray(img_gray);
    int h = gray.rows, w = gray.cols;

    // Downsample for speed
    cv::Mat proc;
    if (std::max(h, w) > 1000) {
        double scale = 1000.0 / std::max(h, w);
        cv::resize(gray, proc, cv::Size(), scale, scale, cv::INTER_AREA);
    } else {
        proc = gray;
    }

    cv::Mat fimg;
    proc.convertTo(fimg, CV_32F, 1.0 / 255.0);

    // --- Gabor filterbank ---
    // 4 orientations x 3 scales
    double orientations[] = {0, M_PI / 4, M_PI / 2, 3 * M_PI / 4};
    double wavelengths[] = {5.0, 10.0, 20.0};

    double total_energy = 0.0;
    std::vector<double> orient_energies(4, 0.0);
    py::list gabor_orient_list;

    for (int oi = 0; oi < 4; ++oi) {
        double orient_energy = 0.0;
        for (double lambda : wavelengths) {
            cv::Mat kernel = cv::getGaborKernel(
                cv::Size(31, 31), 4.0, orientations[oi], lambda, 0.5, 0, CV_32F);
            cv::Mat response;
            cv::filter2D(fimg, response, CV_32F, kernel);

            // Energy = sum of squared responses
            cv::Mat sq;
            cv::multiply(response, response, sq);
            double energy = cv::sum(sq)[0] / (proc.rows * proc.cols);
            orient_energy += energy;
        }
        orient_energies[oi] = orient_energy;
        total_energy += orient_energy;

        py::dict oe;
        oe["orientation_deg"] = orientations[oi] * 180.0 / M_PI;
        oe["energy"] = orient_energy;
        gabor_orient_list.append(oe);
    }

    // Dominant orientation
    int dom_idx = std::distance(orient_energies.begin(),
        std::max_element(orient_energies.begin(), orient_energies.end()));
    double dominant_orientation = orientations[dom_idx] * 180.0 / M_PI;

    // --- Local Binary Patterns (LBP) ---
    int P = 8;   // neighbours
    int R = 1;   // radius
    int lbp_bins = P + 2;  // P+2 for uniform patterns
    std::vector<int> lbp_hist(lbp_bins, 0);
    int total_pixels = 0;

    for (int r = R; r < proc.rows - R; ++r) {
        for (int c = R; c < proc.cols - R; ++c) {
            uint8_t center = proc.at<uint8_t>(r, c);
            uint8_t pattern = 0;

            // 8-connected neighbours clockwise
            int dr[] = {-1, -1, -1, 0, 1, 1, 1, 0};
            int dc[] = {-1, 0, 1, 1, 1, 0, -1, -1};

            for (int p = 0; p < P; ++p) {
                if (proc.at<uint8_t>(r + dr[p], c + dc[p]) >= center)
                    pattern |= (1 << p);
            }

            // Count transitions for uniform LBP
            int transitions = 0;
            for (int p = 0; p < P; ++p) {
                int bit_curr = (pattern >> p) & 1;
                int bit_next = (pattern >> ((p + 1) % P)) & 1;
                if (bit_curr != bit_next) transitions++;
            }

            if (transitions <= 2) {
                // Uniform pattern: count number of 1-bits
                int ones = 0;
                for (int p = 0; p < P; ++p)
                    ones += (pattern >> p) & 1;
                lbp_hist[ones]++;
            } else {
                lbp_hist[P + 1]++;  // non-uniform
            }
            total_pixels++;
        }
    }

    // Normalise LBP histogram
    py::list lbp_hist_list;
    for (int i = 0; i < lbp_bins; ++i)
        lbp_hist_list.append(total_pixels > 0 ?
            static_cast<double>(lbp_hist[i]) / total_pixels : 0.0);

    // Texture homogeneity: how uniform the LBP histogram is
    // High homogeneity = one or few bins dominate
    double max_bin = 0;
    for (int i = 0; i < lbp_bins; ++i) {
        double v = total_pixels > 0 ? static_cast<double>(lbp_hist[i]) / total_pixels : 0.0;
        if (v > max_bin) max_bin = v;
    }
    double texture_homogeneity = max_bin;

    // Texture contrast: variance of LBP values
    double mean_lbp = 0;
    for (int i = 0; i < lbp_bins; ++i)
        mean_lbp += i * (total_pixels > 0 ?
            static_cast<double>(lbp_hist[i]) / total_pixels : 0.0);
    double var_lbp = 0;
    for (int i = 0; i < lbp_bins; ++i) {
        double p = total_pixels > 0 ? static_cast<double>(lbp_hist[i]) / total_pixels : 0.0;
        var_lbp += (i - mean_lbp) * (i - mean_lbp) * p;
    }
    double texture_contrast = std::min(1.0, var_lbp / (P * P / 4.0));

    py::dict features;
    features["gabor_energy"] = total_energy;
    features["gabor_orientations"] = gabor_orient_list;
    features["lbp_histogram"] = lbp_hist_list;
    features["texture_homogeneity"] = texture_homogeneity;
    features["texture_contrast"] = texture_contrast;
    features["dominant_orientation"] = dominant_orientation;
    return features;
}
